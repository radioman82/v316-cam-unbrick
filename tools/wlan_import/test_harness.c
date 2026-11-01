/* Host-only parser/serialization/PSK harness. No device or network operations. */
#include "config.h"
#ifdef _WIN32
#include <fcntl.h>
#include <io.h>
#endif
int main(int argc,char **argv){
#ifdef _WIN32
    _setmode(_fileno(stdin),_O_BINARY);_setmode(_fileno(stdout),_O_BINARY);
#endif
    unsigned char data[WLAN_LIMIT+2];size_t n=fread(data,1,sizeof data,stdin);
    struct wlan_config c;const char *error;if(wlan_parse(data,n,&c,&error)){fprintf(stderr,"%s\n",error);return 1;}
    char output[1024];int len=argc>1&&!strcmp(argv[1],"wpa")?wlan_wpa(&c,output,sizeof output):wlan_serialize(&c,output,sizeof output);
    if(len<0)return 2;return fwrite(output,1,(size_t)len,stdout)==(size_t)len?0:2;
}
