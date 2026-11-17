"""Concept art plus a clearly labelled composite motion study; no game integration."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[2]/'src/.tmp/fire-ground-vents-v9/final/design/FIR_04'
MEDIA=HERE/'media';MEDIA.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 report=json.loads((CACHE/'capture.json').read_text())
 assert report['frames']==120 and not report['errors']
 assert report['info']['canvas']==[1920,940]
 art=Image.open(HERE/'raw/ground-vents-lookdev.png').convert('RGB')
 art=art.resize((1920,940),Image.Resampling.LANCZOS)
 # A close view keeps the current mage in frame as a height reference.
 close=art.crop((480,440,1040,850))
 sheet=Image.new('RGB',(1120,930),'#1d1916');d=ImageDraw.Draw(sheet)
 base.text(d,(25,34),'圆形地火 · 低焰造型修订',29,'#ffbe79',True)
 sheet.paste(close.resize((1120,820),Image.Resampling.LANCZOS),(0,65))
 base.text(d,(25,909),'贴地圆圈 / 圈内连贯热纹 / 约半米低焰 · 概念稿，未实现',18,'#b6a99b')
 sheet.save(MEDIA/'ground-vent-lookdev-closeup.jpg',quality=96,subsampling=0)
 art.save(MEDIA/'ground-vent-lookdev-scene.jpg',quality=96,subsampling=0)

 # One isolated vent: concept footprint and real animated fire silhouettes.
 # Late native frame supplies clean ground, so rejected hoop geometry is absent.
 box=(770,465,1020,655);cx,cy=892-box[0],563-box[1]
 blank=np.asarray(Image.open(CACHE/'119.jpg').convert('RGB').crop(box),dtype=np.float32)
 concept=np.asarray(art.crop(box),dtype=np.float32)
 yy,xx=np.indices(blank.shape[:2]);radius=((xx-cx)/108)**2+((yy-cy)/77)**2
 region=np.clip((1.03-radius)/.18,0,1)
 frames=[]
 for index in range(120):
  local=index/30-.5333333333-.08
  heat=float(base.smooth(local/.12)*(1-base.smooth((local-1.25)/1.10)))
  strength=heat*(.97+.03*np.sin(index*.48))
  image=blank*(1-region[:,:,None]*strength)+concept*region[:,:,None]*strength
  native=np.asarray(Image.open(CACHE/f'{index:03}.jpg').convert('RGB').crop(box),dtype=np.float32)
  r,g,b=native.transpose(2,0,1)
  fire=np.clip((r-190)/60,0,1)*np.clip((r-g-25)/45,0,1)*np.clip((g-75)/65,0,1)
  fire*=region*.64*heat
  image=image*(1-fire[:,:,None])+native*fire[:,:,None]
  image=Image.fromarray(np.uint8(np.clip(image,0,255))).resize((750,570),Image.Resampling.LANCZOS)
  out=Image.new('RGB',(750,674),'#1d1916');d=ImageDraw.Draw(out)
  base.text(d,(18,27),'圆形地火 · 近景动效示意',24,'#ffbe79',True)
  out.paste(image,(0,52))
  phase='圆圈聚热' if local<.18 else '圈内低焰翻卷' if local<1.25 else '余焰与热纹渐退' if local<2.35 else '消散完成'
  base.text(d,(18,642),phase,18,'#ffc78c')
  base.text(d,(732,659),'概念合成 · 非运行实现',13,'#a99b8d',anchor='rm')
  frames.append(out)
 base.video(MEDIA/'ground-vent-lookdev-motion.mp4',iter(frames),(750,674))
 base.preview([frames[round(i*1.5)] for i in range(80)],MEDIA/'ground-vent-lookdev-motion.gif',750)
 data={
  'artBackend':'OpenAI image_gen cloud editing tool',
  'rawArt':'raw/ground-vents-lookdev.png','prompt':'lookdev-prompt.txt',
  'references':['../../../src/.tmp/fire-ground-vents-v9/final/design/FIR_04/036.jpg','../reference-seals-v3/assets/FIR-source.png'],
  'artDirection':'Low fire, about .4-.6m; five flat circular vents; dark-orange engraved rims and broad connected inner heat flows.',
  'motionMethod':'Concept ground-footprint art and native fire-frame color masks are composited on clean ground. 120 frames at 30fps. This is a look-development animatic, not a native implementation of this art.',
  'sourceCaptureErrors':report['errors'],
  'generationStatus':'success','artAcceptance':'Pending user review',
  'nativePrototypeStatus':'Size/anchor study only; its solid outline treatment is superseded by the look-development art.',
  'productIntegration':False,
  'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'raw/ground-vents-lookdev.png',HERE/'lookdev-prompt.txt']}
 }
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 with Image.open(MEDIA/'ground-vent-lookdev-motion.gif') as gif:
  duration=0
  for frame in range(gif.n_frames):gif.seek(frame);duration+=gif.info['duration']
  assert gif.n_frames>40 and duration==4000
 print(json.dumps({'frames':120,'fps':30,'art':art.size,'closeup':sheet.size,'artAcceptance':'pending user review','productIntegration':False}),flush=True)

if __name__=='__main__':main()
