"""Pure pixel resize of the user's chosen fire; no generated replacement style."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def fill_missing(rgb,mask):
 # Reuse the project's eight-neighbour deterministic fill approach for tiny
 # patches of stone behind the original fire; keep character pixels known.
 result=rgb.copy();known=~mask
 for _ in range(100):
  if known.all():break
  total=np.zeros_like(result);count=np.zeros(known.shape,dtype=np.float32)
  for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
   valid=np.roll(known,(dy,dx),(0,1));total+=np.roll(result,(dy,dx),(0,1))*valid[:,:,None];count+=valid
  new=(~known)&(count>0);result[new]=total[new]/count[new,None];known[new]=True
 return result

def main():
 source_path=HERE/'raw/user-selected.jpg';source=Image.open(source_path).convert('RGB')
 original=np.asarray(source,dtype=np.float32);result=original.copy();height_scale=2.0
 sh,sw=original.shape[:2];yy,xx=np.indices((sh,sw))
 r,g,b=original.transpose(2,0,1)
 actor_area=np.zeros((sh,sw),bool)
 for x0,y0,x1,y1 in [(355,340,458,520),(650,132,779,310),(775,105,894,275),(827,48,922,238)]:actor_area[y0:y1,x0:x1]=True
 actor=actor_area&(((r-g>15)&(r-b>35)&(g-b<65)&(r<235))|(original.mean(axis=2)<95))
 centers=[(497,424,28),(598,366,26),(700,315,25),(822,261,24),(929,208,23)]
 changed=np.zeros((sh,sw),bool);samples=[]
 for i,(cx,baseline,ry) in enumerate(centers):
  anchor=baseline+4-ry
  x0,x1=max(0,cx-61),min(sw,cx+62);y0,y1=max(0,baseline-95),min(sh,anchor+13)
  patch=original[y0:y1,x0:x1].copy();pr,pg,pb=patch.transpose(2,0,1)
  color=(pr>180)&(pr-pg>16)&(pg-pb>25)&(~actor[y0:y1,x0:x1])
  # Restrict the source to its actual original flame, not adjacent effects.
  px=xx[y0:y1,x0:x1];py=yy[y0:y1,x0:x1]
  region=(np.abs(px-cx)<np.clip((py-(baseline-80))*.65+8,8,48))
  evidence=color&region
  bright=evidence&(pr>210)&(pg>115)&(pr-pb>75)&(py<anchor)
  rows=np.where(bright.sum(axis=1)>=2)[0]
  assert len(rows),i
  tip=y0+int(rows.min());old_height=baseline-tip
  target_height=height_scale*old_height
  scale=(anchor-(baseline-target_height))/(anchor-tip)
  missing=np.asarray(Image.fromarray(np.uint8(evidence)*255).filter(ImageFilter.MaxFilter(5)))>0
  missing&=~actor[y0:y1,x0:x1]
  clean=fill_missing(patch,missing)
  # Minimum physically valid alpha reconstructs the source fire color over its
  # estimated local background. Resize premultiplied color, avoiding halos.
  positive=np.maximum(patch-clean,0)/np.maximum(255-clean,1)
  negative=np.maximum(clean-patch,0)/np.maximum(clean,1)
  alpha=np.max(np.maximum(positive,negative),axis=2)
  soft=np.asarray(Image.fromarray(np.uint8(evidence)*255).filter(ImageFilter.GaussianBlur(.65)),dtype=np.float32)/255
  premult=(patch-clean*(1-alpha[:,:,None]))*soft[:,:,None]
  alpha*=soft;alpha[actor[y0:y1,x0:x1]]=0
  premult=np.clip(premult,0,255*alpha[:,:,None])
  count=anchor-y0;alpha=alpha[:count];premult=premult[:count]
  target_rows=max(1,round(count*scale));top=anchor-target_rows
  def stretch(a):return np.asarray(Image.fromarray(np.float32(a)).resize((x1-x0,target_rows),Image.Resampling.BICUBIC),dtype=np.float32)
  aa=np.clip(stretch(alpha),0,1);cc=np.stack([stretch(premult[:,:,k]) for k in range(3)],axis=2)
  cc=np.clip(cc,0,255*aa[:,:,None])
  # Remove old fire only above the untouched circular base.
  erase=missing[:count]&region[:count]&(~actor[y0:anchor,x0:x1])
  local=result[y0:anchor,x0:x1];local[erase]=clean[:count][erase];changed[y0:anchor,x0:x1]|=erase
  ya=max(0,top);offset=ya-top;yb=min(sh,anchor)
  a=aa[offset:offset+yb-ya].copy();c=cc[offset:offset+yb-ya].copy()
  a[actor[ya:yb,x0:x1]]=0;c[actor[ya:yb,x0:x1]]=0
  result[ya:yb,x0:x1]=result[ya:yb,x0:x1]*(1-a[:,:,None])+c
  changed[ya:yb,x0:x1]|=a>.00001
  samples.append({'vent':i+1,'originalBrightTipHeightPixels':old_height,'targetBrightTipHeightPixels':target_height,'upperSegmentScale':scale})
 result[actor]=original[actor]
 result[~changed]=original[~changed]
 scene=Image.fromarray(np.uint8(np.clip(result,0,255)))
 assert np.array_equal(np.asarray(scene)[~changed],np.asarray(source)[~changed])
 assert np.array_equal(np.asarray(scene)[actor],np.asarray(source)[actor])
 scene.save(HERE/'media/height2x-scene.png')
 box=(325,190,680,550)
 out=Image.new('RGB',(710,820),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(19,30),'选定版本 · 恢复两倍高度',25,'#ffbe79',True)
 out.paste(scene.crop(box).resize((710,720),Image.Resampling.LANCZOS),(0,59))
 base.text(d,(19,800),'原选图高度 2× / 原配色与法阵保留 / 概念稿，未实现',14,'#b6a99b')
 out.save(HERE/'media/height2x-closeup.jpg',quality=96,subsampling=0)
 data={'source':'raw/user-selected.jpg','baselineAcceptedByUser':True,'requestedScaleFromDoubleHeight':1.0,'scaleFromSelectedOriginal':2.0,'method':'Deterministic original-fire extraction, local stone fill and premultiplied-alpha vertical resampling. Original character pixels and circles are preserved. No new cloud/local generation for this adjustment.','samples':samples,'sourceCharacterPixelsUnchanged':True,'pixelsOutsideChangedMaskUnchanged':True,'artAcceptance':'Pending user review','productIntegration':False,'sourceSHA256':hashlib.sha256(source_path.read_bytes()).hexdigest()}
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(samples),flush=True)

if __name__=='__main__':main()
