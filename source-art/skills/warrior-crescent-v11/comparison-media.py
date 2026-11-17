"""Export the existing-vs-revised native study with matching actors and events."""
from pathlib import Path
import json,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
BEFORE=ROOT/'src/.tmp/warrior-silvercyan-v10/final/design'
AFTER=ROOT/'src/.tmp/warrior-crescent-v11/final/design'
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
 assert b['style']['targetScreenCrossAngle']==24 and b['style']['opacityScale']==.55,shot
 projected=[angle for sample in b['crossGeometrySamples'] for angle in sample['acuteAnglesDegrees']]
 assert all(abs(angle-24)<.02 for angle in projected),shot
 if projected:check['measuredScreenAcuteAngleRange']=[min(projected),max(projected)]
 checks[shot]=check

def frame(index):
 out=Image.new('RGB',(1440,712),'#171d22');d=ImageDraw.Draw(out)
 text(d,(22,27),'战士剑气 · 同动作对照',28,bold=True)
 text(d,(1418,27),'0.5× 动作细节',19,'#adbfca',anchor='rm')
 text(d,(22,73),'上一版 · 卷曲波面',24,'#c4cbd0',True)
 text(d,(742,73),'本轮 · 尖端月牙 / 收紧交叉',24,'#bde8ed',True)
 for col,folder in enumerate([BEFORE/'WAR_01',AFTER/'WAR_01']):
  with Image.open(folder/f'{index:03d}.jpg') as im:
   out.paste(im.convert('RGB').crop((350,10,730,305)).resize((704,540),Image.Resampling.LANCZOS),(8+720*col,104))
 text(d,(22,679),'中段宽、两端尖、内侧凹入；保留透明感，交叉开口按实际画面检查。',22)
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

frame(18).save(OUT/'design-comparison.jpg',quality=96,subsampling=0)
frames=[frame(i).resize((1008,498),Image.Resampling.LANCZOS) for i in range(72)]
duration=[(round((i+1)*100/15)-round(i*100/15))*10 for i in range(72)]
frames=frames[18:]+frames[:18];duration=duration[18:]+duration[:18]
sample=Image.new('RGB',(504,249*3))
for row,index in enumerate([0,24,48]):sample.paste(frames[index].resize((504,249)),(0,row*249))
palette=sample.quantize(255,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
indexed[0].save(OUT/'design-comparison.gif',save_all=True,append_images=indexed[1:],duration=duration,loop=0,optimize=True,transparency=255,disposal=1)
im=Image.open(OUT/'design-comparison.gif');milliseconds=0
for i in range(im.n_frames):im.seek(i);im.load();milliseconds+=im.info.get('duration',0)
assert milliseconds==4800
report={'method':'Same frozen native Cocos scene, deterministic reset, same skill events, targets, actors, camera and frame times; only design renderer and colour texture changed.',
 'comparison':{'before':'warrior-silvercyan-v10','after':'warrior-crescent-v11','halfSpeed':True,'frames':im.n_frames,'milliseconds':milliseconds},
 'backgroundChecks':background,'shots':checks,'artAcceptance':'Pending user review','productionIntegration':False}
(BASE/'comparison-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'validatedShots':len(checks),'frames':im.n_frames,'milliseconds':milliseconds}))
