"""Assemble current fire review artifacts; keep selected jet pixels authoritative."""
from pathlib import Path
from fractions import Fraction
import importlib.util,json,hashlib,sys
from functools import lru_cache
from PIL import Image,ImageDraw,ImageOps
import av

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MEDIA=HERE/'media'
MEDIA.mkdir(exist_ok=True)
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
v7=module('fire_v7',HERE.parent/'fire-kit-revision-v7/media.py')
base=v7.base
SELECTED=HERE.parent/'fire-selected-reference-v18/user-selected-effect.jpg'
V5=ROOT/'src/.tmp/fire-spells-design-v5/final/design/FIR_01'
SHIELD=ROOT/'src/.tmp/fire-kit-showcase-v19/current/FIR_03'
ORDER=['FIR_01','FIR_04','FIR_05','FIR_03','FIR_02']
DATA={
 'FIR_01':dict(name='赤焰枪',role='单体飞行弹',status='设计预览',frames=126,
   lines=['尖锐火核向前飞行，尾焰跟随弹道。','命中后短促爆开，残焰逐渐退去。']),
 'FIR_04':dict(name='烈焰喷流',role='前方一列地面喷焰',status='已选定静态造型',frames=120,
   lines=['五个小法阵沿前方排成一列，火焰竖直向上。','高度、颜色和通透感，保留你刚选定的效果。']),
 'FIR_05':dict(name='焚焰火域',role='火墙与火海合并方案',status='设计预览',frames=210,
   lines=['火浪展开，形成有纵深的持续燃烧区域。','结束后火势回落，再以低位残焰缓慢消散。']),
 'FIR_03':dict(name='焰心护盾',role='自身防护',status='现有实现',frames=162,
   lines=['贴近角色的护盾光焰，保持人物轮廓清楚。','展示当前护盾效果；此技能尚未另行改稿。']),
 'FIR_02':dict(name='焚星坠落',role='终极技能 · 陨石',status='设计预览',frames=195,
   lines=['双层纹样法阵预告范围，陨石下压后持续爆燃。','范围扩大；主爆燃约 1.2 秒，地面余焰渐退。']),
}
COLORS={'bg':'#171513','panel':'#231f1b','gold':'#e8b976','text':'#eee5d8','muted':'#b5aa9c','line':'#6c5236'}

@lru_cache(maxsize=1)
def jet():return Image.open(SELECTED).convert('RGB').resize((960,470),Image.Resampling.LANCZOS)
def scene(skill,index):
 if skill=='FIR_04':return jet().copy()
 if skill in ['FIR_05','FIR_02']:return v7.scene('design',skill,index)
 return Image.open((V5 if skill=='FIR_01' else SHIELD)/f'{index:03}.jpg').convert('RGB')

def phase(skill,index):
 t=index/30
 if skill=='FIR_04':return '选定效果图 · 静态参考，动态尚未制作'
 if skill in ['FIR_05','FIR_02']:return v7.phase(skill,index)
 if skill=='FIR_01':return base.phase(skill,index)
 return '准备施放' if t<.3 else '护盾形成' if t<.8 else '护盾维持' if t<4.45 else '护盾结束'

def framed(skill,index):
 data=DATA[skill];out=Image.new('RGB',(960,634),COLORS['bg']);d=ImageDraw.Draw(out)
 base.text(d,(22,28),data['name'],27,COLORS['gold'],True)
 base.text(d,(938,29),data['status'],16,COLORS['muted'],anchor='rm')
 out.paste(scene(skill,index),(0,58))
 d.line((22,543,938,543),fill=COLORS['line'])
 base.text(d,(22,564),phase(skill,index),18,COLORS['gold'])
 base.text(d,(938,565),f'{ORDER.index(skill)+1}/5',16,COLORS['muted'],anchor='rm')
 base.text(d,(22,594),data['lines'][0],16,COLORS['text'])
 base.text(d,(22,620),'火系效果总览 · 审阅素材 · 尚未接入正式技能',14,COLORS['muted'])
 return out

def contact():
 picks=[('FIR_01',i) for i in [18,21,24]]+[('FIR_05',i) for i in [30,45,75]]+[('FIR_02',i) for i in [28,36,48]]
 if SHIELD.exists():picks += [('FIR_03',i) for i in [21,45,90]]
 out=Image.new('RGB',(1440,265*((len(picks)+2)//3)),COLORS['bg'])
 for n,(skill,i) in enumerate(picks):
  im=scene(skill,i).resize((480,235));x=n%3*480;y=n//3*265
  out.paste(im,(x,y+30));base.text(ImageDraw.Draw(out),(x+8,y+15),skill+' / '+str(i),16)
 out.save(MEDIA/'contact.jpg',quality=90)
 print('Contact:',MEDIA/'contact.jpg',flush=True)

def card(skill,index):
 out=Image.new('RGB',(960,622),COLORS['panel']);d=ImageDraw.Draw(out);data=DATA[skill]
 base.text(d,(22,30),f'{ORDER.index(skill)+1:02}  '+data['name'],27,COLORS['gold'],True)
 base.text(d,(938,31),data['status'],16,COLORS['muted'],anchor='rm')
 out.paste(scene(skill,index),(0,60))
 base.text(d,(22,554),data['role'],20,COLORS['gold'],True)
 for n,line in enumerate(data['lines']):base.text(d,(22,585+n*25),line,17,COLORS['text'])
 d.rectangle((0,0,959,621),outline=COLORS['line'],width=1)
 return out

def passive_card():
 out=Image.new('RGB',(960,622),COLORS['panel']);d=ImageDraw.Draw(out)
 base.text(d,(28,34),'被动效果 · 随战斗触发',27,COLORS['gold'],True)
 d.line((28,68,932,68),fill=COLORS['line'])
 base.text(d,(36,119),'余烬掌握',27,COLORS['text'],True)
 base.text(d,(36,165),'延长敌人身上的燃烧；以低位短焰和余烬表现。',20,COLORS['muted'])
 base.text(d,(36,249),'薪火余辉',27,COLORS['text'],True)
 base.text(d,(36,295),'群攻火技能直接击败敌人后，向附近敌人传播燃烧。',20,COLORS['muted'])
 base.text(d,(36,331),'赤焰枪不触发这种传播。',19,COLORS['muted'])
 d.line((28,387,932,387),fill=COLORS['line'])
 base.text(d,(36,431),'当前整理规则',22,COLORS['gold'],True)
 for i,line in enumerate(['火墙、火海只保留合并后的一个火域。','烈焰喷流原样引用最新选定图，未制作动态。','陨石放在最后，作为火系终极技能。','被动无独立施放镜头；完整合并规则与数值待定。']):
  base.text(d,(36,477+i*33),line,20,COLORS['text'])
 d.rectangle((0,0,959,621),outline=COLORS['line'],width=1)
 return out

def render():
 for skill,folder in [('FIR_01',V5),('FIR_03',SHIELD),('FIR_05',v7.CACHE/'design/FIR_05'),('FIR_02',v7.CACHE/'design/FIR_02')]:
  report=json.loads((folder/'capture.json').read_text(encoding='utf8'))
  assert not report['errors'] and len(list(folder.glob('*.jpg')))==DATA[skill]['frames'],skill
 selected_hash=hashlib.sha256(SELECTED.read_bytes()).hexdigest()
 assert selected_hash=='52b78fa21809693c830796ed479eb42acb545258f19286c0ff80f1d4acc20b36'
 picks={'FIR_01':18,'FIR_04':0,'FIR_05':45,'FIR_03':45,'FIR_02':28}
 board=Image.new('RGB',(1976,2090),COLORS['bg']);d=ImageDraw.Draw(board)
 base.text(d,(28,45),'火系技能效果 · 当前方案总览',42,COLORS['gold'],True)
 base.text(d,(28,94),'4 个主动技能 + 1 个终极技能　/　选定稿、候选效果与现有护盾分别标注',23,COLORS['muted'])
 for n,skill in enumerate(ORDER):board.paste(card(skill,picks[skill]),(20+n%2*976,132+n//2*638))
 board.paste(passive_card(),(996,1408))
 base.text(d,(28,2061),'设计审阅素材 · 并非正式接入结果　|　喷流以用户最新选定图片为准',21,COLORS['muted'])
 board.save(MEDIA/'fire-skills-overview.jpg',quality=95,subsampling=0)
 for skill in ORDER:
  frame=framed(skill,picks[skill]);frame.save(MEDIA/(skill+'-effect.jpg'),quality=93)
 chapters=[];start=0
 for n,skill in enumerate(ORDER):
  end=start+DATA[skill]['frames']
  chapters.append(dict(id=n,time_base=Fraction(1,30),start=start,end=end,metadata={'title':DATA[skill]['name']+('（静态选定稿）' if skill=='FIR_04' else '')}));start=end
 base.video(MEDIA/'fire-skills-preview.mp4',(framed(s,i) for s in ORDER for i in range(DATA[s]['frames'])),(960,634),chapters)
 for skill in ['FIR_01','FIR_05','FIR_03','FIR_02']:
  base.video(MEDIA/(skill+'-motion.mp4'),(framed(skill,i) for i in range(DATA[skill]['frames'])),(960,634))
 verification={
  'selectedJetSourceSha256':selected_hash,'selectedJetProcessing':'Only proportional downscaling for layout; no regeneration, recoloring, flame reshaping, or fake motion.',
  'expectedVideoFrames':start,'expectedDurationSeconds':start/30,'jetChapterIsStatic':True,
  'productionFilesModified':False,'shieldSource':'Existing cached native Cocos Web build; not newly redesigned.',
  'candidateArt':['FIR_01','FIR_05','FIR_02'],'selectedStillArt':['FIR_04'],'currentImplementation':['FIR_03'],
  'passives':'Descriptions from PureSkills; no staged activation footage claimed.'
 }
 with av.open(str(MEDIA/'fire-skills-preview.mp4')) as clip:
  stream=clip.streams.video[0];verification['video']={'frames':stream.frames,'fps':float(stream.average_rate),'width':stream.width,'height':stream.height,'durationSeconds':float(clip.duration)/av.time_base}
  assert stream.frames==start and float(stream.average_rate)==30
 (HERE/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(verification,ensure_ascii=False),flush=True)

if __name__=='__main__':contact() if '--contact' in sys.argv else render()
