"""Preserve the cloud edit and make the selected decal exactly bilateral."""
from pathlib import Path
import hashlib
import json
import shutil
from PIL import Image, ImageFilter, ImageOps
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'source-art/maps/waypoints-symmetric-v5'
RUNTIME=ROOT/'src/cocos/assets/resources/flat2d/waypoints-v1'
SOURCE=Path(r'C:/Users/Alexa/.codex/generated_images/01a1b873-5272-72a3-a18c-03223c658990/exec-45df9d37-bfa2-447d-8fca-226d788ace0c.png')

def bilateral(image):
    assert image.width%2==0
    half=image.crop((0,0,image.width//2,image.height))
    result=Image.new('RGBA',image.size)
    result.paste(half,(0,0))
    result.paste(ImageOps.mirror(half),(image.width//2,0))
    return result

def main():
    ART.mkdir(parents=True,exist_ok=True)
    RUNTIME.mkdir(parents=True,exist_ok=True)
    shutil.copy2(SOURCE,ART/'symmetric-rune-generated.png')
    original=Image.open(SOURCE).convert('RGBA')
    symmetric=bilateral(original)
    core=bilateral(symmetric.resize((512,768),Image.Resampling.LANCZOS))
    core.save(RUNTIME/'waystone-rune-symmetric-v5.png')
    floor=symmetric.crop((0,512,1024,1536)).resize((512,512),Image.Resampling.LANCZOS)
    pixels=np.array(floor)
    yy,xx=np.mgrid[:512,:512]
    edge=np.minimum(np.minimum(xx,511-xx),np.minimum(yy,511-yy))
    pixels[:,:,3]=(pixels[:,:,3]*np.clip(edge/18.,0,1)).astype('uint8')
    floor=bilateral(Image.fromarray(pixels))
    floor.save(RUNTIME/'waystone-floor-symmetric-v5.png')
    alpha=core.getchannel('A').resize((256,384),Image.Resampling.LANCZOS)
    soft=np.asarray(alpha.filter(ImageFilter.GaussianBlur(7)),dtype=np.float32)
    wide=np.asarray(alpha.filter(ImageFilter.GaussianBlur(18)),dtype=np.float32)
    yy,xx=np.mgrid[:384,:256]
    edge=np.minimum(np.minimum(xx,255-xx),np.minimum(yy,383-yy))
    glow=Image.new('RGBA',(256,384),(153,96,240,0))
    glow.putalpha(Image.fromarray((np.minimum(160,soft*.85+wide*.40)*np.clip(edge/8.,0,1)).astype('uint8')))
    glow=bilateral(glow)
    glow.save(RUNTIME/'waystone-glow-symmetric-v5.png')
    sheet=Image.new('RGB',(768,768),'#444750')
    sheet.paste(core,(0,0),core)
    small=core.resize((128,192),Image.Resampling.LANCZOS)
    sheet.paste(small,(576,280),small)
    sheet.save(ART/'decal-review.jpg',quality=94)
    outputs=[]
    for name in ['rune','glow','floor']:
        path=RUNTIME/('waystone-'+name+'-symmetric-v5.png')
        image=Image.open(path)
        pixels=np.asarray(image,dtype=np.int16)
        error=int(np.abs(pixels-pixels[:,::-1]).max())
        assert error==0
        outputs.append({'path':path.relative_to(ROOT).as_posix(),'size':list(image.size),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgbaMirrorMaxError':error,'alphaAbove128Fraction':float((pixels[:,:,3]>128).mean())})
    (ART/'generation.json').write_text(json.dumps({'tool':'OpenAI image_gen built-in cloud','mode':'reference-guided edit of our original v4 decal','userCorrection':'Make the portal symmetrical','prompt':'prompt.txt','reference':'src/cocos/assets/resources/flat2d/waypoints-v1/waystone-rune-v4.png','originalSource':str(SOURCE),'originalSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'generationStatus':'succeeded','processing':'Pillow mirror of the left half about the canvas vertical axis, after each resize; original cloud edit retained unmodified. Floor crop and alpha glow derived locally.','artAcceptance':'decal visual review pending runtime','outputs':outputs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
