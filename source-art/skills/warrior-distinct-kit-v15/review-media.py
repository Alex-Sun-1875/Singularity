"""Verify design-only captures and present distinct skill silhouettes side by side."""
from pathlib import Path
import hashlib,json,math,os
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
CACHE=ROOT/'src/.tmp/warrior-distinct-kit-v15/final/design'
OLD=ROOT/'src/.tmp/warrior-reference120-v14/final/design'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SHOTS=['BASIC_WAR','WAR_01','WAR_02','WAR_03','WAR_04','WAR_05','WAR_P1','WAR_P2']
def read(folder,shot):return json.loads((folder/shot/'capture.json').read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mesh_code(path):
 text=path.read_text(encoding='utf8').replace('\r\n','\n')
 return text[text.index(' private pressureMesh('):text.index(' private wave(')]
assert mesh_code(BASE/'WarriorKitStudy.ts')==mesh_code(BASE.parent/'warrior-reference120-v14/WarriorKitStudy.ts')
assert sha(BASE/'blade.png')==sha(BASE.parent/'warrior-reference120-v14/blade.png')
checks={}
for shot in SHOTS:
 a,b=read(OLD,shot),read(CACHE,shot)
 check={'sameGameHash':a['gameHash']==b['gameHash'],'sameCombatEvents':a['events']==b['events'],
  'sameTargets':a['info']['targets']==b['info']['targets'],'sameCamera':a['presentation']['camera']==b['presentation']['camera'],
  'sameFrames':a['frames']==b['frames'],'nativeSkeleton':bool(b['info']['player']['skeletons']),
  'noPageErrors':not b['errors'],'noPoolOverflow':b['style']['droppedLayers']==0}
 assert all(check.values()),(shot,check)
 for name,value in b['reviewInputs'].items():assert sha(BASE/name)==value,(shot,name)
 roles=sorted({r for f in b['roleFrames'] for r in f['roles']});check['roles']=roles
 angles=[c['obtuse'] for f in b['crossGeometrySamples'] for c in f['crossings']]
 if shot in ['WAR_02','WAR_05']:assert angles,shot
 else:assert not angles,shot
 assert all(abs(v-120)<.02 for v in angles),shot
 if angles:check['crossingObtuseDegrees']=[min(angles),max(angles)]
 if shot=='WAR_04':
  ground=b['style']['groundRecord'];assert ground['maxDistance']<=ground['radius'] and ground['maxGroundOffset']<=.071
  assert 'attack_sword_3' in b['clips']
  target=b['info']['targets'][0];assert math.hypot(target['x']-ground['centre']['x'],target['z']-ground['centre']['z'])<1e-6
  assert 'ground-crack' in roles and 'downstroke' in roles and 'earth-chip' in roles
  check['groundImpact']=ground
  sampling=b['groundSampling'];assert sampling['queries']>0 and sampling['hits']==sampling['queries']
  check['groundSampling']=sampling
 checks[shot]=check
assert len({tuple(checks[s]['roles']) for s in SHOTS[:6]})==6

FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
def font(n,bold=False):return ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),n)
specs=[('WAR_01','断空斩 · 两段定向切割'),('WAR_02','破军突袭 · 路径风痕 / 命中交叉'),('WAR_03','铁誓壁垒 · 贴身盾面 / 受击亮边'),('WAR_04','裂地审判 · 重劈地裂 / 碎石起落')]
def comparison(index):
 out=Image.new('RGB',(1280,740),'#171d22');d=ImageDraw.Draw(out)
 d.text((18,23),'战士技能分化 · 同一银白质感，不同动作与形态',font=font(25,True),fill='#e3ebf0',anchor='lm')
 for cell,(shot,label) in enumerate(specs):
  x=cell%2*640;y=48+cell//2*338;count=read(CACHE,shot)['frames'];i=(index+{'WAR_01':-10,'WAR_02':-6}.get(shot,0))%count
  with Image.open(CACHE/shot/f'{i:03d}.jpg') as im:out.paste(im.convert('RGB').resize((632,309),Image.Resampling.LANCZOS),(x+4,y+27))
  d.text((x+14,y+13),label,font=font(21,True),fill='#dce6ed',anchor='lm')
 d.text((18,725),'当前 3D 角色与实际技能时序 · 仅设计预览，尚未接入',font=font(18),fill='#aebfca',anchor='lm')
 return out
comparison(28).save(OUT/'skill-contrast.jpg',quality=95,subsampling=0)
frames=[comparison(i).resize((1024,592),Image.Resampling.LANCZOS) for i in range(0,108,2)]
durations=[(round((i+2)*100/30)-round(i*100/30))*10 for i in range(0,108,2)]
# Begin at each skill's active phase; preserve every frame and loop back naturally.
poster=14;frames=frames[poster:]+frames[:poster];durations=durations[poster:]+durations[:poster]
sampler=Image.new('RGB',(512,888))
for row,index in enumerate([0,18,36]):sampler.paste(frames[index].resize((512,296)),(0,row*296))
palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'skill-contrast.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,transparency=255,disposal=1)
(BASE/'review-checks.json').write_text(json.dumps({'status':'Mechanical and media checks passed; visual acceptance pending user review','productionIntegration':False,'checks':checks},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Verified eight distinct native captures and unchanged gameplay events.')
