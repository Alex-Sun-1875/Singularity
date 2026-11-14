from pathlib import Path
from PIL import Image,ImageFilter
import json,uuid,shutil,hashlib

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
ASSETS=PROJECT/'src/cocos/assets/resources/ui'
CLOUD=Path('C:/Users/Alexa/.codex/generated_images/01a1c46b-eff4-7a71-a1ee-6621fccd0eb5')
sources={'hero':'exec-797e741c-73ad-4b47-8555-c76d596f036c.png','bow':'exec-6171b4c3-8132-4ad8-8569-bbd3f9f45050.png','fir':'exec-1d740156-6184-48f8-930c-bcad9070a840.png','thu':'exec-1dfcdaa1-f14e-4932-91ef-736d095414e0.png'}
records=[]
def meta(target,template,name,oldname):
 p=Path(str(target)+'.meta')
 if not p.exists():
  text=json.dumps(template,ensure_ascii=False,indent=2).replace(template['uuid'],str(uuid.uuid4())).replace(oldname,name)
  p.write_text(text,encoding='utf8')

for family,filename in sources.items():
 original=CLOUD/filename;saved=ROOT/'sources'/('hero-cutout-generated.png' if family=='hero' else 'skill-'+family+'-atlas-generated.png');shutil.copyfile(original,saved);image=Image.open(saved).convert('RGBA')
 record={'family':family,'original_cloud_file':str(original),'original_sha256':hashlib.sha256(saved.read_bytes()).hexdigest(),'prompt':'prompts/asset-'+family+'.txt','generation_status':'complete','art_review_status':'Assistant reviewed: coherent style and individual motifs; user final in-game review pending','exports':[]}
 if family=='hero':
  alpha=image.getchannel('A').filter(ImageFilter.MinFilter(3));image.putalpha(alpha);image=image.crop(alpha.getbbox());image.thumbnail((496,1248),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(512,1280));canvas.alpha_composite(image,((512-image.width)//2,1280-image.height-8));target=ASSETS/'quiet-bronze/raphael-portrait-v2.png';canvas.save(target);template=json.loads((ASSETS/'quiet-bronze/forge-room-v2.png.meta').read_text(encoding='utf8'));meta(target,template,'raphael-portrait-v2','forge-room-v2');record['exports'].append({'file':target.relative_to(PROJECT).as_posix(),'method':'Pillow alpha erosion 1 source pixel to remove matte fringes; tight crop, aspect-preserving resize, transparent 512x1280 canvas'})
 else:
  keys=[family.upper()+f'_{i:02}' for i in range(1,6)]+[family.upper()+'_P1',family.upper()+'_P2']
  if family=='thu':keys+=['COM_01','COM_02']
  for index,key in enumerate(keys):
   x,y=index%3,index//3;box=(round(x*image.width/3),round(y*image.height/3),round((x+1)*image.width/3),round((y+1)*image.height/3));tile=image.crop(box).resize((256,256),Image.Resampling.LANCZOS);name='rpg-'+key.lower().replace('_','-');target=ASSETS/'combat-relief'/(name+'.png');tile.save(target);template=json.loads((ASSETS/'combat-relief/skill-war-01.png.meta').read_text(encoding='utf8'));meta(target,template,name,'skill-war-01');record['exports'].append({'skill':key,'source_rect':box,'file':target.relative_to(PROJECT).as_posix(),'method':'Pillow uniform 3x3 atlas crop and Lanczos 256px export'})
 records.append(record)
(ROOT/'painted-assets-provenance.json').write_text(json.dumps({'method':'OpenAI built-in image_gen; transparent hero extraction and separate illustrated family atlases; deterministic local exports only','assets':records},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Exported full-body portrait and 23 illustrated skill icons; seven approved WAR icons were cropped separately.')
