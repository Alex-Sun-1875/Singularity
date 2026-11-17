"""Compare the selected reference and mark the measured 120-degree screen crossing."""
from pathlib import Path
import json,hashlib,math,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
OLD=BASE.parent/'warrior-aura-v9'
BEFORE=ROOT/'src/.tmp/warrior-aura-v9/opacity-before/WAR_01'
AFTER=ROOT/'src/.tmp/warrior-reference120-v14/final/design'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
SHOTS=['BASIC_WAR','WAR_01','WAR_02','WAR_03','WAR_04','WAR_05','WAR_P1','WAR_P2']
FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
def font(size,bold=False):return ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
def text(d,xy,s,size=23,fill='#e2e8ed',bold=False,anchor='lm'):
 d.text(xy,s,font=font(size,bold),fill=fill,anchor=anchor)
def read(shot):return json.loads((AFTER/shot/'capture.json').read_text(encoding='utf8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mesh_source(path):
 code=path.read_text(encoding='utf8').replace('\r\n','\n')
 return code[code.index(' private pressureMesh('):code.index(' private wave(')]
assert mesh_source(BASE/'WarriorKitStudy.ts')==mesh_source(OLD/'WarriorKitStudy.ts'),'Reference mesh or vertex profile changed'
assert sha(BASE/'blade.png')==sha(OLD/'blade.png') and sha(BASE/'guard.png')==sha(OLD/'guard.png')
rgba=np.asarray(Image.open(BASE/'blade.png').convert('RGBA'))
assert np.all(rgba[:rgba.shape[0]*2//3,:,3]==255),'Core texture contains transparency'
checks={}
for shot in SHOTS:
 before=json.loads((ROOT/'src/.tmp/warrior-aura-v9/final/design'/shot/'capture.json').read_text(encoding='utf8'))
 after=read(shot)
 check={'sameGameHash':before['gameHash']==after['gameHash'],'sameCombatEvents':before['events']==after['events'],
  'sameTargets':before['info']['targets']==after['info']['targets'],'sameCamera':before['presentation']['camera']==after['presentation']['camera'],
  'sameFrames':before['frames']==after['frames'],'nativeSkeleton':bool(after['info']['player']['skeletons']),'noPageErrors':not after['errors']}
 assert all(check.values()),shot
 obtuse=[c['obtuse'] for s in after['crossGeometrySamples'] for c in s['crossings']]
 assert all(abs(angle-120)<.02 for angle in obtuse),shot
 if obtuse:check['measuredObtuseAngleRange']=[min(obtuse),max(obtuse)]
 opaque=[s['frame'] for s in after['crossGeometrySamples'] if any(c['h']['materialOpacity']==1 and c['v']['materialOpacity']==1 for c in s['crossings'])]
 if shot in ['WAR_01','WAR_02','WAR_05']:assert opaque,shot
 check['opaqueCrossFrames']=opaque
 for name,value in after['reviewInputs'].items():assert sha(BASE/name)==value,'Capture source changed: '+name
 checks[shot]=check

def comparison(index):
 out=Image.new('RGB',(1440,712),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,27),'以所选原稿为基础 · 同帧对照',28,bold=True)
 text(d,(1418,27),'0.5× 动作细节',19,'#adbfca',anchor='rm')
 text(d,(22,73),'所选原稿 · 较实的波前',24,'#c4cbd0',True)
 text(d,(742,73),'本轮 · 亮刃不透明 / 120°交叉',24,'#e2e8ef',True)
 for col,folder in enumerate([BEFORE,AFTER/'WAR_01']):
  with Image.open(folder/f'{index:03d}.jpg') as im:
   out.paste(im.convert('RGB').crop((400,40,730,295)).resize((704,540),Image.Resampling.LANCZOS),(8+720*col,104))
 text(d,(22,679),'沿用原稿波前造型与银白配色，取消整层半透明折减，交叉钝角改为 120°。',21)
 return out

for index in [14,18,22]:
 a=np.asarray(Image.open(BEFORE/f'{index:03d}.jpg').convert('RGB'))
 b=np.asarray(Image.open(AFTER/'WAR_01'/f'{index:03d}.jpg').convert('RGB'))
 assert np.array_equal(a[:,:210],b[:,:210]),'Fixed scenery changed'
comparison(18).save(OUT/'design-comparison.jpg',quality=96,subsampling=0)
frames=[comparison(i).resize((1008,498),Image.Resampling.LANCZOS) for i in range(72)]
durations=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(72)]
frames=frames[18:]+frames[:18];durations=durations[18:]+durations[:18]
sampler=Image.new('RGB',(504,747))
for row,index in enumerate([0,24,48]):sampler.paste(frames[index].resize((504,249)),(0,row*249))
palette=sampler.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'design-comparison.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,optimize=True,transparency=255,disposal=1)
im=Image.open(OUT/'design-comparison.gif');milliseconds=0
for i in range(im.n_frames):im.seek(i);im.load();milliseconds+=im.info.get('duration',0)
assert milliseconds==4800

sample=next(s for s in read('WAR_01')['crossGeometrySamples'] if s['frame']==18)
cross=next(c for c in sample['crossings'] if c['h']['materialOpacity']==1 and c['v']['materialOpacity']==1)
h,v=cross['h'],cross['v'];height=read('WAR_01')['info']['canvas'][1]
ph=np.array([h['projectedOrigin']['x'],height-h['projectedOrigin']['y']])
pv=np.array([v['projectedOrigin']['x'],height-v['projectedOrigin']['y']])
ah=-math.radians(h['screenAxisDegrees']);av=-math.radians(v['screenAxisDegrees'])
dh=np.array([math.cos(ah),math.sin(ah)]);dv=np.array([math.cos(av),math.sin(av)])
t,s=np.linalg.solve(np.column_stack([dh,-dv]),pv-ph);origin=ph+t*dh
# Choose the two directed rays that bound the obtuse opening of the crossing.
a1=ah;a2=av+math.pi;delta=(a2-a1+math.pi)%(2*math.pi)-math.pi
assert abs(abs(math.degrees(delta))-120)<.02
picture=Image.open(AFTER/'WAR_01/018.jpg').convert('RGB');d=ImageDraw.Draw(picture)
gold='#edbd6c'
for angle in [a1,a2]:
 direction=np.array([math.cos(angle),math.sin(angle)]);tip=origin+direction*104
 d.line([tuple(origin),tuple(tip)],fill='#171d22',width=5);d.line([tuple(origin),tuple(tip)],fill=gold,width=2)
 left=tip-direction*10+np.array([-direction[1],direction[0]])*4
 right=tip-direction*10-np.array([-direction[1],direction[0]])*4
 d.polygon([tuple(tip),tuple(left),tuple(right)],fill=gold)
points=[tuple(origin+np.array([math.cos(a1+delta*x),math.sin(a1+delta*x)])*43) for x in np.linspace(0,1,41)]
d.line(points,fill='#171d22',width=5);d.line(points,fill=gold,width=2)
label=origin+np.array([math.cos(a1+delta/2),math.sin(a1+delta/2)])*73
d.text(tuple(label),'120°',font=font(25,True),fill=gold,anchor='mm',stroke_width=2,stroke_fill='#171d22')
d.ellipse((origin[0]-3,origin[1]-3,origin[0]+3,origin[1]+3),fill=gold)
board=Image.new('RGB',(1440,806),'#171d22');d=ImageDraw.Draw(board)
text(d,(22,28),'交叉角核对 · 120°',30,bold=True)
board.paste(picture.resize((1392,682),Image.Resampling.LANCZOS),(24,56))
text(d,(22,775),'交叉钝角 120° · 对应锐角 60° · 标注依据为实际波面长轴的相机投影。',23)
board.save(OUT/'angle-check.jpg',quality=96,subsampling=0)

report={'base':'User-uploaded v9 comparison image; denser reference side used for the comparison',
 'userReferenceSha256':sha(BASE/'user-reference.jpg'),'sameReferenceMeshAndVertexProfile':True,'sameReferenceTextureHashes':True,
 'coreTextureAlpha':255,'fixedSceneryIdentical':True,'gif':{'frames':im.n_frames,'milliseconds':milliseconds},
 'annotatedFrame':18,'annotatedObtuseDegrees':abs(math.degrees(delta)),'annotationOriginNativePixels':origin.tolist(),
 'shots':checks,'artAcceptance':'Pending user review','productionIntegration':False}
(BASE/'comparison-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'validatedShots':len(checks),'obtuseAngleDegrees':abs(math.degrees(delta)),'gifFrames':im.n_frames}))
