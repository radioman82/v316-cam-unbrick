"""Build v23's central UI renderer and SD resource overrides from verified v22."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from thumb import enc_bw
from generate_font import generate

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'firmware/ui_theme'
GNU=Path(r'C:/Program Files (x86)/Arm GNU Toolchain arm-none-eabi/13.3 rel1/bin')


def geometry(tree,name,rect):
    widget=tree.find(f".//widget[@name='{name}']")
    if widget is None:raise ValueError(name)
    r=widget.find("property[@name='geometry']/rect")
    for tag,value in zip(('x','y','width','height'),rect):r.find(tag).text=str(value)


def resources():
    (OUT/'layout').mkdir(parents=True,exist_ok=True)
    (OUT/'images').mkdir(exist_ok=True)
    changed={
      'SettingWindow.ui':{'mode_gview':(8,7,100,34),'device_gview':(111,7,100,34),'return_gview':(214,7,98,34),'listtable':(8,48,304,192)},
      'Sublist.ui':{'Sublist':(0,0,320,240),'sublist_view':(8,48,304,192)},
      'Submenu.ui':{'Dialog':(8,7,304,224),'submenu_title':(2,0,300,36),'submenulist_View':(0,40,304,176)},
      'Dialog.ui':{'Dialog':(8,20,304,200),'dialog_title':(4,4,296,36),'info_text':(10,48,284,140)},
      'Prompt.ui':{'prompt_title_label':(12,36,296,36),'prompt_info_label':(16,82,288,118)},
      'SettingHandlerWindow.ui':{'setting_handler_label':(20,143,280,56)},
      'VoiceCtrlListWindow.ui':{'return_button':(8,7,76,34),'voice_ctrl_list':(90,7,222,34),'splite':(8,44,304,1),'listtable':(8,50,304,182)},
      'PlaylistWindow.ui':{'tl_playlist':(10,7,300,36),'list_view':(8,49,304,146),'confirm':(10,202,146,32),'cancel':(164,202,146,32)},
      'USBModeWindow.ui':{'usb_connect_list':(8,7,304,36),'listtable':(8,48,304,192)},
      'MediaWindow.ui':{'tl_file':(54,10,154,24),'tl_card':(254,10,64,24),'tv_media':(8,48,304,192)},
    }
    for name in ('OKDialog.ui','InfoDialog.ui','TipDialog.ui','WifiDialog.ui'):
        changed[name]={'title':(8,7,304,36),'info':(14,54,292,110 if name=='OKDialog.ui' else 164),'splite':(14,45,292,1)}
    changed['OKDialog.ui'].update(confirm_button=(10,184,146,44),cancel_button=(164,184,146,44))
    changed['OKDialogSmall.ui']={'OKDialog':(8,24,304,192),'title':(141,10,22,24),'info':(12,42,280,62),'confirm_button':(12,124,136,46),'cancel_button':(156,124,136,46),'splite':(12,110,280,1)}
    changed['TimeSettingWindow.ui']={'title_bg':(8,7,224,36),'confirm_button':(240,7,72,36),'title':(18,12,204,24)}
    for i,col in enumerate(('l','m','r')):
        x=12+100*i
        changed['TimeSettingWindow.ui'].update({f'{col}_label':(x,58,90,22),f'{col}_text':(x,119,90,40),f'{col}t_ind':(x,111,90,1),f'{col}d_ind':(x,169,90,1),f'{col}up_arrow':(x,82,90,28),f'{col}down_arrow':(x,173,90,28)})
    for source in (HERE/'original/layout').iterdir():
        if source.suffix=='.ui' and source.name in changed:
            tree=ET.parse(source)
            for name,rect in changed[source.name].items():geometry(tree,name,rect)
            ET.indent(tree,space=' ');tree.write(OUT/'layout'/source.name,encoding='utf-8',xml_declaration=True)
        else:(OUT/'layout'/source.name).write_bytes(source.read_bytes())
    translations=json.loads((HERE/'de.json').read_text(encoding='utf-8'))
    tree=ET.parse(HERE/'original/zh-DE.xml')
    labels=[]
    for e in tree.getroot():
        key=e.get('name')
        lookup=key+'[]' if e.tag=='string-array' else key
        if lookup in translations:
            value=translations[lookup]
            if e.tag=='string' and isinstance(value,str):e.text=value
            elif e.tag=='string-array' and isinstance(value,list):
                assert len(e)==len(value),key
                for item,text in zip(e,value):item.text=text
        if e.tag=='string' and key.startswith('ml_') and not key.endswith(('width','height')):labels.append((key,e.text or ''))
        if e.tag=='string-array':
            for item in e:
                if item.text in ('Ausschalten','Turn Off','Turn 0ff'):item.text='Aus'
                elif item.text in ('Einschalten','Turn On'):item.text='Ein'
    ET.indent(tree,space='  ');tree.write(OUT/'zh-DE.xml',encoding='utf-8',xml_declaration=True)
    f=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',14)
    keys=ET.parse(HERE/'original/setting_keys.xml').getroot()
    menu_keys={item.text for array in keys for item in array}
    too_wide=[(k,t) for k,t in labels if k in menu_keys and f.getlength(t)>266]
    assert not too_wide,too_wide
    def tile(name,title,size=(100,34),hi=False):
        scale=3;im=Image.new('RGBA',(size[0]*scale,size[1]*scale),(16,21,28,255));d=ImageDraw.Draw(im)
        d.rounded_rectangle((1*scale,1*scale,(size[0]-2)*scale,(size[1]-2)*scale),radius=6*scale,fill='#3c321c' if hi else '#1b2430',outline='#ffb300' if hi else '#344151',width=(2 if hi else 1)*scale)
        font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',14*scale)
        box=d.textbbox((0,0),title,font=font);x=(size[0]*scale-d.textlength(title,font=font))/2;y=(size[1]*scale-(box[3]-box[1]))/2-box[1]
        d.text((x,y),title,font=font,fill='#eef3fa')
        im.resize(size,Image.Resampling.LANCZOS).save(OUT/'images'/name)
    nav={'normal':'Gerät','setting_return':'Zurück','rec':'Video','timelapse_rec':'Zeitraffer','track_rec':'Video','delay_rec':'Zeitlupe','loop_rec':'Endlos','pic':'Foto','time_pic':'Timer','auto_pic':'Auto-Foto','continue_pic':'Serie'}
    for name,label in nav.items():
        stem='button_'+name+('_setting' if name not in ('normal','setting_return') else '')
        if name=='normal':stem='button_normal_setting'
        for hi in (False,True):tile(stem+('_hi' if hi else '')+'.png',label,hi=hi)
    tile('button_time_setting_return.png','Fertig',(52,36))
    tile('button_voice_ctrl_list_return.png','Zurück',(76,34))
    Image.new('RGB',(320,240),'#10151c').save(OUT/'images/bg.png')
    for direction in ('up','down'):
        for hi in (False,True):
            im=Image.new('RGBA',(90,28),'#10151c');d=ImageDraw.Draw(im)
            d.rounded_rectangle((1,1,88,26),radius=5,fill='#3c321c' if hi else '#1b2430',outline='#ffb300' if hi else '#344151',width=2 if hi else 1)
            pts=[(38,17),(45,10),(52,17)] if direction=='up' else [(38,10),(45,17),(52,10)]
            d.line(pts,fill='#ffb300' if hi else '#abb9ca',width=2)
            im.save(OUT/'images'/('datetime_arrow_'+direction+('_hi' if hi else '')+'.png'))
    # The factory quick menu has image-only controls, separate from the setup
    # list. Keep the native normal/highlight state switching and replace skins.
    for kind in ('wifi','rec_audio','rc','lock','shutdown','voice_ctrl'):
        for hi in (False,True):
            scale=3;im=Image.new('RGBA',(162,162),'#10151c');d=ImageDraw.Draw(im)
            d.rounded_rectangle((3,3,156,156),radius=18,fill='#3c321c' if hi else '#1b2430',outline='#ffb300' if hi else '#344151',width=6 if hi else 3)
            color='#ffb300' if hi else '#eef3fa'
            def line(points,width=2):d.line([(x*scale,y*scale)for x,y in points],fill=color,width=width*scale)
            def arc(rect,start,end):d.arc(tuple(x*scale for x in rect),start,end,fill=color,width=2*scale)
            if kind=='wifi':
                for r in (7,13,19):arc((27-r,32-r,27+r,32+r),218,322)
                d.ellipse((25*3,33*3,29*3,37*3),fill=color)
            elif kind in ('rec_audio','voice_ctrl'):
                d.rounded_rectangle((22*3,12*3,32*3,31*3),radius=5*3,outline=color,width=2*3)
                arc((18,21,36,36),0,180);line([(27,36),(27,41)]);line([(21,41),(33,41)])
                if kind=='voice_ctrl':arc((31,15,41,29),290,70)
            elif kind=='rc':
                d.rounded_rectangle((19*3,14*3,35*3,42*3),radius=3*3,outline=color,width=2*3)
                for x,y in ((24,24),(30,24),(24,30),(30,30)):d.ellipse((x*3,y*3,(x+1)*3,(y+1)*3),fill=color)
                arc((18,5,36,19),215,325)
            elif kind=='lock':
                arc((20,11,34,29),180,360)
                d.rounded_rectangle((16*3,24*3,38*3,42*3),radius=3*3,outline=color,width=2*3)
                line([(27,30),(27,35)])
            else:arc((13,13,41,41),300,600);line([(27,10),(27,27)],3)
            im.resize((54,54),Image.Resampling.LANCZOS).save(OUT/'images'/('button_'+kind+('_hi' if hi else '')+'.png'))
    im=Image.new('RGBA',(60,50),'#10151c');d=ImageDraw.Draw(im)
    d.rounded_rectangle((1,1,58,48),radius=6,fill='#1b2430',outline='#344151')
    d.line([(20,20),(30,30),(40,20)],fill='#ffb300',width=3);im.save(OUT/'images/button_shortcut_menu.png')
    Image.new('RGB',(320,2),'#344151').save(OUT/'images/orna_line2.png')
    Image.new('RGB',(2,156),'#344151').save(OUT/'images/orna_line3.png')
    for selected in (False,True):
        im=Image.new('RGBA',(24,24),(0,0,0,0));d=ImageDraw.Draw(im)
        d.ellipse((3,3,20,20),outline='#ffb300' if selected else '#abb9ca',width=2)
        if selected:d.ellipse((8,8,15,15),fill='#ffb300')
        im.save(OUT/'images'/('submenu_select.png' if selected else 'submenu_unselect.png'))
    return changed


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    generate(HERE/'font.h')
    data=bytearray((ROOT/'firmware/sdvcam/sdvcam_menu_v22').read_bytes())
    assert hashlib.md5(data).hexdigest()=='ece022b21206d5bc28058b24cf3790d7'
    with tempfile.TemporaryDirectory() as temp:
        t=Path(temp)
        cc=GNU/'arm-none-eabi-gcc.exe';ld=GNU/'arm-none-eabi-ld.exe'
        subprocess.run([str(cc),'-mcpu=cortex-a7','-mthumb','-mfloat-abi=soft','-Os','-ffreestanding','-fno-builtin','-fno-stack-protector','-fno-unwind-tables','-fno-asynchronous-unwind-tables','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Wno-misleading-indentation','-c',str(HERE/'theme.c'),'-o',str(t/'theme.o')],check=True)
        subprocess.run([str(cc),'-mcpu=cortex-a7','-mthumb','-c',str(HERE/'entry.s'),'-o',str(t/'entry.o')],check=True)
        (t/'link.ld').write_text('SECTIONS { . = 0x400000; .text : { *(.text*) } .rodata : { *(.rodata*) } .data : { *(.data*) } .bss : { *(.bss*) *(COMMON) } }\n')
        subprocess.run([str(ld),'-T',str(t/'link.ld'),str(t/'theme.o'),str(t/'entry.o'),'-o',str(t/'theme.elf')],check=True)
        symbols={}
        for line in subprocess.check_output([str(GNU/'arm-none-eabi-nm.exe'),str(t/'theme.elf')],text=True).splitlines():
            parts=line.split()
            if len(parts)==3:symbols[parts[2]]=int(parts[0],16)
        subprocess.run([str(GNU/'arm-none-eabi-objcopy.exe'),'-O','binary',str(t/'theme.elf'),str(t/'theme.bin')],check=True)
        payload=(t/'theme.bin').read_bytes()
        (OUT/'renderer.elf').write_bytes((t/'theme.elf').read_bytes())
    patches=[]
    def patch(a,old,new):
        off=a-0x10000
        assert data[off:off+len(old)]==old,hex(a)
        assert len(old)==len(new)
        data[off:off+len(new)]=new;patches.append([off,len(new)])
    patch(0x200590,struct.pack('<I',0x53729),struct.pack('<I',symbols['theme_list_message']|1))
    patch(0x2015c4,struct.pack('<I',0x56679),struct.pack('<I',symbols['theme_text_message']|1))
    patch(0x201028,struct.pack('<I',0x5476f),struct.pack('<I',symbols['theme_graph_message']|1))
    patch(0x200fb4,struct.pack('<I',0x543ed),struct.pack('<I',symbols['theme_button_message']|1))
    patch(0x54a38,bytes.fromhex('2de9f04f'),enc_bw(0x54a38,symbols['theme_menu_draw']))
    patch(0x57184,bytes.fromhex('61292de9f043'),enc_bw(0x57184,symbols['theme_window_proc'])+bytes.fromhex('00bf'))
    from thumb import enc_bl
    patch(0x675e4,enc_bl(0x675e4,0x24ae28),enc_bl(0x675e4,symbols['theme_mode_items']))
    patch(0x5081e,bytes.fromhex('ccf77eea'),enc_bl(0x5081e,symbols['theme_dispatch']))
    patch(0x24ada0,bytes.fromhex('70b50446'),enc_bw(0x24ada0,symbols['theme_tile_dispatch']))
    patch(0x24adf8,bytes.fromhex('3c2906d0'),enc_bw(0x24adf8,symbols['theme_preview_key']))
    patch(0x5aa08,bytes.fromhex('2de9f743'),enc_bw(0x5aa08,symbols['theme_preview_post']))
    patch(0x6c0e8,bytes.fromhex('d4f89000'),enc_bw(0x6c0e8,symbols['startup_menu_entry']))
    offset=(len(data)+4095)&~4095
    data.extend(bytes(offset-len(data)));data.extend(payload)
    # The unused NOTE program header becomes one RX load; existing LOADs, unwind
    # table, dynamic loader and all original addresses remain unchanged.
    note=52+6*32
    assert struct.unpack_from('<I',data,note)[0]==4
    struct.pack_into('<8I',data,note,1,offset,0x400000,0x400000,len(payload),len(payload),5,4096)
    patches.append([note,32]);patches.append([offset,len(payload)])
    binary=OUT/'sdvcam_menu_v23';binary.write_bytes(data)
    changed=resources()
    manifest={'baseline':'ece022b21206d5bc28058b24cf3790d7','md5':hashlib.md5(data).hexdigest(),'patches':patches,'symbols':symbols,'layouts':list(changed),'payload_bytes':len(payload)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(binary,len(data),'MD5',manifest['md5'],'renderer',len(payload))


if __name__=='__main__':build()
