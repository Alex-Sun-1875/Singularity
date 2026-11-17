"""Composite the reference artwork into a motion-design board and captured 3D review frames."""
import argparse
import json
import sys
from pathlib import Path
from fractions import Fraction
from functools import lru_cache
import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
sys.path.insert(0,str(Path(__file__).resolve().parent))
from extract import FAMILIES,mapping

HERE=Path(__file__).resolve().parent
MEDIA=HERE/'media'
CACHE=HERE.parents[2]/'src/.tmp/reference-seals-v3'
FPS=30
INK='#f1d7aa'
MUTED='#b1a28c'
METEOR_SKILL_ID='FIR_02'
METEOR_ARTWORK={'FIR':FAMILIES['FIR']}


@lru_cache(maxsize=16)
def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)


def smooth(value):
    t=np.clip(value,0,1)
    return t*t*(3-2*t)


def prepare(key,style):
    plane=Image.open(HERE/'assets'/f'{key}-plane.png').convert('RGBA')
    bg=Image.open(HERE/'assets'/f'{key}-ground.png').convert('RGB')
    a=np.asarray(plane,dtype=np.float32)/255
    x0,y0,_,_=style['box']
    src=[(x-x0,y-y0) for x,y in style['cardinals']]
    dest=[(512,52),(972,512),(512,972),(52,512)]
    m=mapping(dest,src)
    y,x=np.indices(a.shape[:2]);den=m[6]*x+m[7]*y+1
    u=(m[0]*x+m[1]*y+m[2])/den-512
    v=(m[3]*x+m[4]*y+m[5])/den-512
    r=np.sqrt(u*u+v*v)/460
    theta=np.abs(np.arctan2(u,-v))/np.pi
    return bg,a,r,theta


def luminous(bg,rgba,mask,boost):
    ink=rgba.copy()
    ink[:,:,3]*=mask
    plane=Image.fromarray(np.uint8(np.clip(ink*255,0,255)))
    soft=plane.filter(ImageFilter.GaussianBlur(2.1))
    # Preserve the open stone between strokes and confine the bloom to existing linework.
    result=Image.alpha_composite(bg.convert('RGBA'),soft)
    result=Image.alpha_composite(result,plane)
    if boost>0:
        glint=plane.copy();glint.putalpha(glint.getchannel('A').point(lambda a:round(a*boost)))
        result=Image.alpha_composite(result,glint)
    return result.convert('RGB')


def board_frame(t,prepared,styles=FAMILIES):
    fire_only=len(styles)==1
    height=800
    out=Image.new('RGB',(1280,height),'#201a16')
    d=ImageDraw.Draw(out)
    title='陨石落点 · 法阵动画' if fire_only else '四职业法阵纹样 · 设计存档'
    d.text((24,13),title,font=font(30),fill=INK)
    d.text((937,23),'原稿纹样 · 动画设计',font=font(21),fill=MUTED)
    d.line((24,60,1256,60),fill='#8a6741')
    for k,(key,style) in enumerate(styles.items()):
        x=24+(k%2)*632;y=80+(k//2)*327
        d.text((x,y),style['name'],font=font(23),fill=style['hot'])
        bg,rgba,r,theta=prepared[key]
        annulus=smooth((r-.85)/.035)
        rim=smooth((t-.12-theta*.43)/.13)
        inside=smooth((t-.50-r*.40)/.18)
        hold=.92+.08*np.sin(t*4.6-r*2.4)
        fade=1-smooth((t-2.85)/.60)
        pulse=np.exp(-((t-2.74)/.11)**2)*.27
        mask=np.clip((annulus*rim+(1-annulus)*inside)*hold*fade+pulse,0,1)
        panel=luminous(bg,rgba,mask,.12+pulse)
        panel_size=(1172,608) if fire_only else (608,279)
        panel=panel.resize(panel_size,Image.Resampling.LANCZOS)
        panel_position=(54,y+37) if fire_only else (x,y+37)
        out.paste(panel,panel_position)
    d.line((24,height-58,1256,height-58),fill='#8a6741')
    stage='双圈刻纹亮起' if t<.6 else '内纹连贯显现' if t<1.15 else '蓄力 · 呼吸微光' if t<2.65 else '释放 · 余光消散'
    d.text((26,height-41),stage,font=font(21),fill=INK)
    d.text((951,height-39),'设计预览 · 待确认',font=font(19),fill=MUTED)
    return out


def video(path,frames,dimensions):
    with av.open(str(path),'w',format='mp4',options={'movflags':'+faststart'}) as movie:
        stream=movie.add_stream('libx264',rate=FPS);stream.width,stream.height=dimensions
        stream.pix_fmt='yuv420p';stream.options={'crf':'17','preset':'veryfast'};stream.codec_context.thread_count=3
        for n,image in enumerate(frames):
            f=av.VideoFrame.from_image(image);f.pts=n;f.time_base=Fraction(1,FPS)
            for packet in stream.encode(f):movie.mux(packet)
        for packet in stream.encode():movie.mux(packet)


def design(fire_only=False):
    styles=METEOR_ARTWORK if fire_only else FAMILIES
    prefix='fire-area-seal' if fire_only else 'reference-seals'
    height=800
    prepared={key:prepare(key,style) for key,style in styles.items()}
    frames=[board_frame(i/FPS,prepared,styles) for i in range(114)]
    video(MEDIA/f'{prefix}-motion.mp4',frames,(1280,height))
    frames[49].save(MEDIA/f'{prefix}-effects.jpg',quality=96,subsampling=0)
    # A 20 Hz inline preview and 30 Hz MP4 share the same animation time.
    preview_height=round(height*.75)
    preview=[frames[round(i*1.5)].resize((960,preview_height),Image.Resampling.LANCZOS) for i in range(76)]
    preview=preview[32:]+preview[:32]
    preview[0].save(MEDIA/f'{prefix}-motion.webp',save_all=True,append_images=preview[1:],duration=50,loop=0,quality=87,method=4)
    small_height=round(height*.625)
    small=[im.resize((800,small_height),Image.Resampling.LANCZOS) for im in preview]
    atlas=Image.new('RGB',(800,small_height*3))
    for j,index in enumerate([12,31,55]):atlas.paste(small[index],(0,j*small_height))
    palette=atlas.quantize(256,method=Image.Quantize.MEDIANCUT)
    indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in small]
    indexed[0].save(MEDIA/f'{prefix}-motion.gif',save_all=True,append_images=indexed[1:],duration=50,loop=0,optimize=False)


def native():
    families=list(FAMILIES)
    seal_families=set()
    for family in families:
        report=json.loads((CACHE/family/'capture.json').read_text(encoding='utf8'))
        assert report['frames']==99 and not report['errors']
        assert report['info']['renderer']=='Actors' and report['info']['player']['skeletons']
        if report['shot']==METEOR_SKILL_ID:seal_families.add(family)
    layers={}
    for family in seal_families:
        projected=json.loads((CACHE/family/'projection.json').read_text(encoding='utf8'))
        transform=mapping([(0,0),(1024,0),(1024,1024),(0,1024)],projected['projection'])
        texture=Image.open(HERE/'assets'/f'{family}.png').convert('RGBA')
        layer=texture.transform(tuple(projected['viewport']),Image.Transform.PERSPECTIVE,transform,Image.Resampling.BICUBIC)
        layers[family]=np.asarray(layer,dtype=np.float32)/255

    def scene_image(family,index):
        with Image.open(CACHE/family/f'{index:03d}.jpg') as scene:
            scene=np.asarray(scene.convert('RGB'),dtype=np.float32)/255
        if family in seal_families:
            layer=layers[family]
            age=index/30-.30
            strength=float(smooth(age/.32)*(1-smooth((age-1.45)/.24)))
            strength*=.94+.06*np.sin(max(0,age-.3)*4.8)
            # Dark actor bodies and contact shadows stay in front of the design overlay.
            visibility=smooth((scene.max(axis=2)-.43)/.20)
            alpha=np.clip(layer[:,:,3]*1.35*strength*visibility,0,1)
            scene=scene*(1-alpha[:,:,None])+layer[:,:,:3]*alpha[:,:,None]
        image=Image.fromarray(np.uint8(np.clip(scene*255,0,255)))
        # Keep the whole circle and player visible while making the new pattern readable.
        box=(160,24,920,396) if family=='THU' else (200,48,840,360)
        return image.crop(box)

    frames=[]
    for index in range(99):
        out=Image.new('RGB',(1280,800),'#201a16');d=ImageDraw.Draw(out)
        d.text((24,14),'四职业技能 · 法阵使用修订',font=font(29),fill=INK)
        d.text((1028,24),'动画设计预览',font=font(20),fill=MUTED)
        for k,family in enumerate(families):
            x=24+(k%2)*632;y=76+(k//2)*330
            title={'WAR':'战士 · 挥砍与重击','BOW':'弓箭手 · 射击与陷阱','THU':'雷系 · 电弧与连锁命中'}.get(family,FAMILIES[family]['name'])
            d.text((x,y),title,font=font(23),fill=FAMILIES[family]['hot'])
            out.paste(scene_image(family,index).resize((608,296),Image.Resampling.LANCZOS),(x,y+31))
        d.text((24,761),'法阵仅用于陨石落点',font=font(20),fill=INK)
        d.text((1024,764),'3D 录屏 + 原稿纹样',font=font(17),fill=MUTED)
        frames.append(out)
    video(MEDIA/'profession-effects-v3-3d.mp4',frames,(1280,800))
    frames[38].save(MEDIA/'profession-effects-v3-3d.jpg',quality=96,subsampling=0)
    fire=[]
    for i in range(99):
        out=Image.new('RGB',(1280,718),'#201a16');d=ImageDraw.Draw(out)
        d.text((24,12),'火系 · 原稿陨星阵',font=font(29),fill=FAMILIES['FIR']['hot'])
        out.paste(scene_image('FIR',i).resize((1280,624),Image.Resampling.LANCZOS),(0,54))
        d.text((24,685),'双圈显现 · 连贯焰纹 · 陨星落点',font=font(21),fill=INK)
        d.text((1004,686),'3D 场景合成预览',font=font(19),fill=MUTED)
        fire.append(out)
    video(MEDIA/'meteor-design.mp4',fire,(1280,718))
    phases=Image.new('RGB',(1280,820),'#201a16');d=ImageDraw.Draw(phases)
    d.text((24,16),'火系 · 施放过程',font=font(29),fill=FAMILIES['FIR']['hot'])
    for k,(frame,title) in enumerate([(15,'起阵'),(39,'蓄力'),(51,'陨星下落'),(57,'落点爆发')]):
        x=24+(k%2)*632;y=76+(k//2)*354
        d.text((x,y),title,font=font(22),fill=INK)
        phases.paste(scene_image('FIR',frame).resize((608,296),Image.Resampling.LANCZOS),(x,y+32))
    phases.save(MEDIA/'meteor-stages.jpg',quality=95,subsampling=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['design','fire','native'])
    args=parser.parse_args()
    MEDIA.mkdir(exist_ok=True)
    if args.mode=='native':native()
    else:design(fire_only=args.mode=='fire')
