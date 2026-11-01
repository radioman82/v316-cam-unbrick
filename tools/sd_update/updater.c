/* Fixed-board SD updater. Static binary; the writer must be PID 1 in tmpfs.
 * No shell, shared libraries or reads from the old root after pivot_root.
 * SHA-256 is an integrity check, not a firmware signature/authentication. */
#define _GNU_SOURCE
#include <errno.h>
#include <dirent.h>
#include <fcntl.h>
#include <linux/fb.h>
#include <linux/input.h>
#include <linux/fs.h>
#include <poll.h>
#include <sched.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <sys/statfs.h>
#include <sys/sysmacros.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "update_font.h"

#define IMAGE_SIZE 16777216u
static const unsigned offsets[7]={0,0x100000,0x400000,0xe80000,0xf00000,0xf20000,0xf80000};
static const unsigned sizes[7]={0x100000,0x300000,0xa80000,0x80000,0x20000,0x60000,0x80000};
static const char *names[7]={"uboot","boot","rootfs","overlay","env","bootlogo","UDISK"};
static unsigned char *image;
static int committed;
static FILE *journal;
static uint32_t *pixels;
static struct fb_var_screeninfo vi;
static struct fb_fix_screeninfo fi;
static int fb=-1;
static uint32_t logical_pixels[320*240];
#include "display.h"
/* Explicit wire layout for this kernel's measured 16-byte ARM32 evdev ABI. */
struct update_input_event {int32_t sec,usec;uint16_t type,code;int32_t value;};
_Static_assert(sizeof(struct update_input_event)==16,"ARM32 evdev ABI");

/* SHA-256, FIPS 180-4, streaming implementation. */
typedef struct {uint32_t h[8];uint64_t n;unsigned char b[64];unsigned used;} SHA;
static uint32_t rr(uint32_t x,unsigned n){return (x>>n)|(x<<(32-n));}
static const uint32_t k[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static void block(SHA *s){
 uint32_t w[64];for(int i=0;i<16;i++)w[i]=(uint32_t)s->b[i*4]<<24|(uint32_t)s->b[i*4+1]<<16|(uint32_t)s->b[i*4+2]<<8|s->b[i*4+3];
 for(int i=16;i<64;i++){uint32_t a=w[i-15],b=w[i-2];w[i]=w[i-16]+(rr(a,7)^rr(a,18)^(a>>3))+w[i-7]+(rr(b,17)^rr(b,19)^(b>>10));}
 uint32_t a=s->h[0],b=s->h[1],c=s->h[2],d=s->h[3],e=s->h[4],f=s->h[5],g=s->h[6],h=s->h[7];
 for(int i=0;i<64;i++){uint32_t t=h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^(~e&g))+k[i]+w[i];uint32_t u=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void sha_init(SHA*s){*s=(SHA){.h={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}};}
static void sha_add(SHA*s,const void*data,size_t n){const unsigned char*p=data;s->n+=n;while(n--){s->b[s->used++]=*p++;if(s->used==64){block(s);s->used=0;}}}
static void sha_end(SHA*s,unsigned char*out){uint64_t bits=s->n*8;unsigned char pad=128;sha_add(s,&pad,1);pad=0;while(s->used!=56)sha_add(s,&pad,1);unsigned char tail[8];for(int i=0;i<8;i++)tail[i]=bits>>(56-8*i);sha_add(s,tail,8);for(int i=0;i<32;i++)out[i]=s->h[i/4]>>(24-8*(i%4));}
static void hash(const void*p,size_t n,unsigned char*out){SHA s;sha_init(&s);sha_add(&s,p,n);sha_end(&s,out);}

static void screen(const char *a,const char *b,const char *c){
 printf("%s | %s | %s\n",a,b,c);fflush(stdout);
 if(journal){fprintf(journal,"%s | %s | %s\n",a,b,c);fflush(journal);fsync(fileno(journal));}
 if(!pixels)return;
 for(unsigned i=0;i<320*240;i++)logical_pixels[i]=0xff102030;
 const char *lines[]={"V316 FIRMWARE UPDATE",a,b,c};
 {
  for(int l=0;l<4;l++)for(int i=0;lines[l][i]&&i<33;i++){
   unsigned ch=(unsigned char)lines[l][i];if(ch<32||ch>126)ch='?';
   for(int y=0;y<18;y++)for(int x=0;x<9;x++)if(font[ch-32][y]&(1u<<x)){
    unsigned py=32+l*42+y,px=10+i*9+x;
    if(py<240&&px<320)logical_pixels[py*320+px]=0xffffffff;
   }
  }
 }
 /* Landscape UI -> portrait LCD, matching the camera's native rotation. */
 for(unsigned y=0;y<240;y++)for(unsigned x=0;x<320;x++)pixels[x*240+239-y]=logical_pixels[y*320+x];
 if(update_display_present()<0){pixels=NULL;fprintf(stderr,"DISPLAY OVERLAY COMMIT FEHLER\n");}
}
static void fb_open(void){
 fb=open("/dev/fb0",O_RDWR|O_CLOEXEC);if(fb<0)return;
 if(ioctl(fb,FBIOGET_VSCREENINFO,&vi)||ioctl(fb,FBIOGET_FSCREENINFO,&fi)||vi.bits_per_pixel!=32||vi.xres!=320||vi.yres!=240||fi.line_length<1280||fi.smem_len<fi.line_length*vi.yres_virtual)return;
 void*p=mmap(NULL,fi.smem_len,PROT_READ|PROT_WRITE,MAP_SHARED,fb,0);
 if(p!=MAP_FAILED&&update_display_open(p,fi.smem_len)==0)pixels=p;
}
static void fail(const char *s){
 screen(committed?"UPDATE FEHLGESCHLAGEN":"UPDATE ABGEBROCHEN",s,committed?"FEL-RETTUNG ERFORDERLICH":"FLASH UNVERAENDERT");
 if(getpid()==1){sync();if(!committed){sleep(8);reboot(RB_AUTOBOOT);}for(;;)pause();}exit(1);
}
static void exact(int fd,void*p,size_t n,off_t at){
 while(n){ssize_t r=pread(fd,p,n,at);if(r<0&&errno==EINTR)continue;if(r<=0)fail("LESEFEHLER");p=(char*)p+r;at+=r;n-=r;}
}
static void write_exact(int fd,const void*p,size_t n,off_t at){
 while(n){ssize_t r=pwrite(fd,p,n,at);if(r<0&&errno==EINTR)continue;if(r<=0)fail("SCHREIBFEHLER");p=(const char*)p+r;at+=r;n-=r;}
}
static void package(const char*path){
 int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);struct stat st;unsigned char h[512],digest[32];
 if(fd<0||fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size!=IMAGE_SIZE+512)fail("PAKETGROESSE UNGUELTIG");
 exact(fd,h,sizeof h,0);
 static const char magic[16]="V316-SDUPDATE1\n",board[32]="V316-A14018-16M";
 if(memcmp(h,magic,16)||memcmp(h+20,board,32)||memcmp(h+16,"\0\0\0\1",4))fail("FALSCHES PAKETMODELL");
 for(int i=52;i<512;i++)if((i<64||i>=96)&&h[i])fail("PAKETVERSION UNBEKANNT");
 image=malloc(IMAGE_SIZE);if(!image)fail("ZU WENIG RAM");
 exact(fd,image,IMAGE_SIZE,512);close(fd);hash(image,IMAGE_SIZE,digest);
 if(memcmp(digest,h+64,32))fail("SHA256 PRUEFSUMME FALSCH");
 if(memcmp(image+0x400000,"hsqs",4)||memcmp(image+0x100000,"\x27\x05\x19\x56",4))fail("IMAGEFORMAT UNGUELTIG");
 screen("PAKET GEPRUEFT","SHA256 OK","16 MIB / V316-A14018");
}
static int powered(void){
 const char*paths[]={"/sys/class/power_supply/usb/online","/sys/class/power_supply/ac/online"};
 for(int i=0;i<2;i++){int fd=open(paths[i],O_RDONLY);char c=0;if(fd>=0){ssize_t n=read(fd,&c,1);close(fd);if(n==1&&c=='1')return 1;}}return 0;
}
static int device(int i,int writable){
 /* This vendor kernel has mtdblock but no registered MTD character driver.
  * mtdblock performs NOR erase/write; fsync + BLKFLSBUF precedes readback. */
 char path[96],type[16]={0};unsigned size=0,erase=0,flags=0;
 snprintf(path,sizeof path,"/sys/class/mtd/mtd%d/type",i);FILE*f=fopen(path,"r");if(!f)fail("FLASH-TYP FEHLT");int rc=fscanf(f,"%15s",type);fclose(f);if(rc!=1||strcmp(type,"nor"))fail("KEIN NOR-FLASH");
 snprintf(path,sizeof path,"/sys/class/mtd/mtd%d/size",i);f=fopen(path,"r");if(!f)fail("FLASH-GROESSE FEHLT");rc=fscanf(f,"%u",&size);fclose(f);if(rc!=1||size!=sizes[i])fail("FLASH-GROESSE FALSCH");
 snprintf(path,sizeof path,"/sys/class/mtd/mtd%d/erasesize",i);f=fopen(path,"r");if(!f)fail("ERASESIZE FEHLT");rc=fscanf(f,"%u",&erase);fclose(f);if(rc!=1||erase!=4096)fail("ERASESIZE FALSCH");
 snprintf(path,sizeof path,"/sys/class/mtd/mtd%d/flags",i);f=fopen(path,"r");if(!f)fail("FLASH-FLAGS FEHLEN");rc=fscanf(f,"%x",&flags);fclose(f);if(rc!=1||!(flags&0x400))fail("FLASH SCHREIBGESCHUETZT");
 snprintf(path,sizeof path,"/dev/mtdblock%d",i);int fd=open(path,(writable?O_RDWR:O_RDONLY)|O_SYNC|O_CLOEXEC);struct stat st;uint64_t bytes=0;
 if(fd<0||fstat(fd,&st)||!S_ISBLK(st.st_mode)||major(st.st_rdev)!=31||minor(st.st_rdev)!=(unsigned)i||ioctl(fd,BLKGETSIZE64,&bytes)||bytes!=sizes[i])fail("FLASHGEOMETRIE UNBEKANNT");return fd;
}
static void preflight(void){
 FILE*f=fopen("/proc/mtd","r");if(!f)fail("MTD FEHLT");char line[160];int count=0;
 while(fgets(line,sizeof line,f)){unsigned i,size,erase;char name[64];if(sscanf(line,"mtd%u: %x %x \"%63[^\"]\"",&i,&size,&erase,name)==4){if(i>=7||i!=(unsigned)count||size!=sizes[i]||erase!=4096||strcmp(name,names[i]))fail("PARTITIONEN UNBEKANNT");count++;}}fclose(f);if(count!=7)fail("PARTITIONEN FEHLEN");
 unsigned char b[4096];int fd=device(0,0);
 for(unsigned at=0;at<sizes[0];at+=sizeof b){exact(fd,b,sizeof b,at);if(memcmp(b,image+at,sizeof b))fail("BOOTLOADER PASST NICHT");}close(fd);
 for(int i=1;i<7;i++){fd=device(i,0);close(fd);}
 if(!powered())fail("USB-STROM ERFORDERLICH");
 screen("HARDWARE GEPRUEFT","BOOTLOADER PASST","USB-STROM VORHANDEN");
}
static int offer(void){
 fb_open();if(!pixels)fail("DISPLAY NICHT VERFUEGBAR");
 struct pollfd inputs[3];
 const char*names[]={"sunxi-gpadc0","axp22x-powerkey","gpiokey"};
 for(int i=0;i<3;i++){
  char path[48],name[80]={0};snprintf(path,sizeof path,"/dev/input/event%d",i);
  inputs[i]=(struct pollfd){open(path,O_RDONLY|O_NONBLOCK|O_CLOEXEC),POLLIN,0};
  if(inputs[i].fd<0||ioctl(inputs[i].fd,EVIOCGNAME(sizeof name),name)<0||strcmp(name,names[i]))fail("TASTATUR UNBEKANNT");
  if(ioctl(inputs[i].fd,EVIOCGRAB,1))fail("TASTATUR BELEGT");
  struct update_input_event ev;while(read(inputs[i].fd,&ev,sizeof ev)==sizeof ev){}
 }
 unsigned char keys[(KEY_MAX+8)/8]={0};if(ioctl(inputs[2].fd,EVIOCGKEY(sizeof keys),keys)<0)fail("TASTENSTATUS FEHLT");
 /* Measured on this board: physical OK/shutter = gpiokey KEY_MENU (139). */
 int released=!(keys[KEY_MENU/8]&(1<<(KEY_MENU%8)));struct timespec clock;clock_gettime(CLOCK_MONOTONIC,&clock);double start=clock.tv_sec+clock.tv_nsec/1e9,pressed=0;
 screen("NEUE FIRMWARE AUF SD","OK / AUSLOESER 2 S HALTEN","ANDERE TASTE: ABBRUCH");
 if(!pixels)fail("DISPLAYAUSGABE FEHLGESCHLAGEN");
 for(;;){
  clock_gettime(CLOCK_MONOTONIC,&clock);double now=clock.tv_sec+clock.tv_nsec/1e9;if(now-start>=30)break;
  poll(inputs,3,100);
  for(int i=0;i<3;i++){
   struct update_input_event ev;
   while(read(inputs[i].fd,&ev,sizeof ev)==sizeof ev){if(ev.type!=EV_KEY)continue;
    if(i==2&&ev.code==KEY_MENU){if(!ev.value){released=1;pressed=0;}else if(ev.value==1&&released)pressed=now;}
    else if(ev.value==1){for(int j=0;j<3;j++)close(inputs[j].fd);return 0;}
   }
  }
  if(pressed&&now-pressed>=2){if(!powered())fail("USB-STROM ERFORDERLICH");for(int i=0;i<3;i++)close(inputs[i].fd);return 10;}
 }
 for(int i=0;i<3;i++)close(inputs[i].fd);screen("UPDATE UEBERSPRUNGEN","KEINE BESTAETIGUNG","NORMALER START");return 0;
}
static void move_mount(const char*from,const char*to){mkdir(to,0755);if(mount(from,to,NULL,MS_MOVE,NULL))fail("MOUNT-VERSCHIEBUNG FEHLER");}
static void busy_report(void){
 DIR*d=opendir("/proc");struct dirent*e;if(!d)return;
 while((e=readdir(d)))if(e->d_name[0]>='0'&&e->d_name[0]<='9'){
  char path[128],out[256];snprintf(path,sizeof path,"/proc/%.16s/exe",e->d_name);ssize_t n=readlink(path,out,sizeof out-1);
  if(n>0){out[n]=0;fprintf(stderr,"live PID %s exe %s\n",e->d_name,out);}
  snprintf(path,sizeof path,"/proc/%.16s/root",e->d_name);n=readlink(path,out,sizeof out-1);if(n>0){out[n]=0;if(strcmp(out,"/"))fprintf(stderr,"PID %s root %s\n",e->d_name,out);}
  snprintf(path,sizeof path,"/proc/%.16s/cwd",e->d_name);n=readlink(path,out,sizeof out-1);if(n>0){out[n]=0;if(strcmp(out,"/"))fprintf(stderr,"PID %s cwd %s\n",e->d_name,out);}
 }
 closedir(d);FILE*f=fopen("/proc/mounts","r");if(f){char line[1024];while(fgets(line,sizeof line,f))fprintf(stderr,"mount %s",line);fclose(f);}d=opendir("/proc/self/fd");if(!d)return;
 while((e=readdir(d))){char path[128],out[256];snprintf(path,sizeof path,"/proc/self/fd/%.16s",e->d_name);ssize_t n=readlink(path,out,sizeof out-1);if(n>0){out[n]=0;fprintf(stderr,"fd %s -> %s\n",e->d_name,out);}}closedir(d);
}
static void ram_root(int namespace_test){
 if(!namespace_test&&getpid()!=1)fail("WRITER MUSS PID 1 SEIN");
 struct statfs fs;struct stat parent,root;
 if(statfs("/tmp/v316-update",&fs)||fs.f_type!=0x01021994||stat("/tmp",&parent)||stat("/tmp/v316-update",&root)||parent.st_dev==root.st_dev)fail("EIGENES RAM-TMPFS FEHLT");
 /* All other userspace processes have been killed by BusyBox init RESTART. */
 mkdir("/tmp/v316-update/oldroot",0755);
 if(chdir("/tmp/v316-update")||syscall(SYS_pivot_root,".","oldroot")||chdir("/"))fail("RAM-PIVOT FEHLER");
 move_mount("/oldroot/proc","/proc");move_mount("/oldroot/sys","/sys");move_mount("/oldroot/dev","/dev");
 move_mount("/oldroot/mnt/extsd","/sd");
 /* Move children out first: overlayfs holds its lower/upper mounts busy until
  * the overlay root itself is unmounted. No lazy detaches are used. */
 int saved=0;char saved_paths[32][64];
 for(int pass=0;pass<32;pass++){
  FILE*f=fopen("/proc/mounts","r");if(!f)fail("MOUNTS NICHT LESBAR");char dev[256],at[256],type[64],rest[512],last[256]="";
  /* /proc/mounts is not topologically sorted: overlay can follow its children. */
  while(fscanf(f,"%255s %255s %63s %511[^\n]\n",dev,at,type,rest)==4)if((!strcmp(at,"/oldroot")||!strncmp(at,"/oldroot/",9))&&strlen(at)>strlen(last))strcpy(last,at);
  fclose(f);if(!last[0])break;
  if(strcmp(last,"/oldroot")){
   char *to=saved_paths[saved++];strcpy(to,"/saved-mount-XXXXXX");struct stat st;
   if(stat(last,&st))fail("MOUNT-STATUS FEHLER");
   if(S_ISDIR(st.st_mode)){if(!mkdtemp(to))fail("MOUNT-ZIEL FEHLER");}else{int fd=mkstemp(to);if(fd<0)fail("MOUNT-ZIEL FEHLER");close(fd);}
   if(mount(last,to,NULL,MS_MOVE,NULL)){fprintf(stderr,"move %s: %s\n",last,strerror(errno));fail("MOUNT-VERSCHIEBUNG FEHLER");}
  }else{
   int rc=-1;for(int retry=0;retry<10;retry++){while(waitpid(-1,NULL,WNOHANG)>0){}rc=umount(last);if(!rc)break;sleep(1);}
   if(rc){fprintf(stderr,"umount %s: %s\n",last,strerror(errno));busy_report();fail("ALTES SYSTEM NOCH BELEGT");}
  }
 }
 for(int i=saved-1;i>=0;i--){const char*to=saved_paths[i];if(umount(to)){fprintf(stderr,"umount %s: %s\n",to,strerror(errno));fail("ALTER MOUNT NOCH BELEGT");}unlink(to);rmdir(to);}
 FILE*f=fopen("/proc/mounts","r");if(!f)fail("MOUNTS NICHT LESBAR");char line[1024];
 while(fgets(line,sizeof line,f))if(strstr(line,"mtd")||strstr(line,"squashfs")||strstr(line," overlay ")||strstr(line,"/oldroot"))fail("FLASH NOCH EINGEHAENGT");fclose(f);
 screen("RAM-UPDATEUMGEBUNG AKTIV","ALLE FLASH-MOUNTS FREI","VERSORGUNG NICHT TRENNEN");
}
static void partition(int i,int test){
 int fd=device(i,0);unsigned char b[4096];int same=1;
 for(unsigned at=0;at<sizes[i];at+=sizeof b){exact(fd,b,sizeof b,at);if(memcmp(b,image+offsets[i]+at,sizeof b))same=0;}close(fd);
 char label[80];snprintf(label,sizeof label,"%s: %s",names[i],same?"BEREITS IDENTISCH":test?"TEST / WUERDE SCHREIBEN":"SCHREIBEN");screen(label,"BOOTLOADER BLEIBT ERHALTEN","EINSTELLUNGEN BLEIBEN ERHALTEN");
 if(test||same)return;
 if(!powered())fail("USB-STROM VERLOREN");
 fd=device(i,1);committed=1;
 for(unsigned at=0;at<sizes[i];at+=4096){
  write_exact(fd,image+offsets[i]+at,4096,at);
  if(!(at%0x40000)){char progress[80];snprintf(progress,sizeof progress,"%s: %u PROZENT",names[i],(at+4096)*100/sizes[i]);screen(progress,"SCHREIBEN LAEUFT","VERSORGUNG NICHT TRENNEN");}
 }
 if(fsync(fd)||ioctl(fd,BLKFLSBUF,0))fail("FLASH SYNC-FEHLER");close(fd);fd=device(i,0);
 for(unsigned at=0;at<sizes[i];at+=sizeof b){exact(fd,b,sizeof b,at);if(memcmp(b,image+offsets[i]+at,sizeof b))fail("RUECKLESEPRUEFUNG FEHLER");}close(fd);
 screen(names[i],"GESCHRIEBEN UND VERIFIZIERT","VERSORGUNG NICHT TRENNEN");
}
int main(int argc,char**argv){
 setvbuf(stdout,NULL,_IONBF,0);
 if(argc!=3){fprintf(stderr,"Usage: updater --check|--preflight|--offer|--namespace-test|--pid1-test|--pid1 PACKAGE\n");return 2;}
 int pid1=!strcmp(argv[1],"--pid1"),test=!strcmp(argv[1],"--pid1-test");
 int ns=!strcmp(argv[1],"--namespace-test");
 if(strcmp(argv[1],"--check")&&strcmp(argv[1],"--preflight")&&strcmp(argv[1],"--offer")&&!pid1&&!test&&!ns)return 2;
 if((pid1||test)&&getpid()!=1)fail("PID 1 ERFORDERLICH");
 if(pid1||test){
  /* Init's inherited console can refer to a static node on the old root. */
  int console=open("/dev/console",O_RDWR|O_NOCTTY);if(console<0)fail("KONSOLE FEHLT");
  for(int fd=0;fd<3;fd++)if(dup2(console,fd)<0)fail("KONSOLE DUP FEHLER");
  long limit=sysconf(_SC_OPEN_MAX);if(limit>65536||limit<0)limit=65536;for(int fd=3;fd<limit;fd++)close(fd);
 }
 package(argv[2]);if(!strcmp(argv[1],"--check"))return 0;
 preflight();if(!strcmp(argv[1],"--preflight"))return 0;
 if(!strcmp(argv[1],"--offer")){free(image);return offer();}
 if(ns){if(unshare(CLONE_NEWNS)||mount(NULL,"/",NULL,MS_REC|MS_PRIVATE,NULL))fail("MOUNT-NAMESPACE FEHLER");test=1;}
 else fb_open();sync();ram_root(ns);
 journal=fopen(test?"/sd/firmware-update-test.log":"/sd/firmware-update.log","a");if(!journal)fail("SD-LOG NICHT SCHREIBBAR");
 screen(test?"TEST OHNE FLASH-SCHREIBEN":"FLASH-UPDATE STARTET",ns?"ISOLIERTER MOUNT-NAMESPACE":"PID 1 / STATISCH / RAM","SYSTEMDATEISYSTEM AUSGEHAENGT");
 preflight();partition(2,test);partition(1,test);partition(5,test);
 if(ns){screen("NAMESPACE-TEST ERFOLGREICH","FLASH NICHT BESCHRIEBEN","KEIN NEUSTART");return 0;}
 if(!test&&rename("/sd/firmware-update.installing","/sd/firmware-update.done"))fail("PAKET UMBENENNEN FEHLER");
 screen(test?"RAM-TEST ERFOLGREICH":"UPDATE ERFOLGREICH","NEUSTART IN 3 SEKUNDEN",test?"FLASH NICHT BESCHRIEBEN":"RUECKLESEPRUEFUNG OK");
 sync();sleep(3);reboot(RB_AUTOBOOT);fail("NEUSTART FEHLGESCHLAGEN");
}
