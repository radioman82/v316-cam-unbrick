/* Bounded, data-only WLAN configuration. This parser never evaluates shell
 * syntax. Lowercase values are literal UTF-8, including quotes and spaces.
 * Uppercase legacy keys additionally support one pair of shell-style quotes. */
#include <ctype.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define WLAN_LIMIT 4096
struct wlan_config {
    char ssid[33], password[65], mode[8], address[16], netmask[16], gateway[16];
    unsigned port;
};
extern int wlan_psk(const unsigned char *, size_t, const unsigned char *, size_t, unsigned char *);
static int wlan_ipv4(const char *s) {
    for (int part=0; part<4; part++) {
        if (!isdigit((unsigned char)*s)) return 0;
        unsigned n=0, digits=0;
        while (isdigit((unsigned char)*s)) { n=n*10+(unsigned)(*s++-'0'); if(++digits>3||n>255)return 0; }
        if (part<3) { if (*s++!='.')return 0; } else if (*s)return 0;
    }
    return 1;
}
static uint32_t wlan_ip_number(const char *s) {
    unsigned a,b,c,d; if(sscanf(s,"%u.%u.%u.%u",&a,&b,&c,&d)!=4)return 0;
    return a<<24|b<<16|c<<8|d;
}
static int wlan_utf8(const unsigned char *s) {
    while (*s) {
        unsigned x=*s++, n=0, minimum=0;
        if(x<0x80){if(x<32||x==127)return 0;continue;}
        if(x>=0xc2&&x<=0xdf){n=1;minimum=0x80;x&=31;}
        else if(x>=0xe0&&x<=0xef){n=2;minimum=0x800;x&=15;}
        else if(x>=0xf0&&x<=0xf4){n=3;minimum=0x10000;x&=7;}
        else return 0;
        for(unsigned i=0;i<n;i++){unsigned b=*s++;if((b&0xc0)!=0x80)return 0;x=x<<6|(b&63);}
        if(x<minimum||x>0x10ffff||(x>=0xd800&&x<=0xdfff))return 0;
    }
    return 1;
}
static int wlan_parse(const unsigned char *data, size_t size, struct wlan_config *out, const char **error) {
    const char *bad="KONFIGURATION UNGUELTIG";
#define WLAN_BAD(reason) do { *error=(reason); return -1; } while(0)
    if(!size||size>WLAN_LIMIT||memchr(data,0,size))WLAN_BAD(bad);
    char buffer[WLAN_LIMIT+1];memcpy(buffer,data,size);buffer[size]=0;
    char *cursor=buffer;
    if(size>=3&&!memcmp(cursor,"\xef\xbb\xbf",3))cursor+=3;
    *out=(struct wlan_config){.mode="dhcp",.port=8080};unsigned seen=0;
    while(*cursor){
        char *line=cursor,*end=strchr(cursor,'\n');
        if(end){*end=0;cursor=end+1;}else cursor+=strlen(cursor);
        size_t length=strlen(line);if(length&&line[length-1]=='\r')line[--length]=0;
        char *key=line;while(*key==' '||*key=='\t')key++;
        if(!*key||*key=='#')continue;
        char *value=strchr(key,'=');if(!value)WLAN_BAD("ZEILE OHNE GLEICHHEITSZEICHEN");
        *value++=0;char *tail=key+strlen(key);while(tail>key&&(tail[-1]==' '||tail[-1]=='\t'))*--tail=0;
        const char *keys[]={"ssid","password","ip_mode","address","netmask","gateway","http_port"};
        const char *legacy[]={"ROUTER_SSID","ROUTER_PASS","IP_MODE","CAM_IP","NETMASK","GATEWAY","STREAM_PORT"};
        int id=-1,is_legacy=0;
        for(int i=0;i<7;i++){if(!strcmp(key,keys[i]))id=i;if(!strcmp(key,legacy[i])){id=i;is_legacy=1;}}
        if(id<0)WLAN_BAD("UNBEKANNTER SCHLUESSEL");
        if(seen&(1u<<id))WLAN_BAD("DOPPELTER SCHLUESSEL");seen|=1u<<id;
        char decoded[WLAN_LIMIT+1];
        if(is_legacy&&(*value=='\''||*value=='"')){
            char quote=*value++;size_t n=0;
            while(*value&&*value!=quote){
                if(quote=='"'&&*value=='\\'&&(value[1]=='"'||value[1]=='\\'))value++;
                decoded[n++]=*value++;
            }
            if(*value++!=quote)WLAN_BAD("LEGACY-ANFUEHRUNGSZEICHEN FEHLEN");
            while(*value==' '||*value=='\t')value++;if(*value)WLAN_BAD("TEXT NACH LEGACY-WERT");
            decoded[n]=0;value=decoded;
        }
        if(!wlan_utf8((unsigned char*)value))WLAN_BAD("WERT MUSS DRUCKBARES UTF-8 SEIN");
        char *fields[]={out->ssid,out->password,out->mode,out->address,out->netmask,out->gateway};
        const size_t limits[]={sizeof out->ssid,sizeof out->password,sizeof out->mode,sizeof out->address,sizeof out->netmask,sizeof out->gateway};
        if(id<6){if(strlen(value)>=limits[id])WLAN_BAD("WERT ZU LANG");strcpy(fields[id],value);}
        else {unsigned n=0;if(!*value)WLAN_BAD("HTTP-PORT FEHLT");for(char *p=value;*p;p++){if(!isdigit((unsigned char)*p))WLAN_BAD("HTTP-PORT UNGUELTIG");n=n*10+(unsigned)(*p-'0');if(n>65535)WLAN_BAD("HTTP-PORT UNGUELTIG");}if(!n)WLAN_BAD("HTTP-PORT UNGUELTIG");out->port=n;}
    }
    if(!(seen&1)||!out->ssid[0])WLAN_BAD("WLAN-NAME FEHLT");
    size_t n=strlen(out->password);if(!(seen&2)||n<8)WLAN_BAD("PASSWORT MUSS 8 BIS 63 BYTES HABEN");
    if(n==64){for(size_t i=0;i<n;i++)if(!isxdigit((unsigned char)out->password[i]))WLAN_BAD("64-STELLIGER SCHLUESSEL MUSS HEX SEIN");}
    if(!(seen&4)&&out->address[0])strcpy(out->mode,"static");
    if(strcmp(out->mode,"dhcp")&&strcmp(out->mode,"static"))WLAN_BAD("IP-MODUS MUSS DHCP ODER STATIC SEIN");
    if(!strcmp(out->mode,"static")){
        if(!wlan_ipv4(out->address)||!wlan_ipv4(out->netmask)||(out->gateway[0]&&!wlan_ipv4(out->gateway)))WLAN_BAD("STATISCHE IP UNGUELTIG");
        uint32_t ip=wlan_ip_number(out->address),mask=wlan_ip_number(out->netmask),inv=~mask;
        if(!mask||(inv&(inv+1))||!(ip>>24)||(ip>>24)>=224||(ip>>24)==127||(ip&inv)==0||(ip&inv)==inv)WLAN_BAD("IP ODER NETZMASKE UNGUELTIG");
        if(out->gateway[0]&&(wlan_ip_number(out->gateway)&mask)!=(ip&mask))WLAN_BAD("GATEWAY AUSSERHALB DES NETZES");
    } else out->address[0]=out->netmask[0]=out->gateway[0]=0;
    *error=NULL;return 0;
#undef WLAN_BAD
}
static int wlan_serialize(const struct wlan_config *c,char *out,size_t size) {
    int n=snprintf(out,size,"ssid=%s\npassword=%s\nip_mode=%s\naddress=%s\nnetmask=%s\ngateway=%s\nhttp_port=%u\n",c->ssid,c->password,c->mode,c->address,c->netmask,c->gateway,c->port);
    return n<0||(size_t)n>=size?-1:n;
}
static int wlan_wpa(const struct wlan_config *c,char *out,size_t size) {
    unsigned char key[32];char psk[65],ssid[65];const char *hex="0123456789abcdef";
    if(strlen(c->password)==64)memcpy(psk,c->password,65);
    else {if(wlan_psk((const unsigned char*)c->password,strlen(c->password),(const unsigned char*)c->ssid,strlen(c->ssid),key))return -1;for(int i=0;i<32;i++){psk[i*2]=hex[key[i]>>4];psk[i*2+1]=hex[key[i]&15];}psk[64]=0;}
    size_t length=strlen(c->ssid);for(size_t i=0;i<length;i++){ssid[i*2]=hex[(unsigned char)c->ssid[i]>>4];ssid[i*2+1]=hex[(unsigned char)c->ssid[i]&15];}ssid[length*2]=0;
    int n=snprintf(out,size,"ctrl_interface=/var/run/wpa_supplicant\nupdate_config=0\nnetwork={\n    ssid=%s\n    psk=%s\n    key_mgmt=WPA-PSK\n}\n",ssid,psk);
    memset(key,0,sizeof key);memset(psk,0,sizeof psk);
    return n<0||(size_t)n>=size?-1:n;
}
