from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def sampled_height(image,cx,baseline,search=220):
 rgb=np.asarray(image,dtype=np.float32)
 y0=max(0,baseline-search)
 patch=rgb[y0:baseline,cx-23:cx+24]
 r,g,b=patch.transpose(2,0,1)
 bright=(r>210)&(g>115)&(r-b>75)&(g-b>30)
 rows=np.where(bright.sum(axis=1)>=2)[0]
 return int(baseline-y0-rows.min()) if len(rows) else None

def main():
 reference=HERE/'raw/user-selected.jpg';raw=HERE/'raw/double-height.png'
 source=Image.open(reference).convert('RGB');edited=Image.open(raw).convert('RGB').resize(source.size,Image.Resampling.LANCZOS)
 centers=[(497,424),(598,366),(700,315),(822,261),(929,208)]
 original_heights=[sampled_height(source,x,y,90) for x,y in centers]
 raw_heights=[sampled_height(edited,x,y,220) for x,y in centers]
 # The unobstructed near pair and furthest flame provide scale samples.
 # The middle source samples intersect enemy sprites; interpolate their scale.
 scales=[2*original_heights[i]/raw_heights[i] for i in [0,1,4]]
 scale_by_vent=[scales[0],scales[1],scales[1]+(scales[2]-scales[1])/3,scales[1]+2*(scales[2]-scales[1])/3,scales[2]]
 target_heights=[2*original_heights[0],2*original_heights[1],104,98,2*original_heights[4]]
 scene=source.copy();mask=Image.new('L',source.size)
 yy,xx=np.indices((source.height,source.width))
 source_rgb=np.asarray(source,dtype=np.float32);sr,sg,sb=source_rgb.transpose(2,0,1)
 actors=np.zeros((source.height,source.width),dtype=bool)
 for x0,y0,x1,y1 in [(355,340,458,520),(650,132,779,310),(775,105,894,275),(827,48,922,238)]:actors[y0:y1,x0:x1]=True
 actor_pixels=actors&(((sr-sg>15)&(sr-sb>35)&(sg-sb<65)&(sr<235))|(source_rgb.mean(axis=2)<95))
 for i,((x,y),scale,height) in enumerate(zip(centers,scale_by_vent,target_heights)):
  warped=edited.transform(source.size,Image.Transform.AFFINE,(1,0,0,0,1/scale,y-y/scale),Image.Resampling.BICUBIC)
  local=Image.new('L',source.size);d=ImageDraw.Draw(local)
  d.polygon([(x-58,y+5),(x-58,y-12),(x-20,y-height-16),(x+20,y-height-16),(x+58,y-12),(x+58,y+5)],fill=255)
  local=local.filter(ImageFilter.GaussianBlur(3))
  # Keep the selected ground circle and the original flame's foot untouched.
  radius_x=[57,56,54,50,49][i];radius_y=[28,26,25,24,23][i]
  radial=np.sqrt(((xx-x)/radius_x)**2+((yy-(y+4))/radius_y)**2)
  protect=np.clip((radial-.94)/.14,0,1)
  wr,wg,wb=np.asarray(warped,dtype=np.float32).transpose(2,0,1)
  hot=np.clip((wr-238)/10,0,1)*np.clip((wg-wb-25)/55,0,1)
  orange=np.clip((wr-200)/35,0,1)*np.clip((wr-wg-45)/35,0,1)*np.clip((wg-wb-65)/45,0,1)
  # Resampling the cloud scene also moves actors. Admit only fire colors and
  # protect the actual source silhouettes, so no shifted people are pasted.
  flame=np.maximum(hot,orange);flame[actor_pixels]=0
  local=Image.fromarray(np.uint8(np.asarray(local,dtype=np.float32)*protect*flame))
  scene=Image.composite(warped,scene,local)
  mask=Image.fromarray(np.maximum(np.asarray(mask),np.asarray(local)))
 outside=np.asarray(mask)==0
 assert np.array_equal(np.asarray(scene)[outside],np.asarray(source)[outside])
 scene.save(HERE/'media/double-height-scene.png')
 box=(325,190,680,550);crop=scene.crop(box).resize((710,720),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(710,820),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(19,30),'选定版本 · 火焰高度 2×',25,'#ffbe79',True)
 out.paste(crop,(0,59));base.text(d,(19,800),'沿用原图配色、通透感与法阵 · 概念稿，未实现',14,'#b6a99b')
 out.save(HERE/'media/double-height-closeup.jpg',quality=96,subsampling=0)
 compare=Image.new('RGB',(1420,820),'#1d1916');d=ImageDraw.Draw(compare)
 for col,(im,title) in enumerate([(source,'你选的原图'),(scene,'火焰高度 2×')]):
  base.text(d,(19+col*710,30),title,25,'#ffbe79',True)
  compare.paste(im.crop(box).resize((710,720),Image.Resampling.LANCZOS),(col*710,59))
 base.text(d,(19,800),'同一底稿与构图；仅调整火焰向上的高度。设计预览，尚未实现。',16,'#b6a99b')
 compare.save(HERE/'media/height-comparison.jpg',quality=96,subsampling=0)
 samples=[]
 for x,y in centers[:2]:
  a,b=sampled_height(source,x,y),sampled_height(scene,x,y)
  samples.append({'center':[x,y],'sourceBrightTipHeightPixels':a,'candidateBrightTipHeightPixels':b,'ratio':round(b/a,3) if a and b else None})
 assert all(1.90<=s['ratio']<=2.10 for s in samples),samples
 data={'backend':'OpenAI image_gen built-in cloud editing tool','userSelectedBaseline':'raw/user-selected.jpg','prompt':'prompt.txt','rawResult':'raw/double-height.png','requestedHeightMultiplier':2,'baselineAcceptedByUser':True,'newArtAcceptance':'Pending user review','productIntegration':False,'processing':'The cloud draft overshot the requested height. Deterministic vertical resampling calibrates it to the selected source, anchored at each emission baseline. The middle two scales are interpolated because enemy sprites obscure their source tips. Original ground-circle footprints and pixels outside the flame masks are retained. Crop and comparison layout use Pillow.','heightCalibrationScales':scale_by_vent,'outsideMaskPixelsIdentical':True,'brightTipSamples':samples,'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [reference,raw,HERE/'prompt.txt']}}
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({'dimensions':scene.size,'samples':samples,'outsideMasksPreserved':True}),flush=True)

if __name__=='__main__':main()
