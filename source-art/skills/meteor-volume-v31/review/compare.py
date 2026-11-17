"""Read-only v29/v30 review. Image brightness is not inferred RGBA opacity."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RES=ROOT/'src/cocos/assets/resources/vfx/production'
reference=Image.open(ROOT/'source-art/skills/fire-distinct-shapes-design-v29/fire-distinct-shapes-v29.png').convert('RGB')
native=Image.open(ROOT/'src/.tmp/fire-distinct-runtime-v30/meteor-final-empty-r1/FIR_02/075.jpg').convert('RGB')

def metrics(im,centre,radii):
    p=np.asarray(im,dtype=float)/255;y,x=np.mgrid[:im.height,:im.width]
    area=((x-centre[0])/radii[0])**2+((y-centre[1])/radii[1])**2<1
    warm=area&(p[...,0]>.40)&(p[...,0]-p[...,2]>.20)&(p[...,1]-p[...,2]>.07)
    bright=area&(p[...,0]>.85)&(p[...,1]>.55)&(p[...,0]-p[...,2]>.20)
    q=p[warm];l=q@np.array([.2126,.7152,.0722])
    return dict(ellipsePixels=int(area.sum()),warmPixels=int(warm.sum()),warmDisplayCoverage=float(warm.sum()/area.sum()),brightDisplayCoverage=float(bright.sum()/area.sum()),
        warmRGBQuantiles255=np.round(np.quantile(q,[.10,.50,.90],axis=0)*255,1).tolist(),warmLumaQuantiles255=np.round(np.quantile(l,[.10,.50,.90])*255,1).tolist())

results=dict(caveat='Display photometry only, not opacity extraction or a matched lighting/camera measurement. Warm/bright thresholds reject dark stones and neutral floor; reference floor reflection can still contribute to its rendered appearance.',
    v29=metrics(reference,(1106,882),(210,114)),
    v30=metrics(native,(596,794),(530,310)))
for name in ['fire-lance-v30','fire-field-flow-v30']:
    a=np.asarray(Image.open(RES/(name+'.png')),dtype=float)/255
    results[name]=dict(meanAlpha=float(a[...,3].mean()),fractionAbove01=float((a[...,3]>.1).mean()),fractionAbove035=float((a[...,3]>.35).mean()),fractionAbove06=float((a[...,3]>.6).mean()))
    if name=='fire-lance-v30':
        widths=[]
        for frame in range(16):
            cell=a[frame//4*96:(frame//4+1)*96,frame%4*256:(frame%4+1)*256,3]
            # This is the U .03..86 range actually used by curlingFire; V maps
            # across the ribbon. Empty source padding reduces visible width.
            used=cell[:,round(.03*256):round(.86*256)]
            widths.extend((used>.20).sum(axis=0)/96)
        results[name]['medianEffectiveCrossSectionFractionAbove02']=float(np.median(widths))
        results[name]['p90EffectiveCrossSectionFractionAbove02']=float(np.quantile(widths,.9))

canvas=Image.new('RGB',(1220,462),'#242b27');d=ImageDraw.Draw(canvas)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
d.text((12,10),'v29 原稿局部 vs v30 实景 / 仅裁切排版，非同镜头光照或alpha真值',font=font,fill='#edc282')
canvas.paste(reference.crop((930,735,1330,985)).resize((600,375)),(8,61))
canvas.paste(native.crop((35,460,1095,1120)).resize((600,375)),(612,61))
d.text((12,39),'原稿：中心外爆、厚火体、亮金褶线、互连翻卷',font=small,fill='#edc282')
d.text((616,39),'实景：贴地淡面 + 七条窄火丝，中心缺体积',font=small,fill='#edc282')
canvas.save(HERE/'v29-v30-comparison.jpg',quality=95,subsampling=0)
(HERE/'metrics.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(results,ensure_ascii=False))
