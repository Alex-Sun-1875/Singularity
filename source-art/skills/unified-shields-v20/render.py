"""Composite one shared shield with four motif/color skins over native game pixels.

This is a deterministic design animatic, not a Cocos runtime implementation.
"""
from pathlib import Path
from functools import lru_cache
import json,hashlib,importlib.util
from PIL import Image,ImageDraw,ImageFilter,ImageOps
import numpy as np
import av

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ASSETS=HERE/'assets';ASSETS.mkdir(exist_ok=True)
MEDIA=HERE/'media';MEDIA.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('fire_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
DESIGN=json.loads((HERE/'design.json').read_text(encoding='utf8'))
FAMILIES=['WAR','BOW','FIR','THU']
MOTIFS={'WAR':'银金 · 刃纹','BOW':'青绿 · 风纹','FIR':'橙金 · 焰纹','THU':'蓝紫 · 雷纹'}
BG=Image.open(HERE/'inputs/native-player-crop.png').convert('RGBA')
W,H=512,576
yy,xx=np.mgrid[:H,:W]
X=(xx-(W-1)/2)/(W*.47);Y=(yy-(H-1)/2)/(H*.48)
R=np.sqrt(X*X+Y*Y)
SMOOTH=lambda x:np.clip(x,0,1)**2*(3-2*np.clip(x,0,1))
INSIDE=1-SMOOTH((R-.97)/.035)
PALETTE={key:np.array(tuple(bytes.fromhex(DESIGN['variants'][key]['color'][1:])),dtype=np.float32)/255 for key in FAMILIES}

def raw_shell():
 im=Image.open(HERE/'raw/shared-shell-v2.png').convert('RGBA')
 a=np.asarray(im)[:,:,3]
 rows,cols=np.where(a>24)
 bbox=(max(0,int(cols.min())-16),max(0,int(rows.min())-16),min(im.width,int(cols.max())+17),min(im.height,int(rows.max())+17))
 im=im.crop(bbox).resize((W,H),Image.Resampling.LANCZOS)
 arr=np.asarray(im,dtype=np.float32)/255
 # Same matte in every profession. The field keeps the actor visible and the
 # generated highlight texture, while softly clipping exterior alpha noise.
 alpha=arr[:,:,3]*.64*INSIDE
 alpha=np.maximum(alpha,.035*(1-SMOOTH((R-.85)/.13))*INSIDE)
 luma=arr[:,:,:3].max(axis=2)
 return luma,alpha,bbox

LUMA,SHELL_ALPHA,SOURCE_BOX=raw_shell()

def normalized_motif(family):
 source=Image.open(HERE.parent/'reference-seals-v3/assets'/f'{family}.png').convert('RGBA')
 pixels=np.asarray(source,dtype=np.float32)/255
 # Retain only the interior profession linework. Remove the old double ground
 # circles, center emblem, and straight cardinal spokes before curved mapping.
 py,px=np.mgrid[:source.height,:source.width]
 sx=(px-512)/460;sy=(py-512)/460;sr=np.sqrt(sx*sx+sy*sy)
 keep=SMOOTH((sr-.22)/.07)*(1-SMOOTH((sr-.79)/.035))
 keep*=SMOOTH((np.minimum(np.abs(sx),np.abs(sy))-.035)/.035)
 alpha=pixels[:,:,3]*keep
 mask=Image.fromarray(np.uint8(np.clip(alpha*255,0,255))).filter(ImageFilter.MaxFilter(7))
 # Front hemisphere projection; linework follows the curved volume. At the
 # center it stays sparse so head, weapon, hands and body remain readable.
 z=np.sqrt(np.maximum(0,1-X*X-Y*Y))
 u=(np.arctan2(X,np.maximum(z,.001))/np.pi+.5)*(mask.width-1)
 v=(np.arcsin(np.clip(Y,-1,1))/np.pi+.5)*(mask.height-1)
 src=np.asarray(mask,dtype=np.float32)/255
 x0=np.clip(u.astype(int),0,mask.width-2);y0=np.clip(v.astype(int),0,mask.height-2)
 dx=u-x0;dy=v-y0
 sample=src[y0,x0]*(1-dx)*(1-dy)+src[y0,x0+1]*dx*(1-dy)+src[y0+1,x0]*(1-dx)*dy+src[y0+1,x0+1]*dx*dy
 density=SMOOTH((np.abs(X)-.22)/.20)
 mask=sample*INSIDE*density*(1-SMOOTH((R-.94)/.045))*.75
 return np.clip(mask,0,1)

PATTERNS={family:normalized_motif(family) for family in FAMILIES}

def rgba(rgb,alpha):
 a=np.empty((H,W,4),dtype=np.uint8)
 a[:,:,:3]=np.uint8(np.clip(rgb,0,1)*255)
 a[:,:,3]=np.uint8(np.clip(alpha,0,1)*255)
 return Image.fromarray(a,'RGBA')

def state(t,break_demo=False):
 age=t-.30
 form=float(SMOOTH(age/.32))
 end=4.25 if not break_demo else 2.85
 duration=.48 if not break_demo else .28
 decay=float(1-SMOOTH((t-end)/duration))
 return age,form,decay,end

@lru_cache(maxsize=32)
def shield(family,frame,break_demo=False):
 t=frame/30;age,form,decay,end=state(t,break_demo)
 if age<=0 or decay<=0:return Image.new('RGBA',(W,H))
 color=PALETTE[family]
 breath=1+.045*np.sin((t-.62)*2*np.pi/1.6)
 # The same upward reveal and common moving soft sheen for all four skins.
 reveal=SMOOTH((Y-(1-form*2.15))/.14)
 front=np.exp(-((Y-(1-form*2.15))/.04)**2)*(.5 if form<1 else 0)
 alpha=(SHELL_ALPHA*breath+front*.14*INSIDE)*reveal*decay
 sheen=np.exp(-((Y-(.8-((t-.62)*.25)%1.6))/.11)**2)*.035*INSIDE
 alpha=np.clip(alpha+sheen*reveal*decay,0,1)
 rgb=color[None,None,:]*(.83+.17*LUMA[:,:,None])
 rgb+=.20*LUMA[:,:,None]
 shell=rgba(rgb,alpha)
 # Shared placement, width treatment and visibility budget; only the input
 # motif alpha and hue differ. No fire/lightning emitters are introduced.
 pattern_decay=float(1-SMOOTH((t-end)/.35))
 pattern_alpha=PATTERNS[family]*reveal*pattern_decay*breath
 pattern_rgb=np.minimum(1,color*.80+.20)
 layer=rgba(pattern_rgb,pattern_alpha)
 glow=layer.copy();glow.putalpha(layer.getchannel('A').filter(ImageFilter.GaussianBlur(3)).point(lambda x:round(x*.40)))
 shell=Image.alpha_composite(glow,shell)
 shell=Image.alpha_composite(shell,layer)
 # A deliberately staged local shield contact. It is illustrative, not a
 # recording of an actual enemy hit or a new damage/attack event.
 hit_age=t-2.05
 if 0<=hit_age<.22:
  radius=.035+hit_age/.22*.29
  distance=np.sqrt((X-.66)**2+((Y+.12)*1.08)**2)
  ring=np.exp(-((distance-radius)/.015)**2)*(1-hit_age/.22)*.8*INSIDE
  flash=np.exp(-(distance/.12)**2)*(.55*(1-hit_age/.22))*INSIDE
  shell=Image.alpha_composite(shell,rgba(np.minimum(1,color*.5+.5),np.clip(ring+flash,0,.85)))
 if break_demo and t>end:
  # Common dissolve breakup only; no burst outside the protected volume.
  pixels=np.asarray(shell).copy();noise=(np.sin(X*63+Y*17)*np.sin(Y*79-X*27)*.5+.5)
  pixels[:,:,3]=np.uint8(pixels[:,:,3]*SMOOTH((noise-(t-end)/.28)/.18));shell=Image.fromarray(pixels)
 return shell

def scene(family,frame=36,break_demo=False):
 out=BG.copy()
 # Same screen anchors for every skin. Top above head, lower shell surrounds
 # feet; it does not become a projected ground magic circle.
 item=shield(family,frame,break_demo).resize((208,234),Image.Resampling.LANCZOS)
 out.alpha_composite(item,(88,82))
 return out.convert('RGB')

def phase(frame,break_demo=False):
 t=frame/30
 if t<.3:return '准备'
 if t<.62:return '由下向上成形'
 if 2.05<=t<2.27:return '局部受击波纹'
 if break_demo and 2.85<=t<3.13:return '击破 · 碎光淡出'
 if not break_demo and 4.25<=t<4.73:return '纹样退亮 · 护罩渐隐'
 if t>=(3.13 if break_demo else 4.73):return '消散完成'
 return '稳定维持 · 轻微呼吸'

def four(frame):
 out=Image.new('RGB',(1240,1278),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,35),'统一护盾 · 四系同一套效果',33,'#e7bc7d',True)
 base.text(d,(20,79),'轮廓、透明度、动效一致；仅颜色和纹样不同',22,'#bfb2a1')
 for n,family in enumerate(FAMILIES):
  x=18+n%2*612;y=116+n//2*564
  base.text(d,(x+10,y+22),DESIGN['variants'][family]['name']+'  |  '+MOTIFS[family],24,DESIGN['variants'][family]['color'],True)
  out.paste(scene(family,frame).resize((600,520),Image.Resampling.LANCZOS),(x,y+45))
  d.rectangle((x,y,x+600,y+565),outline='#655039')
 base.text(d,(22,1260),phase(frame)+'　/　合成动画设计预览，尚未接入',20,'#e7bc7d')
 base.text(d,(1218,1260),f'{frame/30:.1f}s',20,'#bfb2a1',anchor='rm')
 return out

def board():
 out=Image.new('RGB',(1480,1730),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(25,43),'统一护盾 · 四系花纹与配色稿',40,'#e7bc7d',True)
 base.text(d,(25,88),'相同立体护罩、相同尺寸与动画；只替换花纹和颜色',24,'#bfb2a1')
 for n,family in enumerate(FAMILIES):
  x=25+n%2*728;y=122+n//2*596
  base.text(d,(x+12,y+25),DESIGN['variants'][family]['name']+'  |  '+MOTIFS[family],27,DESIGN['variants'][family]['color'],True)
  out.paste(scene(family,36).resize((700,525),Image.Resampling.LANCZOS),(x,y+48))
  base.text(d,(x+12,y+580),'半透明全身护罩 · 共同轮廓与材质',18,'#c8bdaf')
  d.rectangle((x,y,x+700,y+595),outline='#655039')
 y=1346;base.text(d,(25,y),'共同动画节奏',26,'#e7bc7d',True)
 stages=[(14,'0.32s 成形'),(36,'稳定维持'),(64,'局部受击'),(133,'逐渐淡出'),(148,'消散完成')]
 for n,(frame,title) in enumerate(stages):
  x=25+n*289
  crop=scene('FIR',frame).crop((60,62,310,330)).resize((264,250),Image.Resampling.LANCZOS)
  out.paste(crop,(x,y+34));base.text(d,(x+5,y+306),title,21,'#dfcfb8')
 base.text(d,(25,1697),'设计候选 · 尚未接入　|　沿用现有 3D 角色作材质对比；不增加职业技能',20,'#bfb2a1')
 out.save(MEDIA/'unified-shields-design.jpg',quality=95,subsampling=0)

def main():
 for family in FAMILIES:
  shield(family,36).save(ASSETS/(family+'-shield.png'))
  Image.fromarray(np.uint8(PATTERNS[family]*255)).save(ASSETS/(family+'-motif-alpha.png'))
  scene(family,36).save(MEDIA/(family+'-shield-scene.jpg'),quality=95)
 board();print('Saved shield board',flush=True)
 frames=165
 base.video(MEDIA/'unified-shields-motion.mp4',(four(i) for i in range(frames)),(1240,1278))
 base.video(MEDIA/'shield-break-study.mp4',(four_break(i) for i in range(114)),(960,720))
 # Short lighter animated preview, retaining the same full motion timing.
 base.preview([four(round(i*1.5)).resize((720,742),Image.Resampling.LANCZOS) for i in range(frames*2//3)],MEDIA/'unified-shields-motion.gif',width=720)
 checks={
  'generationTool':'cloud OpenAI image_gen; shared shell v2',
  'generationStatus':'Two cloud outputs saved; v1 rejected as too broad an annular band, v2 used as a transparent shared material source.',
  'artAcceptance':'Candidate only; user review pending',
  'sameGeometry':True,'sameRimAndMembraneAlpha':True,'sameTimings':True,
  'differencesOnly':['motif line shape','profession color'],
  'sourceShellCrop':SOURCE_BOX,'screenShellBounds':[88,82,296,316],
  'commonCenterAlpha':float(SHELL_ALPHA[H//2,W//2]),
  'patternAlphaMax':{f:float(PATTERNS[f].max()) for f in FAMILIES},
  'mainMovie':{'frames':frames,'fps':30,'durationSeconds':frames/30},
  'commonHitRippleIsIllustrative':True,'productionIntegration':False,
  'sources':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'inputs/native-player-crop.png',HERE/'raw/shared-shell-v2.png']+[HERE.parent/'reference-seals-v3/assets'/f'{f}.png' for f in FAMILIES]}
 }
 with av.open(str(MEDIA/'unified-shields-motion.mp4')) as movie:
  v=movie.streams.video[0];assert v.frames==frames and float(v.average_rate)==30
  checks['mainMovie']['encodedFrames']=v.frames
 with Image.open(MEDIA/'unified-shields-motion.gif') as gif:
  duration=0
  for i in range(gif.n_frames):gif.seek(i);duration+=gif.info.get('duration',0)
  assert duration==5500
  checks['gifDurationMilliseconds']=duration
 (HERE/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(checks,ensure_ascii=False),flush=True)

def four_break(frame):
 out=Image.new('RGB',(960,720),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(20,32),'护盾击破 · 共用反馈示意',30,'#e7bc7d',True)
 out.paste(scene('FIR',frame,True).resize((675,585),Image.Resampling.LANCZOS),(142,65))
 base.text(d,(20,676),phase(frame,True)+'　/　各系仅替换颜色与纹样',21,'#dfcfb8')
 base.text(d,(20,708),'合成设计动画 · 并非实际受击录屏 · 尚未接入',17,'#bfb2a1')
 return out

if __name__=='__main__':
 if '--still' in __import__('sys').argv:
  board();print('Saved still board',flush=True)
 else:main()
