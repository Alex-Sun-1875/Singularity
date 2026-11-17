"""Export the existing-vs-revised native study with matching actors and events."""
from pathlib import Path
import json,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
BEFORE=ROOT/'src/.tmp/warrior-silver-cross-v12/final/design'
AFTER=ROOT/'src/.tmp/warrior-snowblade-v13/final/design'
OUT=BASE/'media';OUT.mkdir(exist_ok=True)
FONT=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
SHOTS=['BASIC_WAR','WAR_01','WAR_02','WAR_03','WAR_04','WAR_05','WAR_P1','WAR_P2']

def text(d,xy,s,size=23,fill='#e2e8ed',bold=False,anchor='lm'):
 font=ImageFont.truetype(str(FONT/('msyhbd.ttc' if bold else 'msyh.ttc')),size)
 d.text(xy,s,font=font,fill=fill,anchor=anchor)

checks={}
for shot in SHOTS:
 a=json.loads((BEFORE/shot/'capture.json').read_text(encoding='utf8'))
 b=json.loads((AFTER/shot/'capture.json').read_text(encoding='utf8'))
 check={'sameGameHash':a['gameHash']==b['gameHash'],'sameEvents':a['events']==b['events'],
  'sameTargets':a['info']['targets']==b['info']['targets'],'sameCamera':a['presentation']['camera']==b['presentation']['camera'],
  'sameFrames':a['frames']==b['frames'],'sameRules':all(a['info'].get(k)==b['info'].get(k) for k in ['original','geometry','skillGeometry','loadout']),
  'nativeSkeleton':bool(b['info']['player']['skeletons']),'noPageErrors':not b['errors'],
  'style':b['style']}
 assert all(check[k] for k in ['sameGameHash','sameEvents','sameTargets','sameCamera','sameFrames','sameRules','nativeSkeleton','noPageErrors']),shot
 assert b['style']['targetScreenCrossAngle']==72 and b['style']['opacityScale']==.78,shot
 assert b['style']['droppedLayers']==0,shot
 projected=[angle for sample in b['crossGeometrySamples'] for angle in sample['acuteAnglesDegrees']]
 assert all(abs(angle-72)<.02 for angle in projected),shot
 if projected:check['measuredScreenAcuteAngleRange']=[min(projected),max(projected)]
 if shot in ['WAR_01','WAR_02','WAR_04','WAR_05']:assert b['tripleWaveSamples'],shot
 separations=[]
 for sample in b['tripleWaveSamples']:
  for train in sample['trains']:
   assert [f['pulse'] for f in train['fronts']]==[0,1,2]
   positions=[np.array([f['position']['x'],f['position']['z']]) for f in train['fronts']]
   gaps=[float(np.linalg.norm(positions[i]-positions[i+1])) for i in [0,1]]
   assert min(gaps)>.12,'Wavefronts overlap at one position'
   assert float(np.dot(positions[0]-positions[1],positions[1]-positions[2]))>0,'Wavefront order reversed'
   separations.extend(gaps)
 check['threeFrontFrames']=[sample['frame'] for sample in b['tripleWaveSamples']]
 if separations:check['adjacentFrontSeparationRangeMetres']=[min(separations),max(separations)]
 checks[shot]=check

def frame(index):
 out=Image.new('RGB',(1440,712),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,27),'战士剑气 · 造型与节奏对照',28,bold=True)
 text(d,(1418,27),'0.5× 动作细节',19,'#adbfca',anchor='rm')
 text(d,(22,73),'上一版 · 银色三段冲击波',24,'#c4cbd0',True)
 text(d,(742,73),'本轮 · 亮刃前冲 / 气流拖尾',24,'#e3e8f0',True)
 for col,folder in enumerate([BEFORE/'WAR_01',AFTER/'WAR_01']):
  with Image.open(folder/f'{index:03d}.jpg') as im:
   out.paste(im.convert('RGB').crop((245,25,740,405)).resize((704,540),Image.Resampling.LANCZOS),(8+720*col,104))
 text(d,(22,679),'借鉴电视剧刀气的延长与流动感，三段分别突出横斩、纵劈和十字收尾。',22)
 return out

background=[]
for index in [14,18,22]:
 a=np.asarray(Image.open(BEFORE/'WAR_01'/f'{index:03d}.jpg').convert('RGB'))
 b=np.asarray(Image.open(AFTER/'WAR_01'/f'{index:03d}.jpg').convert('RGB'))
 delta=np.abs(a.astype(np.int16)-b.astype(np.int16))
 # Far-left scenery is outside every wave and character in this shot.
 assert np.array_equal(a[:,:210],b[:,:210]),'Fixed scenery changed'
 assert np.any(delta[:,350:740]),'No visual revision'
 background.append({'frame':index,'fixedSceneryIdentical':True,'effectRegionMeanDifference':float(delta[35:325,350:730].mean())})

frame(25).save(OUT/'design-comparison.jpg',quality=96,subsampling=0)
frames=[frame(i).resize((1008,498),Image.Resampling.LANCZOS) for i in range(72)]
duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(72)]
frames=frames[25:]+frames[:25];duration=duration[25:]+duration[:25]
sample=Image.new('RGB',(504,249*3))
for row,index in enumerate([0,24,48]):sample.paste(frames[index].resize((504,249)),(0,row*249))
palette=sample.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'design-comparison.gif',save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)
im=Image.open(OUT/'design-comparison.gif');milliseconds=0
for i in range(im.n_frames):im.seek(i);im.load();milliseconds+=im.info.get('duration',0)
assert milliseconds==4800
report={'method':'Same frozen native Cocos scene, deterministic reset, same skill events, targets, actors, camera and frame times; only design renderer and colour texture changed.',
 'comparison':{'before':'warrior-silver-cross-v12','after':'warrior-snowblade-v13','halfSpeed':True,'frames':im.n_frames,'milliseconds':milliseconds},
 'backgroundChecks':background,'shots':checks,'artAcceptance':'Pending user review','productionIntegration':False}
(BASE/'comparison-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'validatedShots':len(checks),'frames':im.n_frames,'milliseconds':milliseconds}))
