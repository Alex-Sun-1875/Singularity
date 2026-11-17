from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 raw=HERE/'raw/wide-transparent-jets.png'
 reference=HERE.parent/'fire-magic-jets-v10/media/magic-jets-scene.jpg'
 source=Image.open(reference).convert('RGB')
 edited=Image.open(raw).convert('RGB').resize(source.size,Image.Resampling.LANCZOS)
 mask=Image.new('L',source.size);d=ImageDraw.Draw(mask)
 centers=[(744,642),(895,560),(1048,475),(1205,391),(1363,308)]
 for x,y in centers:d.rounded_rectangle((x-112,y-120,x+112,y+65),radius=24,fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(5))
 original=np.asarray(source,dtype=np.float32)
 effect=np.asarray(edited,dtype=np.float32)
 # Keep the earlier luminous sigil and ground information visible in the fire.
 # Only positive light changes are mixed, avoiding an opaque red fill.
 light=original+.82*np.maximum(effect-original,0)
 light=Image.fromarray(np.uint8(np.clip(light,0,255)))
 scene=Image.composite(light,source,mask)
 outside=np.asarray(mask)==0
 assert np.array_equal(np.asarray(scene)[outside],np.asarray(source)[outside])
 scene.save(HERE/'media/wide-transparent-jets-scene.png')
 crop=scene.crop((480,420,1060,840)).resize((1160,840),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(1160,950),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,32),'通透三角喷焰 · 底边与法阵同宽',29,'#ffbe79',True)
 out.paste(crop,(0,65))
 base.text(d,(24,927),'火焰底宽＝圆的直径 / 橙金透光，纹理可见 / 概念造型，未实现',18,'#b6a99b')
 out.save(HERE/'media/wide-transparent-jets-closeup.jpg',quality=96,subsampling=0)
 data={'backend':'OpenAI image_gen built-in cloud editing tool','editTarget':'../fire-magic-jets-v10/media/magic-jets-scene.jpg','prompt':'prompt.txt','raw':'raw/wide-transparent-jets.png','processing':'Localized soft masks and positive-light pixel blending preserve visible prior ground/sigil detail and avoid dark opaque fill. Pixels outside masks are unchanged in the lossless PNG. Local resize/crop/caption only; no local generative model.','generationStatus':'success','artAcceptance':'Pending user review','productIntegration':False,'outsideMaskPixelsIdentical':True,'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [raw,HERE/'prompt.txt']},'sourceSHA256':hashlib.sha256(reference.read_bytes()).hexdigest()}
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'scene':scene.size,'closeup':out.size,'outsideMasksPreserved':True,'productIntegration':False}),flush=True)

if __name__=='__main__':main()
