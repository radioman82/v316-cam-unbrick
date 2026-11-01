#define _GNU_SOURCE
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>
#include "config.h"
#include "dialog.h"

static volatile sig_atomic_t interrupted;
static pid_t gui_pid,child_pid;
static int network_lock;
static char work[128];
static void interrupted_signal(int s){(void)s;interrupted=1;}
static int load_file(const char *path,unsigned char *data,size_t *length,struct stat *st){
    int fd=open(path,O_RDONLY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return -1;
    struct stat before,after;
    if(fstat(fd,&before)||!S_ISREG(before.st_mode)||before.st_size<1||before.st_size>WLAN_LIMIT){close(fd);return -1;}
    size_t used=0;
    for(;;){ssize_t n=read(fd,data+used,WLAN_LIMIT+1-used);if(n<0&&errno==EINTR)continue;if(n<0){close(fd);return -1;}if(!n)break;used+=(size_t)n;if(used>WLAN_LIMIT){close(fd);return -1;}}
    int rc=fstat(fd,&after);close(fd);
    if(rc||before.st_size!=(off_t)used||before.st_size!=after.st_size||before.st_mtim.tv_sec!=after.st_mtim.tv_sec||before.st_mtim.tv_nsec!=after.st_mtim.tv_nsec)return -1;
    *length=used;if(st)*st=after;return 0;
}
static int read_config(const char *path,struct wlan_config *c){
    unsigned char data[WLAN_LIMIT+1];size_t n;const char *error;
    if(load_file(path,data,&n,NULL)){fputs("WLAN-DATEI NICHT LESBAR\n",stderr);return -1;}
    int rc=wlan_parse(data,n,c,&error);memset(data,0,sizeof data);
    if(rc)fprintf(stderr,"%s\n",error);return rc;
}
static int atomic_write(const char *path,const void *data,size_t n){
    char temp[512],parent[512];if(strlen(path)>400)return -1;
    struct stat st;if(!lstat(path,&st)&&!S_ISREG(st.st_mode))return -1;
    snprintf(temp,sizeof temp,"%s.tmp-%ld",path,(long)getpid());
    int fd=open(temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);if(fd<0)return -1;
    const unsigned char *p=data;size_t left=n;int rc=0;
    while(left){ssize_t w=write(fd,p,left);if(w<0&&errno==EINTR)continue;if(w<=0){rc=-1;break;}p+=w;left-=(size_t)w;}
    if(!rc&&fsync(fd))rc=-1;if(close(fd))rc=-1;
    if(!rc&&rename(temp,path))rc=-1;
    if(!rc){strcpy(parent,path);char *slash=strrchr(parent,'/');if(slash){if(slash==parent)slash[1]=0;else *slash=0;}else strcpy(parent,".");int dir=open(parent,O_RDONLY|O_DIRECTORY|O_CLOEXEC);if(dir<0)rc=-1;else {if(fsync(dir))rc=-1;close(dir);}}
    if(rc)unlink(temp);return rc;
}
static int save_config(const char *path,const struct wlan_config *c){char data[1024];int n=wlan_serialize(c,data,sizeof data);return n<0?-1:atomic_write(path,data,(size_t)n);}
static pid_t camera_pid(void){
    DIR *d=opendir("/proc");if(!d)return -1;struct dirent *e;pid_t found=0;
    while((e=readdir(d)))if(e->d_name[0]>='0'&&e->d_name[0]<='9'){
        char path[96],name[32]={0};snprintf(path,sizeof path,"/proc/%.16s/comm",e->d_name);FILE *f=fopen(path,"r");if(!f)continue;fgets(name,sizeof name,f);fclose(f);
        if(!strcmp(name,"sdvcam\n")){if(found){found=-1;break;}found=(pid_t)atoi(e->d_name);}
    }closedir(d);return found;
}
static int camera_idle(pid_t pid){
    char path[96],line[512];snprintf(path,sizeof path,"/proc/%ld/stat",(long)pid);FILE*f=fopen(path,"r");if(!f)return 0;
    char *s=fgets(line,sizeof line,f);fclose(f);if(!s)return 0;s=strrchr(line,')');if(!s||s[2]=='T'||s[2]=='t')return 0;
    snprintf(path,sizeof path,"/proc/%ld/fd",(long)pid);DIR*d=opendir(path);if(!d)return 0;struct dirent *e;int idle=1;
    while((e=readdir(d))){char fd[160],target[256];snprintf(fd,sizeof fd,"%s/%.20s",path,e->d_name);ssize_t n=readlink(fd,target,sizeof target-1);if(n<0)continue;target[n]=0;char*ext=strrchr(target,'.');
        if(strstr(target,"/DCIM/")&&ext&&(!strcasecmp(ext,".mp4")||!strcasecmp(ext,".sec"))){idle=0;break;}}
    closedir(d);return idle;
}
static void cleanup(void){
    if(child_pid>0){kill(-child_pid,SIGKILL);waitpid(child_pid,NULL,0);child_pid=0;}
    update_display_close();
    for(int i=0;i<3;i++)if(inputs[i].fd>=0)close(inputs[i].fd);
    if(fb_memory!=MAP_FAILED)munmap(fb_memory,fi.smem_len);
    if(fb_fd>=0)close(fb_fd);
    if(gui_pid>0)kill(gui_pid,SIGCONT);
    if(work[0]){const char*files[]={"candidate.conf","previous.conf","connect.log"};for(int i=0;i<3;i++){char path[256];snprintf(path,sizeof path,"%s/%s",work,files[i]);unlink(path);}rmdir(work);}
    if(network_lock)rmdir("/tmp/v316cm-network-lock");
}
static int run_script(const char *script,const char *arg,int cancellable){
    child_pid=fork();if(child_pid<0)return -1;
    if(!child_pid){
        setpgid(0,0);char log[256];snprintf(log,sizeof log,"%s/connect.log",work);
        int fd=open(log,O_WRONLY|O_CREAT|O_TRUNC,0600);if(fd>=0){dup2(fd,1);dup2(fd,2);close(fd);}
        int null=open("/dev/null",O_RDONLY);if(null>=0){dup2(null,0);close(null);}
        execl("/bin/sh","sh",script,arg,(char*)NULL);_exit(127);
    }
    setpgid(child_pid,child_pid);double start=monotonic();int status;
    for(;;){
        pid_t result=waitpid(child_pid,&status,WNOHANG);
        if(result==child_pid){child_pid=0;return WIFEXITED(status)&&WEXITSTATUS(status)==0?0:-1;}
        if(result<0&&errno!=EINTR){child_pid=0;return -1;}
        int cancelled=cancellable&&(interrupted||cancel_pressed());if(cancelled)interrupted=1;
        if(monotonic()-start>60||cancelled){kill(-child_pid,SIGTERM);usleep(200000);kill(-child_pid,SIGKILL);waitpid(child_pid,NULL,0);child_pid=0;return -1;}
        if(!cancellable)usleep(100000);
    }
}
static int source_unchanged(const char *path,const struct stat *original,const unsigned char *raw,size_t n){
    unsigned char data[WLAN_LIMIT+1];size_t length;struct stat current;
    if(load_file(path,data,&length,&current))return 0;
    return current.st_dev==original->st_dev&&current.st_ino==original->st_ino&&length==n&&!memcmp(raw,data,n);
}
static int import_sd(const char *source,const char *destination){
    unsigned char raw[WLAN_LIMIT+1],old_raw[WLAN_LIMIT+1];size_t n=0,old_n=0;struct stat source_stat;struct wlan_config next,previous;const char *error;
    if(load_file(source,raw,&n,&source_stat))return 2;
    int parsed=wlan_parse(raw,n,&next,&error);
    if(access("/mnt/extsd/firmware-update.bin",F_OK)==0||access("/tmp/v316-sd-update.lock",F_OK)==0)return 3;
    if(mkdir("/tmp/v316cm-network-lock",0700))return 3;network_lock=1;
    atexit(cleanup);signal(SIGTERM,interrupted_signal);signal(SIGINT,interrupted_signal);signal(SIGHUP,interrupted_signal);
    pid_t pid=camera_pid();if(pid<=0||!camera_idle(pid))return 3;
    if(kill(pid,SIGSTOP))return 3;gui_pid=pid;
    if(dialog_open()){fputs("WLAN-DISPLAY NICHT VERFUEGBAR\n",stderr);return 1;}
    if(parsed){show("DATEI NICHT UEBERNOMMEN",error,"SD-DATEI BLEIBT ERHALTEN");sleep(4);return 2;}
    if(!offer()||interrupted){puts("WLAN-IMPORT ABBRUCH: KEINE BESTAETIGUNG");return 0;}
    strcpy(work,"/tmp/v316-wlan-import-XXXXXX");if(!mkdtemp(work)){work[0]=0;return 1;}
    char candidate[256],old[256];snprintf(candidate,sizeof candidate,"%s/candidate.conf",work);snprintf(old,sizeof old,"%s/previous.conf",work);
    int old_exists=load_file(destination,old_raw,&old_n,NULL)==0;
    struct stat destination_stat;
    if(!old_exists&&(!lstat(destination,&destination_stat)||errno!=ENOENT)){
        show("BISHERIGE DATEN NICHT LESBAR","KEINE AENDERUNG VORGENOMMEN","SD-DATEI BLEIBT ERHALTEN");sleep(4);return 1;
    }
    int old_valid=old_exists&&!wlan_parse(old_raw,old_n,&previous,&error);
    if(save_config(candidate,&next)||(old_valid&&save_config(old,&previous)))return 1;
    int stream=access("/tmp/v316cm-stream-mode",F_OK)==0;
    const char *failure="VERBINDUNG FEHLGESCHLAGEN";
    show("VERBINDUNG WIRD GEPRUEFT","BITTE WARTEN","ANDERE TASTE: ABBRECHEN");
    if(run_script("/opt/cam/wlan/connect.sh",candidate,1))goto rollback;
    if(save_config(destination,&next)){
        failure="SPEICHERN FEHLGESCHLAGEN";
        /* rename may have succeeded before a directory fsync failed. */
        if(old_exists)atomic_write(destination,old_raw,old_n);else unlink(destination);
        goto rollback;
    }
    {
        int deleted=source_unchanged(source,&source_stat,raw,n)&&unlink(source)==0;
        if(deleted){int dir=open("/mnt/extsd",O_RDONLY|O_DIRECTORY);if(dir>=0){fsync(dir);close(dir);}}
        char ip[32]="",address[64]="VERBUNDEN";FILE*f=fopen("/run/v316-wlan/ip","r");if(f){fgets(ip,sizeof ip,f);fclose(f);ip[strcspn(ip,"\r\n")]=0;if(wlan_ipv4(ip))snprintf(address,sizeof address,"IP %s:%u",ip,next.port);}
        show("WLAN GESPEICHERT",address,deleted?"SD-DATEI GELOESCHT":"SD-DATEI BITTE SELBST LOESCHEN");
        puts(deleted?"WLAN-IMPORT ERFOLGREICH; SD-DATEI GELOESCHT":"WLAN-IMPORT ERFOLGREICH; SD-DATEI ERHALTEN");
        if(stream)run_script("/opt/cam/start_streaming.sh","",0);else run_script("/opt/cam/wlan/connect.sh","--stop",0);
        sleep(12);return 0;
    }
rollback:
    if(interrupted)failure="EINRICHTUNG ABGEBROCHEN";
    else if(!strcmp(failure,"VERBINDUNG FEHLGESCHLAGEN")){
        char reason[32]={0};FILE*f=fopen("/run/v316-wlan/error","r");if(f){fgets(reason,sizeof reason,f);fclose(f);}
        if(!strcmp(reason,"AUTH\n"))failure="WLAN-NAME / PASSWORT PRUEFEN";
        else if(!strcmp(reason,"DHCP\n"))failure="KEINE IP VOM ROUTER ERHALTEN";
        else if(!strcmp(reason,"DRIVER\n"))failure="WLAN-TREIBER NICHT BEREIT";
        else if(!strcmp(reason,"ADDRESS\n"))failure="IP-EINSTELLUNGEN PRUEFEN";
    }
    show("NEUE VERBINDUNG FEHLGESCHLAGEN","ALTE DATEN WIEDERHERSTELLEN","SD-DATEI BLEIBT ERHALTEN");
    int restored=old_valid?run_script("/opt/cam/wlan/connect.sh",old,0):run_script("/opt/cam/wlan/connect.sh","--stop",0);
    if(stream&&old_valid&&!restored)run_script("/opt/cam/start_streaming.sh","",0);
    if(!stream)run_script("/opt/cam/wlan/connect.sh","--stop",0);
    show(failure,old_valid&&!restored?"ALTE VERBINDUNG WIEDER AKTIV":"BISHERIGE DATEN BLEIBEN ERHALTEN","SD-DATEI BLEIBT ERHALTEN");
    puts("WLAN-IMPORT FEHLER; BISHERIGE DATEN UND SD-DATEI ERHALTEN");sleep(4);return 1;
}
int main(int argc,char **argv){
    umask(0077);setvbuf(stdout,NULL,_IONBF,0);
    if(argc==4&&!strcmp(argv[1],"--import"))return import_sd(argv[2],argv[3]);
    if(argc==3&&!strcmp(argv[1],"--valid-ip"))return !wlan_ipv4(argv[2]);
    if(argc<3)return 2;
    struct wlan_config c;if(read_config(argv[2],&c))return 1;
    if(argc==3&&!strcmp(argv[1],"--check")){puts("WLAN-KONFIGURATION GUELTIG");return 0;}
    if(argc==4&&!strcmp(argv[1],"--same")){struct wlan_config other;char a[1024],b[1024];if(read_config(argv[3],&other))return 1;wlan_serialize(&c,a,sizeof a);wlan_serialize(&other,b,sizeof b);return strcmp(a,b)!=0;}
    if(argc==4&&!strcmp(argv[1],"--get")){
        const char*key=argv[3];if(!strcmp(key,"ip_mode"))puts(c.mode);else if(!strcmp(key,"address"))puts(c.address);else if(!strcmp(key,"netmask"))puts(c.netmask);else if(!strcmp(key,"gateway"))puts(c.gateway);else if(!strcmp(key,"http_port"))printf("%u\n",c.port);else return 2;return 0;
    }
    if(argc==4&&(!strcmp(argv[1],"--normalize")||!strcmp(argv[1],"--dhcp")||!strcmp(argv[1],"--wpa"))){
        if(!strcmp(argv[1],"--dhcp")){strcpy(c.mode,"dhcp");c.address[0]=c.netmask[0]=c.gateway[0]=0;}
        if(strcmp(argv[1],"--wpa"))return save_config(argv[3],&c)!=0;
        char data[1024];int n=wlan_wpa(&c,data,sizeof data);return n<0||atomic_write(argv[3],data,(size_t)n);
    }
    return 2;
}
