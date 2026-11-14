"""Derive an opaque painted stone face and separate cold-blue carved light."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageDraw, ImageFilter, ImageOps
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'source-art/maps/waypoints-carved-v6'
RUNTIME=ROOT/'src/cocos/assets/resources/flat2d/waypoints-v1'
SOURCE=Path(r'C:/Users/Alexa/.codex/generated_images/01a1b873-5272-72a3-a18c-03223c658990/exec-90db6f7f-8f40-46fc-a611-b895d26be3c9.png')

def mirror(image):
    assert image.width%2==0
    half=image.crop((0,0,image.width//2,image.height))
    result=Image.new('RGBA',image.size)
    result.paste(half,(0,0));result.paste(ImageOps.mirror(half),(image.width//2,0))
    return result

def shrink(image,size):
    return mirror(image.resize(size,Image.Resampling.LANCZOS))

def main():
    ART.mkdir(parents=True,exist_ok=True);RUNTIME.mkdir(parents=True,exist_ok=True)
    shutil.copy2(SOURCE,ART/'carved-waystone-generated.png')
    raw=Image.open(SOURCE).convert('RGBA')
    # Keep a centered even-width crop. The cloud original stays untouched.
    source=mirror(raw.crop((40,20,984,1516)))
    p=np.asarray(source,dtype=np.float32)
    r,g,b=p[:,:,0],p[:,:,1],p[:,:,2]
    blue=np.clip((np.minimum(b-r,g-r)-9)/24,0,1)
    yy=np.mgrid[:source.height,:source.width][0]/source.height
    blue*=np.clip((yy-.28)/.04,0,1)*np.clip((.82-yy)/.04,0,1)*(p[:,:,3]/255)
    # Carving shade and grey bevel highlights remain visible while locked.
    value=r*.30+g*.55+b*.15
    base=p.copy()
    for c in range(3):base[:,:,c]=p[:,:,c]*(1-blue)+value*blue
    face=mirror(Image.fromarray(base.astype('uint8')))
    light=Image.new('RGBA',source.size,(145,226,242,0))
    light.putalpha(Image.fromarray((blue*255).astype('uint8')))
    light=mirror(light)
    face=shrink(face,(512,768));core=shrink(light,(512,768))
    face.save(RUNTIME/'waystone-face-carved-v6.png');core.save(RUNTIME/'waystone-rune-carved-v6.png')
    # A soft layer is independent of the stable carved core.
    a=core.getchannel('A').resize((256,384),Image.Resampling.LANCZOS)
    glow=Image.new('RGBA',(256,384),(98,187,217,0))
    glow.putalpha(a.filter(ImageFilter.GaussianBlur(5)))
    glow=mirror(glow);glow.save(RUNTIME/'waystone-glow-carved-v6.png')
    # The same recessed medallion becomes an inset floor stone where needed.
    crop=(60,240,452,632)
    ff=face.crop(crop).resize((512,512),Image.Resampling.LANCZOS)
    fc=core.crop(crop).resize((512,512),Image.Resampling.LANCZOS)
    mask=Image.new('L',(512,512),0)
    ImageDraw.Draw(mask).polygon([(152,8),(360,8),(504,152),(504,360),(360,504),(152,504),(8,360),(8,152)],fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(1))
    for image in [ff,fc]:image.putalpha(Image.fromarray((np.asarray(image.getchannel('A'),dtype=np.float32)*np.asarray(mask)/255).astype('uint8')))
    ff=mirror(ff);fc=mirror(fc)
    ff.save(RUNTIME/'waystone-floor-face-carved-v6.png');fc.save(RUNTIME/'waystone-floor-carved-v6.png')
    review=Image.new('RGB',(768,768),'#444750');review.paste(face,(0,0),face);review.paste(core,(0,0),core)
    review.paste(ff.resize((192,192)),(550,320),ff.resize((192,192)))
    review.paste(fc.resize((192,192)),(550,320),fc.resize((192,192)))
    review.save(ART/'material-review.jpg',quality=94)
    outputs=[]
    for name in ['face','rune','glow','floor-face','floor']:
        path=RUNTIME/('waystone-'+name+'-carved-v6.png');image=Image.open(path);p=np.asarray(image,dtype=np.int16)
        error=int(np.abs(p-p[:,::-1]).max());assert error==0
        outputs.append({'path':path.relative_to(ROOT).as_posix(),'size':list(image.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgbaMirrorMaxError':error,'alphaAbove128Fraction':float((p[:,:,3]>128).mean())})
    record={'tool':'OpenAI image_gen built-in cloud','mode':'new reference-guided painted prop','userCorrections':['bilateral symmetry','change the disliked previous style'],'reference':'original user stone-hall image, necessary 470x470 crop only','originalSource':str(SOURCE),'originalSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generationStatus':'succeeded','prompt':'prompt.txt','processing':'Pillow centered crop + exact left-half mirror; cold-blue incisions selected by channel excess, desaturated in diffuse and emitted on a separate alpha layer; floor medallion derived locally','artAcceptance':'material sample reviewed; runtime pending','outputs':outputs}
    (ART/'generation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
