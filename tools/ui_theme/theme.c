/* Allwinner V316 Cam v22 UI renderer and explicit streaming-mode guard.
 * Runs in the existing GUI thread; no input-event injection.
 * Native menu controls retain selection and callbacks.
 * ABI: ARM32 soft-float, MiniGUI 3.0, byte-verified v22 executable.
 */
#include <stdint.h>
#include <stddef.h>
#include "font.h"
typedef uint32_t O;
typedef struct { int l,t,r,b; } Rect;
#define FN(a,t) ((t)(uintptr_t)(a))
#define GET(p,n) (*(uint32_t *)(uintptr_t)((p)+(n)))
#define BYTE(p,n) (*(unsigned char *)(uintptr_t)((p)+(n)))
#define SEND FN(0x1bf2c,int(*)(O,int,O,O))
#define BEGIN FN(0x1bfb4,O(*)(O))
#define END FN(0x1c6cc,void(*)(O,O))
#define RECT FN(0x1c270,int(*)(O,Rect*))
#define ATTR FN(0x1d50c,O(*)(O,int,O))
#define FILL FN(0x1d420,int(*)(O,int,int,int,int))
#define RGBS FN(0x1c050,void(*)(O,const void*,O*,int))
#define INV FN(0x1be5c,int(*)(O,const Rect*,int))
#define BG 0x10151c
#define CARD 0x1b2430
#define EDGE 0x344151
#define GOLD 0xffb300
#define TEXT 0xeef3fa
#define MUTED 0xabb9ca
#define ACTIVE 0x3c321c
static O window(int id);
static int streaming(void) { return !FN(0x1cc3c,int(*)(const char*,int))("/tmp/v316cm-stream-mode",0); }

/* Mode artwork already contains its caption. Hide only the additional native
 * IconView caption, keeping the translated names used by preview and setup.
 * ModelSelectWindow builds eight 20-byte items: id, bitmap, caption, two flags.
 * Its existing filter still owns the photo/video split and selection indices. */
void theme_mode_captions(O unused,O items) {
    (void)unused;
    O first=GET(items,0),end=GET(items,4);
    if(!first||end-first!=8*20)return;
    for(O item=first;item<end;item+=20)GET(item,8)=(O)"";
}

static int len(const char*s) { int n=0; if(s)while(s[n])++n;return n; }
static int eq(const char*a,const char*b) { if(!a||!b)return 0;while(*a&&*a==*b){a++;b++;}return *a==*b; }
static int min(int a,int b){return a<b?a:b;}
static O pixel(O dc,O color) {
    unsigned char rgba[4]={color>>16,color>>8,color,255}; O p;
    RGBS(dc,rgba,&p,1);return p;
}
static void box(O dc,int x,int y,int w,int h,O color) {
    if(w<=0||h<=0)return;
    ATTR(dc,2,pixel(dc,color));FILL(dc,x,y,w,h);
}
static void roundbox(O dc,int x,int y,int w,int h,O color) {
    if(w<12||h<12){box(dc,x,y,w,h,color);return;}
    box(dc,x+5,y,w-10,1,color);box(dc,x+3,y+1,w-6,1,color);
    box(dc,x+2,y+2,w-4,1,color);box(dc,x+1,y+3,w-2,2,color);
    box(dc,x,y+5,w,h-10,color);
    box(dc,x+1,y+h-5,w-2,2,color);box(dc,x+2,y+h-3,w-4,1,color);
    box(dc,x+3,y+h-2,w-6,1,color);box(dc,x+5,y+h-1,w-10,1,color);
}
static void card(O dc,int x,int y,int w,int h,int focus,int active) {
    roundbox(dc,x,y,w,h,focus?GOLD:EDGE);
    int border=focus?2:1;
    roundbox(dc,x+border,y+border,w-2*border,h-2*border,active?ACTIVE:CARD);
}
static unsigned utf8(const char**p) {
    unsigned c=(unsigned char)*(*p)++;
    if(c<128)return c;
    if((c&224)==192&&(**p&192)==128){c=(c&31)<<6;c|=(unsigned char)*(*p)++&63;return c;}
    if((c&240)==224&&**p){c=(c&15)<<6;c|=(unsigned char)*(*p)++&63;if(**p){c<<=6;c|=(unsigned char)*(*p)++&63;}return c;}
    return '?';
}
static const Glyph *glyph(unsigned c,int large) {
    for(unsigned i=0;i<sizeof(glyphs)/sizeof(glyphs[0]);i++)
        if(glyphs[i].code==c&&glyphs[i].large==large)return glyphs+i;
    return glyphs+(large?1:0); /* '?' */
}
static int width(const char*s,int n,int large) {
    if(!s)return 0;const char*end=s+(n<0?len(s):n);int w=0;
    while(s<end&&*s)w+=glyph(utf8(&s),large)->advance;
    return w;
}
static O blend(O fore,O back,int a) {
    int r=(((fore>>16)&255)*a+((back>>16)&255)*(3-a))/3;
    int g=(((fore>>8)&255)*a+((back>>8)&255)*(3-a))/3;
    int b=((fore&255)*a+(back&255)*(3-a))/3;
    return (r<<16)|(g<<8)|b;
}
static void text(O dc,int x,int y,const char*s,int n,int large,O fore,O back) {
    if(!s)return;const char*end=s+(n<0?len(s):n);O colors[4];
    for(int i=1;i<4;i++)colors[i]=pixel(dc,blend(fore,back,i));
    while(s<end&&*s){
        const Glyph*g=glyph(utf8(&s),large);const unsigned char*p=font_runs+g->offset;
        for(int row=0;row<g->height;row++){
            int xx=0;
            while(xx<g->width){unsigned code=*p++,run=(code&63)+1,a=code>>6;
                if(a){ATTR(dc,2,colors[a]);FILL(dc,x+xx,y+row,run,1);}xx+=run;
            }
        }
        x+=g->advance;
    }
}
/* Word wrapping is measured in rendered pixels, never in UTF-8 byte length. */
static void wrapped(O dc,int x,int y,int w,int h,const char*s,int large,int center,O fore,O back) {
    int lineh=large?20:17;
    while(s&&*s&&h>=lineh){
        while(*s==' ')s++;
        if(*s=='\n'){s++;y+=lineh;h-=lineh;continue;}
        const char*p=s,*last=0,*end=s;int ww=0;
        while(*p&&*p!='\n'){
            const char*start=p;unsigned c=utf8(&p);int next=glyph(c,large)->advance;
            if(ww+next>w){p=start;break;}
            ww+=next;end=p;if(c==' ')last=start;
        }
        if(*p&&*p!='\n'&&last&&last>s)end=last;
        if(end==s){ /* Very long words use a measured continuation line. */
            end=p;if(end==s){utf8(&p);end=p;}
        }
        int n=end-s;
        while(n>0&&s[n-1]==' ')n--;
        text(dc,x+(center?(w-width(s,n,large))/2:0),y,s,n,large,fore,back);
        s=end;while(*s==' ')s++;if(*s=='\n')s++;
        y+=lineh;h-=lineh;
    }
}
static void chevron(O dc,int x,int y,O color){
    for(int i=0;i<4;i++){box(dc,x+i,y+i,2,1,color);box(dc,x+i,y+6-i,2,1,color);}
}
static void number(O dc,int x,int y,int n,int total) {
    char b[32];FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(b,sizeof b,"%d / %d",n,total);
    text(dc,x,y,b,-1,0,MUTED,BG);
}
static int menu_window(O p) {
    if(!p)return 0;O v=GET(p,0);
    if(v<0x1f0000||v>=0x210000||GET(v,12)!=0x52acf||GET(v,0x74)!=0x578f9)return 0;
    /* Keep live preview, playback video, status overlays and screen saver intact. */
    return v!=0x203b04&&v!=0x20463c&&v!=0x204538&&v!=0x2065ac&&v!=0x202ae0&&v!=0x203ea0;
}
static int widget_menu(O p){return p&&menu_window(GET(p,4));}
static const char *widget_name(O self) {
    O parent=GET(self,4),stack[32],node=parent?GET(parent,0x80):0;int used=0;
    for(int steps=0;steps<128&&(node||used);steps++){
        if(!node){node=stack[--used];continue;}
        if(GET(node,0x28)==self)return (const char*)GET(node,0x10);
        O right=GET(node,12);if(right&&used<32)stack[used++]=right;
        node=GET(node,8);
    }return "";
}

struct Subitem {unsigned flags;int row,col;char*text;int max,color;O image;};
static void cell(O hwnd,int row,int col,char*b,int max) {
    b[0]=0;struct Subitem s={0,row,col,b,max-1,0,0};
    int n=SEND(hwnd,0xf121,0,(O)&s);
    if(n<=0||n>=max)return;
    SEND(hwnd,0xf119,0,(O)&s);b[max-1]=0;
}
static void confirm_caption(O parent,char*b,int max) {
    b[0]=0;if(GET(parent,0)!=0x2020a0)return;
    O button=GET(parent,0x100);if(!button||GET(button,4)!=parent)return;
    O hwnd=GET(button,0x2c);if(hwnd<4||hwnd==0xffffffff)return;
    FN(0x1d1d0,int(*)(O,char*,int))(hwnd,b,max-1);b[max-1]=0;
}
int theme_list_message(O self,O hwnd,int msg,O wp,O lp) {
    if(!widget_menu(self))return FN(0x53729,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
    if(msg==0xb0)return 0;
    if(msg!=0xb1){
        int r=FN(0x53729,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
        /* Native selection invalidates its original row geometry. Redraw the
         * whole compact page so pagination stays correct with the new layout. */
        if(msg==0xf11f||msg==0xf139||msg==0xf111||msg==0xf124||msg==0xf11d)INV(hwnd,0,0);
        return r;
    }
    O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);int w=r.r,h=r.b;
    box(dc,0,0,w,h,BG);
    int count=SEND(hwnd,0xf11a,0,0),cols=SEND(hwnd,0xf11b,0,0),selected=-1;
    SEND(hwnd,0xf11c,0,(O)&selected);
    if(selected<0||selected>=count)selected=0;
    O owner=GET(self,4),setting=window(1);
    int choices=setting&&owner==GET(setting,0x174);
    char current[256];current[0]=0;
    if(choices){O main=GET(GET(setting,0xe8),0x2c);int row=-1;
        SEND(main,0xf11c,0,(O)&row);if(row>=0)cell(main,row,1,current,sizeof current);
    }
    int slots=h>=155?4:3,first=(selected/slots)*slots,rowh=(h-21)/slots;
    for(int i=0;i<slots&&first+i<count;i++){
        char label[256],value[256];cell(hwnd,first+i,0,label,sizeof label);
        value[0]=0;if(cols>1)cell(hwnd,first+i,1,value,sizeof value);
        int y=i*rowh,focus=first+i==selected,active=choices&&*current&&eq(label,current);
        O back=active?ACTIVE:CARD;
        card(dc,1,y+1,w-5,rowh-4,focus,active);
        if(*value){text(dc,12,y+4,label,-1,0,TEXT,CARD);text(dc,12,y+21,value,-1,0,focus?GOLD:MUTED,CARD);}
        else wrapped(dc,12,y+7,w-(choices?76:36),rowh-9,label,0,0,TEXT,back);
        if(active)text(dc,w-54,y+7,"Aktiv",-1,0,GOLD,ACTIVE);
        if(cols>1&&!choices)chevron(dc,w-21,y+(rowh-7)/2,MUTED);
    }
    if(count)number(dc,w-59,h-17,selected+1,count);
    text(dc,4,h-17,choices?"OK Übernehmen · Zurück":"OK Öffnen · Zurück",-1,0,MUTED,BG);
    END(hwnd,dc);return 0;
}

/* The firmware's QListView uses MenuItems, a separate control from QTableView. */
void theme_menu_draw(O self,O native,O dc,int w) {
    (void)native;
    O begin=GET(self,0x80),end=GET(self,0x84);
    int count=(end-begin)/4,selected=GET(self,0x6c),rowh=GET(self,0x70),first=GET(self,0x64);
    if(count<=0||count>256)return;
    int h=(GET(self,0x68))*rowh;
    if(h<80||h>240)h=160;
    box(dc,0,0,w,h,BG);
    int slots=4;if(h<140)slots=3;
    if(selected<0||selected>=count)selected=first;
    first=(selected/slots)*slots;rowh=h/slots;
    for(int i=0;i<slots&&first+i<count;i++){
        O item=GET(begin,(first+i)*4);if(!item)continue;
        const char*label=(const char*)GET(item,0x70);
        int focus=first+i==selected,y=i*rowh;
        card(dc,2,y+2,w-4,rowh-5,focus,0);
        O values=GET(item,0x88),values_end=GET(item,0x8c);int index=GET(item,0xa0);
        const char*value=0;
        if(values&&values_end>=values&&values_end-values<=24*128&&index>=0&&index<(int)((values_end-values)/24))
            value=(const char*)GET(values,index*24);
        if(value&&*value){
            wrapped(dc,14,y+3,w-48,18,label,0,0,TEXT,CARD);
            text(dc,14,y+21,value,-1,0,focus?GOLD:MUTED,CARD);
        }else wrapped(dc,14,y+(rowh-17)/2,w-48,rowh-5,label,0,0,TEXT,CARD);
        /* Preserve the native icon/radio bitmap rather than guessing its state. */
        if((GET(item,0x98)==2||GET(item,0x98)==3)&&GET(item,0x94))
            FN(0x1d1f4,int(*)(O,int,int,int,int,O))(dc,w-34,y+(rowh-18)/2,18,18,GET(item,0x94));
    }
}

int theme_text_message(O self,O hwnd,int msg,O wp,O lp) {
    if(msg==0xb1&&GET(self,4)&&GET(GET(self,4),0)==0x202ae0&&streaming()&&eq(widget_name(self),"mode_label")){
        O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);box(dc,0,0,r.r,r.b,BG);
        wrapped(dc,0,(r.b-20)/2,r.r,r.b,"Streaming",1,1,0x51d69b,BG);END(hwnd,dc);return 0;
    }
    if(msg!=0xb1||!widget_menu(self))
        return FN(0x56679,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
    O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);
    const char*s=(const char*)GET(self,0x4c);
    char explanation[512],title[256];
    if(GET(GET(self,4),0)==0x2020a0&&eq(widget_name(self),"info")){
        confirm_caption(GET(self,4),title,sizeof title);
        if(eq(title,"Formatieren")||eq(title,"SD-Karte formatieren")){
            while(s&&*s=='\n')s++;
            FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(explanation,sizeof explanation,"Alle Aufnahmen auf der SD-Karte\nwerden gelöscht.\n\n%s",s?s:"");s=explanation;
        }
    }
    O back=GET(GET(self,4),0)==0x206348&&eq(widget_name(self),"title")?CARD:BG;
    if(GET(GET(self,4),0)==0x206348&&len(s)==1&&s[0]>='0'&&s[0]<='9'){
        title[0]='0';title[1]=s[0];title[2]=0;s=title;
    }
    box(dc,0,0,r.r,r.b,back);
    int large=r.b>=23&&r.b<=45;
    int lines=1;
    if(width(s,-1,large)>r.r-8)large=0;
    if(r.b>40)lines=min(r.b/17,8);
    int y=lines>1?5:(r.b-(large?20:17))/2;
    wrapped(dc,4,y,r.r-8,r.b-y,s,large,1,TEXT,back);
    END(hwnd,dc);return 0;
}

int theme_graph_message(O self,O hwnd,int msg,O wp,O lp) {
    if(msg==0xb1&&GET(self,4)&&GET(GET(self,4),0)==0x20463c){
        const char*name=widget_name(self);int live=streaming();
        if((live&&eq(name,"mode_icon"))||eq(name,"wifi_icon")){
            O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);box(dc,0,0,r.r,r.b,BG);
            if(live){
                O color=FN(0x1cc3c,int(*)(const char*,int))("/tmp/v316cm-stream-ready",0)?GOLD:0x51d69b;
                if(eq(name,"mode_icon"))text(dc,2,(r.b-17)/2,"LIVE",-1,0,color,BG);
                else{for(int i=0;i<3;i++)box(dc,7+6*i,17-4*i,4,4+4*i,color);}
            }
            END(hwnd,dc);return 0;
        }
    }
    if(msg!=0xb1||!widget_menu(self)||!BYTE(GET(self,4),12))
        return FN(0x5476f,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
    const char*name=widget_name(self),*label=0;O parent=GET(self,4),vt=GET(parent,0);
    int button=0;char caption[128];
    if(eq(name,"confirm_button")){label=vt==0x206348?"Fertig":"Bestätigen";button=1;}
    else if(eq(name,"cancel_button")){label="Abbrechen";button=1;}
    else if(eq(name,"confirm")){label="Abspielen";button=1;}
    else if(eq(name,"cancel")){label="Zurück";button=1;}
    else if(eq(name,"title")||eq(name,"dialog_title")||eq(name,"prompt_title_label")){
        if(vt==0x2020a0){
            confirm_caption(parent,caption,sizeof caption);
            label=eq(caption,"Formatieren")?"SD-Karte formatieren?":eq(caption,"Zurücksetzen")?"Werkseinstellungen?":"Bestätigung";
        }
        else if(vt==0x201fdc)label="Information";
        else if(vt==0x2023a8)label="WLAN";
        else label="Hinweis";
    }else if(eq(name,"title_bg"))label="";
    else if(eq(name,"splite")||eq(name,"lt_ind")||eq(name,"ld_ind")||eq(name,"mt_ind")||eq(name,"md_ind")||eq(name,"rt_ind")||eq(name,"rd_ind"))label="";
    if(!label)return FN(0x5476f,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
    O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);box(dc,0,0,r.r,r.b,BG);
    if(r.b<4)box(dc,0,0,r.r,r.b,EDGE);
    else{
        int focus=button&&GET(self,0x44);card(dc,1,1,r.r-2,r.b-2,button?focus:1,0);
        if(r.r<50)label="!";
        wrapped(dc,5,(r.b-20)/2,r.r-10,r.b-3,label,1,1,TEXT,CARD);
    }
    END(hwnd,dc);return 0;
}

int theme_button_message(O self,O hwnd,int msg,O wp,O lp) {
    if(msg!=0xb1||!widget_menu(self))
        return FN(0x543ed,int(*)(O,O,int,O,O))(self,hwnd,msg,wp,lp);
    char label[256];label[0]=0;
    FN(0x1d1d0,int(*)(O,char*,int))(hwnd,label,sizeof label-1);
    const char*name=widget_name(self);O parent=GET(self,4);
    int confirm=eq(name,"confirm_button");
    int focus=GET(parent,0)==0x2020a0?(confirm?BYTE(parent,0x108):!BYTE(parent,0x108)):0;
    O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);box(dc,0,0,r.r,r.b,BG);
    card(dc,1,1,r.r-2,r.b-2,focus,0);
    wrapped(dc,6,(r.b-20)/2,r.r-12,r.b-4,*label?label:(confirm?"Bestätigen":"Abbrechen"),1,1,TEXT,CARD);
    END(hwnd,dc);return 0;
}

extern int original_window_proc(O,int,O,O);
int theme_window_proc(O hwnd,int msg,O wp,O lp) {
    if(msg==0xb1){
        O self=FN(0x1be28,O(*)(O))(hwnd),setting=window(1);
        if(self&&setting&&self==GET(setting,0x174)){
            O dc=BEGIN(hwnd);Rect r;RECT(hwnd,&r);box(dc,0,0,r.r,r.b,BG);
            O main=GET(GET(setting,0xe8),0x2c);int row=-1;char title[256];
            SEND(main,0xf11c,0,(O)&row);cell(main,row,0,title,sizeof title);
            card(dc,8,7,304,36,1,0);wrapped(dc,18,15,284,22,title,1,0,TEXT,CARD);
            END(hwnd,dc);return 0;
        }
    }
    if(msg==0xb0){
        O self=FN(0x1be28,O(*)(O))(hwnd);
        if(menu_window(self)){
            O dc=FN(0x1cb5c,O(*)(O))(hwnd);Rect r;RECT(hwnd,&r);
            box(dc,0,0,r.r,r.b,BG);
            FN(0x1cf00,void(*)(O))(dc);return 0;
        }
    }
    return original_window_proc(hwnd,msg,wp,lp);
}

static O window(int id) {
    O m=*(O*)0x35f9e0,node=m?GET(m,0x30):0;
    for(int i=0;node&&i<32;i++){
        int key=GET(node,16);if(key==id)return GET(node,20);
        node=GET(node,id<key?8:12);
    }return 0;
}

/* OnWindowLoaded runs twice during boot. The first call precedes tile resource
 * loading; the second follows it. Complete the native preview initialization,
 * then open the existing tile window in the same GUI call. A per-process marker
 * avoids adding writable globals to this renderer's RX-only ELF segment. */
void theme_startup_window_loaded(O presenter) {
    O manager=GET(presenter,0x90);
    if(manager)FN(GET(GET(manager,0),0x78),void(*)(O,int,int))(manager,11,0);
    int pid=FN(0x1bfa8,int(*)(void))();
    char first[64],done[64];
    FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(first,sizeof first,"/tmp/v316cm-tiles-first-%d",pid);
    FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(done,sizeof done,"/tmp/v316cm-tiles-done-%d",pid);
    if(!FN(0x1cc3c,int(*)(const char*,int))(done,0))return;
    if(FN(0x1cc3c,int(*)(const char*,int))(first,0)){
        void*f=FN(0x1c7d0,void*(*)(const char*,const char*))(first,"w");
        if(f)FN(0x1d0c8,int(*)(void*))(f);
        return;
    }
    O preview=window(2),tiles=preview?GET(preview,0x114):0;
    if(!tiles||!GET(tiles,0xec))return;
    void*f=FN(0x1c7d0,void*(*)(const char*,const char*))(done,"w");
    if(!f)return;
    FN(0x1d0c8,int(*)(void*))(f);
    FN(GET(GET(tiles,0),0x6c),void(*)(O))(tiles);
}

/* Refuse a mode transition while the recorder owns a writable media file.
 * readdir64 uses the target's ARM32 glibc dirent64 layout (name offset 19). */
static int recording(void) {
    void*d=FN(0x1c614,void*(*)(const char*))("/proc/self/fd");if(!d)return 1;
    unsigned char*entry;int active=0;
    while((entry=FN(0x1c4e0,void*(*)(void*))(d))){
        const char*name=(const char*)entry+19;char path[96],target[256],flags[192];
        FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(path,sizeof path,"/proc/self/fd/%.20s",name);
        int n=FN(0x1c534,int(*)(const char*,char*,unsigned))(path,target,sizeof target-1);
        if(n<=0)continue;target[n]=0;
        if(!FN(0x1cca4,char*(*)(const char*,const char*))(target,"/DCIM/"))continue;
        const char*ext=FN(0x1d3e4,char*(*)(const char*,int))(target,'.');
        if(!ext||(!eq(ext,".mp4")&&!eq(ext,".sec")))continue;
        FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(path,sizeof path,"/proc/self/fdinfo/%.20s",name);
        void*f=FN(0x1c7d0,void*(*)(const char*,const char*))(path,"r");if(!f){active=1;break;}
        n=FN(0x1cb90,int(*)(void*,int,int,void*))(flags,1,sizeof flags-1,f);flags[n]=0;
        FN(0x1d0c8,int(*)(void*))(f);
        char*p=FN(0x1cca4,char*(*)(const char*,const char*))(flags,"flags:");
        if(!p||(FN(0x1c594,unsigned(*)(const char*,char**,int))(p+6,0,8)&3)){active=1;break;}
    }
    FN(0x1c334,int(*)(void*))(d);return active;
}
extern void original_preview_post(O,O,int,int);
void theme_preview_post(O self,O sender,int message,int value) {
    /* Native shutter paths: 59 remote, 62 video, 81 still image. */
    if(streaming()&&(message==59||message==62||message==81))return;
    original_preview_post(self,sender,message,value);
}
extern void original_preview_key(O,int,int);
void theme_preview_key(O self,int key,int longpress) {
    if(key==61){O p=GET(self,0xe8);if(p)FN(GET(GET(p,0),0x1c),void(*)(O))(p);return;}
    if(key==60){if(!streaming())FN(0x5b001,void(*)(O))(self);return;}
    if(key==130&&!longpress&&streaming()){
        /* 0x5a658 closes visible dialogs; it is not a status query.
         * Read visibility without changing the menu before native dispatch. */
        int menu=0;
        const unsigned offsets[]={0xe8,0xec,0xf0,0x114,0x118};
        for(unsigned i=0;i<sizeof offsets/sizeof offsets[0];i++){
            O child=GET(self,offsets[i]);if(child&&BYTE(child,12)){menu=1;break;}
        }
        if(!menu)return;
    }
    original_preview_key(self,key,longpress);
}
void theme_tile_dispatch(O self,O unused,int tile) {
    (void)unused;
    if(tile==3){FN(0x5aead,void(*)(O,int))(self,1);return;}
    if(tile<0||tile>2||recording())return;
    if(tile==2){
        void*f=FN(0x1c7d0,void*(*)(const char*,const char*))("/tmp/v316cm-stream-mode","w");
        if(!f)return;FN(0x1d0c8,int(*)(void*))(f);
    }else FN(0x1c8c0,int(*)(const char*))("/tmp/v316cm-stream-mode");
    FN(0x697ad,void(*)(O))(GET(self,0x114));
    O model=GET(self,0xec);int family=tile==0?4:0;
    BYTE(model,0x11d)=family;GET(model,0x118)=0;
    FN(0x67747,void(*)(O))(model);
    FN(0x5ab55,void(*)(O,int,int))(self,0,family);
    if(tile!=2)FN(0x5a6f5,void(*)(O))(self);
    FN(0x1c94c,int(*)(const char*))( "sh /mnt/extsd/network_mode.sh >/tmp/network-mode.log 2>&1 </dev/null &");
    O status=window(4);if(status)INV(GET(status,0x2c),0,1);
    INV(GET(self,0x2c),0,1);
}
/* One-shot maintenance navigation, consumed on the GUI thread. No input events.
 * The private file is only writable through the existing root shell. */
int theme_dispatch(void*msg) {
    const char *path="/tmp/v316cm-ui-command";
    if(!FN(0x1cc3c,int(*)(const char*,int))(path,0)){
        void*f=FN(0x1c7d0,void*(*)(const char*,const char*))(path,"r");
        if(f){
            char cmd[64];int n=FN(0x1cb90,int(*)(void*,int,int,void*))(cmd,1,63,f);
            FN(0x1d0c8,int(*)(void*))(f);cmd[n]=0;
            if(n)FN(0x1c8c0,int(*)(const char*))(path);
            O setting=window(1),preview=window(2);
            char report[192];int report_len=FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(report,sizeof report,"command=%s bytes=%d manager=%x setting=%x preview=%x\n",cmd,n,*(O*)0x35f9e0,setting,preview);
            void *log=FN(0x1c7d0,void*(*)(const char*,const char*))("/tmp/v316cm-ui-result","w");
            if(log){FN(0x1cf94,int(*)(const void*,int,int,void*))(report,1,report_len,log);FN(0x1d0c8,int(*)(void*))(log);}
            if(eq(cmd,"tiles")&&preview){
                O tiles=GET(preview,0x114);FN(GET(GET(tiles,0),0x6c),void(*)(O))(tiles);
            }else if(cmd[0]=='t'&&cmd[1]=='i'&&cmd[2]=='l'&&cmd[3]=='e'&&cmd[4]=='f'&&cmd[5]=='o'&&cmd[6]=='c'&&cmd[7]=='u'&&cmd[8]=='s'&&cmd[9]==' '&&cmd[10]>='0'&&cmd[10]<='3'&&!cmd[11]&&preview){
                FN(0x69791,void(*)(O,int))(GET(preview,0x114),cmd[10]-'0');
            }else if(eq(cmd,"tileactivate")&&preview){
                O tiles=GET(preview,0x114),view=GET(tiles,0xec);
                int selected=FN(GET(GET(view,0),0x88),int(*)(O))(view);
                FN(0x66e59,void(*)(O,O,int))(tiles+0xdc,tiles,selected);
            }else if(eq(cmd,"preview-ok-check")&&preview){
                theme_preview_key(preview,130,0);
            }else if(cmd[0]=='t'&&cmd[1]=='i'&&cmd[2]=='l'&&cmd[3]=='e'&&cmd[4]==' '&&cmd[5]>='0'&&cmd[5]<='3'&&!cmd[6]&&preview){
                theme_tile_dispatch(preview,0,cmd[5]-'0');
            }else if(eq(cmd,"stream-shutter-check")&&preview&&streaming()){
                theme_preview_key(preview,130,0);
                theme_preview_post(preview,preview,59,1);
                theme_preview_post(preview,preview,62,1);
                theme_preview_post(preview,preview,81,1);
            }else if(eq(cmd,"setup")&&setting&&preview){
                for(int off=0xec;off<=0x118;off+=4){
                    if(off!=0xec&&off!=0xf0&&off!=0x114&&off!=0x118)continue;
                    O p=GET(preview,off);if(p&&BYTE(p,12))FN(GET(GET(p,0),0x1c),void(*)(O))(p);
                }
                /* The app message also loads the settings presenter/config.
                 * Switching only the visible window would show default values. */
                FN(0x5aa09,void(*)(O,O,int,int))(preview,preview,74,1);
            }else if(eq(cmd,"device")&&setting){
                FN(0x65a49,void(*)(O,O))(setting,GET(setting,0x1d8));
            }else if(eq(cmd,"mode")&&setting){
                FN(0x65a49,void(*)(O,O))(setting,GET(setting,0x1d4));
            }else if(eq(cmd,"home")&&setting){
                FN(0x65a49,void(*)(O,O))(setting,GET(setting,0x1dc));
            }else if(eq(cmd,"cancel")&&setting){
                for(int off=0x174;off<=0x18c;off+=4){
                    O p=GET(setting,off);if(p&&BYTE(p,12))FN(0x58039,void(*)(O))(p);
                }
            }else if(cmd[0]=='w'&&cmd[1]=='o'&&cmd[2]=='r'&&cmd[3]=='k'&&cmd[4]=='m'&&cmd[5]=='o'&&cmd[6]=='d'&&cmd[7]=='e'&&cmd[8]==' '&&preview){
                int mode=cmd[9]-'0';if(mode>=0&&mode<=7&&!cmd[10])FN(0x5ab55,void(*)(O,int,int))(preview,0,mode);
            }else if(eq(cmd,"dump")&&setting){
                O list=GET(GET(setting,0xe8),0x2c);int count=SEND(list,0xf11a,0,0);
                void*log=FN(0x1c7d0,void*(*)(const char*,const char*))("/tmp/v316cm-ui-result","a");
                if(log){for(int i=0;i<count&&i<64;i++){
                    char label[256];cell(list,i,0,label,sizeof label);
                    char line[300];int size=FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(line,sizeof line,"%d %s\n",i,label);
                    FN(0x1cf94,int(*)(const void*,int,int,void*))(line,1,size,log);
                }
                char value[256];cell(list,9,1,value,sizeof value);
                char line[300];int size=FN(0x1c73c,int(*)(char*,unsigned,const char*,...))(line,sizeof line,"Language display=%s; focus=%d\n",value,GET(GET(setting,0xe8),0x54));
                FN(0x1cf94,int(*)(const void*,int,int,void*))(line,1,size,log);
                FN(0x1d0c8,int(*)(void*))(log);}
            }else if(cmd[0]=='f'&&cmd[1]=='o'&&cmd[2]=='c'&&cmd[3]=='u'&&cmd[4]=='s'&&cmd[5]==' '&&setting){
                int index=0;for(int i=6;cmd[i]>='0'&&cmd[i]<='9';i++)index=index*10+cmd[i]-'0';
                O list=GET(setting,0xe8);if(index>=0&&index<SEND(GET(list,0x2c),0xf11a,0,0))FN(0x530c9,int(*)(O,int))(list,index);
            }else if(cmd[0]=='p'&&cmd[1]=='i'&&cmd[2]=='c'&&cmd[3]=='k'&&cmd[4]==' '&&setting){
                int index=0;for(int i=5;cmd[i]>='0'&&cmd[i]<='9';i++)index=index*10+cmd[i]-'0';
                O list=GET(setting,0xe8);
                if(index>=0&&index<SEND(GET(list,0x2c),0xf11a,0,0)){
                    FN(0x530c9,int(*)(O,int))(list,index);
                    FN(0x65cbd,void(*)(O))(setting);
                }
            }
        }
    }
    return FN(0x1cd1c,int(*)(void*))(msg);
}
