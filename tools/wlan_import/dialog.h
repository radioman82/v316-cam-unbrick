/* Reuse the SD updater's measured, reversible display-layer ABI. */
#include <linux/fb.h>
#include <linux/input.h>
#include <poll.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include "update_font.h"
static struct fb_fix_screeninfo fi;
static struct fb_var_screeninfo vi;
static uint32_t *pixels;
static uint32_t logical_pixels[320*240];
static void *fb_memory=MAP_FAILED;
static int fb_fd=-1;
#include "../sd_update/display.h"
struct wlan_event { int32_t sec,usec; uint16_t type,code; int32_t value; };
_Static_assert(sizeof(struct wlan_event)==16,"measured ARM32 evdev layout");
static struct pollfd inputs[3]={{.fd=-1},{.fd=-1},{.fd=-1}};
static double monotonic(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static int show(const char *a,const char *b,const char *c){
    if(!pixels)return -1;
    for(unsigned i=0;i<320*240;i++)logical_pixels[i]=0xff102030;
    const char *lines[]={"WLAN EINRICHTUNG",a,b,c};
    for(int line=0;line<4;line++)for(int i=0;lines[line][i]&&i<33;i++){
        unsigned ch=(unsigned char)lines[line][i];if(ch<32||ch>126)ch='?';
        for(int y=0;y<18;y++)for(int x=0;x<9;x++)if(font[ch-32][y]&(1u<<x))
            logical_pixels[(32+line*42+y)*320+10+i*9+x]=0xffffffff;
    }
    for(unsigned y=0;y<240;y++)for(unsigned x=0;x<320;x++)pixels[x*240+239-y]=logical_pixels[y*320+x];
    return update_display_present();
}
static int dialog_open(void){
    fb_fd=open("/dev/fb0",O_RDWR|O_CLOEXEC);if(fb_fd<0)return -1;
    if(ioctl(fb_fd,FBIOGET_VSCREENINFO,&vi)||ioctl(fb_fd,FBIOGET_FSCREENINFO,&fi)||
       vi.bits_per_pixel!=32||vi.xres!=320||vi.yres!=240||fi.line_length<1280||
       fi.smem_len<fi.line_length*vi.yres_virtual)return -1;
    fb_memory=mmap(NULL,fi.smem_len,PROT_READ|PROT_WRITE,MAP_SHARED,fb_fd,0);
    if(fb_memory==MAP_FAILED||update_display_open(fb_memory,fi.smem_len))return -1;
    pixels=fb_memory;
    const char *names[]={"sunxi-gpadc0","axp22x-powerkey","gpiokey"};
    for(int i=0;i<3;i++){
        char path[64],name[80]={0};snprintf(path,sizeof path,"/dev/input/event%d",i);
        inputs[i]=(struct pollfd){open(path,O_RDONLY|O_NONBLOCK|O_CLOEXEC),POLLIN,0};
        if(inputs[i].fd<0||ioctl(inputs[i].fd,EVIOCGNAME(sizeof name),name)<0||strcmp(name,names[i])||
           ioctl(inputs[i].fd,EVIOCGRAB,1))return -1;
        struct wlan_event ev;while(read(inputs[i].fd,&ev,sizeof ev)==sizeof ev){}
    }
    return 0;
}
static int offer(void){
    unsigned char keys[(KEY_MAX+8)/8]={0};
    if(ioctl(inputs[2].fd,EVIOCGKEY(sizeof keys),keys)<0)return 0;
    int released=!(keys[KEY_MENU/8]&(1<<(KEY_MENU%8)));double start=monotonic(),pressed=0;
    if(show("NEUE WLAN-DATEN AUF SD","OK / AUSLOESER 2 S HALTEN","ANDERE TASTE: ABBRECHEN"))return 0;
    while(monotonic()-start<30){
        poll(inputs,3,100);double now=monotonic();
        for(int i=0;i<3;i++){
            struct wlan_event ev;
            while(read(inputs[i].fd,&ev,sizeof ev)==sizeof ev){
                if(ev.type!=EV_KEY)continue;
                if(i==2&&ev.code==KEY_MENU){if(!ev.value){released=1;pressed=0;}else if(ev.value==1&&released)pressed=now;}
                else if(ev.value==1)return 0;
            }
        }
        if(pressed&&now-pressed>=2)return 1;
    }
    return 0;
}
static int cancel_pressed(void){
    poll(inputs,3,100);
    for(int i=0;i<3;i++){
        struct wlan_event ev;
        while(read(inputs[i].fd,&ev,sizeof ev)==sizeof ev)
            if(ev.type==EV_KEY&&ev.value==1&&!(i==2&&ev.code==KEY_MENU))return 1;
    }
    return 0;
}
