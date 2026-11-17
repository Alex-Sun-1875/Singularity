from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 raw=HERE/'raw/full-disk-jets.png'
 reference=HERE.parent/'fire-wide-transparent-jets-v12/media/wide-transparent-jets-scene.png'
 source=Image.open(reference).convert('RGB')
 edited=Image.open(raw).convert('RGB').resize(source.size,Image.Resampling.LANCZOS)
 mask=Image.new('L',source.size);d=ImageDraw.Draw(mask)
 centers=[(744,642),(895,560),(1048,475),(1205,391),(1363,308)]
 for x,y in centers:d.rounded_rectangle((x-120,y-155,x+120,y+78),radius=24,fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(5))
 # Normal local blending allows the requested richer orange center to replace
 # the previous pale center, while preserving everything outside the effects.
 scene=Image.composite(edited,source,mask)
 outside=np.asarray(mask)==0
 assert np.array_equal(np.asarray(scene)[outside],np.asarray(source)[outside])
 scene.save(HERE/'media/full-disk-jets-scene.png')
 crop=scene.crop((480,360,1060,840)).resize((1160,960),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(1160,1070),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,32),'全圆喷焰 · 外浅内深',29,'#ffbe79',True)
 out.paste(crop,(0,65))
 base.text(d,(24,1047),'补齐前半圈 / 浅金外缘 → 橙色内层 / 略增高度 · 概念稿，未实现',18,'#b6a99b')
 out.save(HERE/'media/full-disk-jets-closeup.jpg',quality=96,subsampling=0)
 data={'backend':'OpenAI image_gen built-in cloud editing tool','editTarget':'../fire-wide-transparent-jets-v12/media/wide-transparent-jets-scene.png','prompt':'prompt.txt','raw':'raw/full-disk-jets.png','processing':'Local soft-mask composite, resize, crop and captions only. Normal blending retains the requested outside-light/inside-deeper color change. No local generative model.','generationStatus':'success','artAcceptance':'Pending user review','productIntegration':False,'outsideMaskPixelsIdentical':True,'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [raw,HERE/'prompt.txt']},'sourceSHA256':hashlib.sha256(reference.read_bytes()).hexdigest()}
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'scene':scene.size,'closeup':out.size,'outsideMasksPreserved':True,'productIntegration':False}),flush=True)

if __name__=='__main__':main()
