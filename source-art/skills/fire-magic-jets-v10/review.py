from pathlib import Path
import importlib.util,json,hashlib
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def main():
 raw=HERE/'raw/magic-jets.png'
 image=Image.open(raw).convert('RGB')
 assert image.width>image.height and image.width>=1400
 scene=image.resize((1920,940),Image.Resampling.LANCZOS)
 scene.save(HERE/'media/magic-jets-scene.jpg',quality=96,subsampling=0)
 crop=scene.crop((480,420,1060,840)).resize((1160,840),Image.Resampling.LANCZOS)
 out=Image.new('RGB',(1160,950),'#1d1916');d=ImageDraw.Draw(out)
 base.text(d,(24,32),'发光法阵 · 中心垂直喷焰',29,'#ffbe79',True)
 out.paste(crop,(0,65))
 base.text(d,(24,927),'橙金法阵 / 约半米高的集中喷流 / 概念造型，尚未实现',18,'#b6a99b')
 out.save(HERE/'media/magic-jets-closeup.jpg',quality=96,subsampling=0)
 data={
  'backend':'OpenAI image_gen built-in cloud editing tool',
  'editTarget':'../fire-ground-vents-v9/media/ground-vent-lookdev-scene.jpg',
  'styleReference':'../reference-seals-v3/assets/FIR-source.png',
  'prompt':'prompt.txt','raw':'raw/magic-jets.png',
  'processing':'Pillow resizing, cropping, and captions only; no local generative model.',
  'generationStatus':'success','artAcceptance':'Pending user review','productIntegration':False,
  'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [raw,HERE/'prompt.txt']},
  'validation':{'rawDimensions':list(image.size),'sceneDimensions':[1920,940],'closeupDimensions':list(out.size),'review':'Visual review of bright sigils and short vertical jet silhouettes; user acceptance remains pending.'}
 }
 (HERE/'provenance.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(data['validation'],ensure_ascii=False),flush=True)

if __name__=='__main__':main()
