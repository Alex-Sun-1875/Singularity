from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 raw=HERE/'raw/light-interior-jets.png'
 reference=HERE.parent/'fire-full-disk-jets-v13/media/full-disk-jets-scene.png'
 source=Image.open(reference).convert('RGB')
 edited=Image.open(raw).convert('RGB').resize(source.size,Image.Resampling.LANCZOS)
 spatial=Image.new('L',source.size);d=ImageDraw.Draw(spatial)
 centers=[(744,642),(895,560),(1048,475),(1205,391),(1363,308)]
 for x,y in centers:d.ellipse((x-70,y-150,x+70,y+55),fill=255)
 spatial=spatial.filter(ImageFilter.GaussianBlur(7))
 original=np.asarray(source,dtype=np.float32);guide=np.asarray(edited,dtype=np.float32)
 r,g,b=original.transpose(2,0,1)
 # Only the existing saturated orange interior receives the cloud color guide.
 # Pale edges, glyphs, contour, dimensions and all unrelated pixels stay fixed.
 weight=np.clip((r-g-25)/30,0,1)*np.clip((r-130)/60,0,1)*np.clip((g-b-15)/45,0,1)
 weight*=np.asarray(spatial,dtype=np.float32)/255
 adjusted=original+weight[:,:,None]*np.maximum(guide-original,0)
 scene=Image.fromarray(np.uint8(np.clip(adjusted,0,255)))
 outside=weight==0
 assert np.array_equal(np.asarray(scene)[outside],np.asarray(source)[outside])
 selected=weight>.4
 before=original[selected].mean(axis=0);after=np.asarray(scene,dtype=np.float32)[selected].mean(axis=0)
 assert after[1]>before[1]+2 and after[2]>before[2]+2,(before.tolist(),after.tolist())
 scene.save(HERE/'media/light-interior-jets-scene.png')
 crop=scene.crop((480,360,1060,840)).resize((1160,960),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(1160,1070),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,32),'内层提亮 · 柔和金橙',29,'#ffbe79',True)
 out.paste(crop,(0,65))
 base.text(d,(24,1047),'减淡内层深橙 / 形状、高度和全圆覆盖保留 / 概念造型，未实现',18,'#b6a99b')
 out.save(HERE/'media/light-interior-jets-closeup.jpg',quality=96,subsampling=0)
 data={'backend':'OpenAI image_gen built-in cloud editing tool','editTarget':'../fire-full-disk-jets-v13/media/full-disk-jets-scene.png','prompt':'prompt.txt','raw':'raw/light-interior-jets.png','processing':'Use cloud edit as a color guide only, with positive-light blending selectively on the existing saturated orange interior. No geometry replacement. Pale edges, sigils and unrelated source pixels remain unchanged. Local resizing/cropping/captions only; no local generative model.','generationStatus':'success','artAcceptance':'Pending user review','productIntegration':False,'outsideSelectiveMaskPixelsIdentical':True,'interiorMeanRGB':{'before':before.tolist(),'after':after.tolist()},'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [raw,HERE/'prompt.txt']},'sourceSHA256':hashlib.sha256(reference.read_bytes()).hexdigest()}
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'scene':scene.size,'interiorRGBBefore':before.tolist(),'interiorRGBAfter':after.tolist(),'outsideSelectedInteriorUnchanged':True}),flush=True)

if __name__=='__main__':main()
