/* ARM32 ABI subset of Allwinner sunxi_display2.h, legacy layer config.
 * https://github.com/Allwinner-Homlet/H6-BSP4.9-linux/blob/master/include/video/sunxi_display2.h
 * The native camera rotates its GUI into a separate scanout buffer. fb0 alone
 * is not visible. Use an unused overlay layer with the kernel-owned fb0 RAM,
 * never another process's DMA allocation or arbitrary physical memory. */
struct update_rect { int32_t x,y; uint32_t width,height; };
struct update_size { uint32_t width,height; };
struct update_rect64 { int64_t x,y,width,height; };
struct update_fb {
 uint64_t addr[3]; struct update_size size[3]; uint32_t align[3];
 uint32_t format,color_space,trd_right_addr[3]; uint8_t pre_multiply;
 struct update_rect64 crop; uint32_t flags,scan;
};
struct update_layer_info {
 uint32_t mode; uint8_t zorder,alpha_mode,alpha_value;
 struct update_rect screen_win; uint8_t b_trd_out; uint32_t out_trd_mode;
 union { uint32_t color; struct update_fb fb; };
 uint32_t id;
};
struct update_layer {
 struct update_layer_info info; uint8_t enable; uint32_t channel,layer_id;
};
_Static_assert(sizeof(struct update_fb)==128,"display FB ABI");
_Static_assert(sizeof(struct update_layer)==184,"display layer ABI");
static int update_disp=-1,update_layer_active;
static struct update_layer update_saved,update_active;
static void *update_fb_backup;
static void *update_fb_memory;
static size_t update_fb_length;
static int update_layer_config(unsigned request,struct update_layer*config){
 unsigned long args[4]={0,(unsigned long)config,1,0};
 return ioctl(update_disp,request,args);
}
static void update_display_close(void){
 if(update_layer_active){
  /* A pristine disabled slot can have zero dimensions, rejected by this
   * vendor driver even when enable=0. Disable with our last valid geometry. */
  update_active.enable=0;
  if(update_layer_config(0x47,&update_active)<0)fprintf(stderr,"DISPLAY OVERLAY RELEASE FEHLER\n");
  struct timespec delay={0,50000000};nanosleep(&delay,NULL);
  update_layer_active=0;
 }
 /* MiniGUI uses fb0 as the input to its rotation engine. Restore both pages
  * before resuming the paused app, otherwise its next repaint is corrupted. */
 if(update_fb_backup){
  memcpy(update_fb_memory,update_fb_backup,update_fb_length);
  free(update_fb_backup);update_fb_backup=NULL;
 }
 if(update_disp>=0){close(update_disp);update_disp=-1;}
}
static int update_display_open(void *memory,size_t length){
 update_disp=open("/dev/disp",O_RDWR|O_CLOEXEC);
 if(update_disp<0)return -1;
 unsigned long args[4]={0};
 if(ioctl(update_disp,0x07,args)!=240||ioctl(update_disp,0x08,args)!=320)return -1;
 /* Verify the legacy ABI against the known, active GUI layer first. */
 struct update_layer native={.channel=2,.layer_id=0};
 if(update_layer_config(0x48,&native)<0||!native.enable||
    native.info.screen_win.width!=240||native.info.screen_win.height!=320||
    native.info.fb.format!=0||native.channel!=2||native.layer_id!=0)return -1;
 update_saved=(struct update_layer){.channel=2,.layer_id=1};
 if(update_layer_config(0x48,&update_saved)<0||update_saved.enable)return -1;
 update_fb_backup=malloc(length);if(!update_fb_backup)return -1;
 update_fb_memory=memory;update_fb_length=length;
 memcpy(update_fb_backup,memory,length);
 atexit(update_display_close);
 return 0;
}
static int update_display_present(void){
 struct update_layer layer={.enable=1,.channel=2,.layer_id=1};
 layer.info.zorder=17;layer.info.alpha_mode=1;layer.info.alpha_value=255;
 layer.info.screen_win=(struct update_rect){0,0,240,320};
 layer.info.fb.addr[0]=fi.smem_start;
 for(int i=0;i<3;i++)layer.info.fb.size[i]=(struct update_size){240,320};
 layer.info.fb.crop.width=(int64_t)240<<32;
 layer.info.fb.crop.height=(int64_t)320<<32;
 if(update_layer_config(0x47,&layer)<0)return -1;
 update_active=layer;update_layer_active=1;return 0;
}
