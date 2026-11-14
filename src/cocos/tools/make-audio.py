"""Original local synthesized game cues. No downloaded/licensed recordings."""
from pathlib import Path
import math,random,struct,wave
ROOT=Path(__file__).resolve().parents[1]/'assets/resources/audio';ROOT.mkdir(parents=True,exist_ok=True)
SAMPLE=22050
def emit(name,duration,fn):
 rng=random.Random(name)
 with wave.open(str(ROOT/(name+'.wav')),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(SAMPLE)
  f.writeframes(b''.join(struct.pack('<h',int(max(-1,min(1,fn(i/SAMPLE,duration,rng)))*16000)) for i in range(int(duration*SAMPLE))))
emit('step',.13,lambda t,d,r:(r.random()*2-1)*math.exp(-t*45)*.25)
emit('sword',.25,lambda t,d,r:((r.random()*2-1)*.35+math.sin(2*math.pi*(240+1000*t)*t)*.16)*math.sin(math.pi*t/d)**2)
emit('hit',.18,lambda t,d,r:((r.random()*2-1)*.6+math.sin(2*math.pi*90*t)*.35)*math.exp(-t*28))
emit('arrow',.22,lambda t,d,r:(r.random()*2-1)*math.sin(math.pi*t/d)*math.exp(-t*12)*.5)
emit('spell',.45,lambda t,d,r:(math.sin(2*math.pi*(540+180*t)*t)+.4*math.sin(2*math.pi*880*t))*math.sin(math.pi*t/d)*.22)
emit('interact',.18,lambda t,d,r:(math.sin(2*math.pi*660*t)+math.sin(2*math.pi*990*t)*.25)*math.exp(-t*22)*.25)
emit('complete',1.4,lambda t,d,r:sum(math.sin(2*math.pi*f*t)*max(0,1-abs(t-c)/.5) for f,c in [(392,.18),(494,.44),(587,.7),(784,.94)])*.17)
# Wood-like impacts become farther apart as the die loses momentum.
impacts=[(.02,1),(.09,.86),(.18,.76),(.30,.64),(.46,.49),(.66,.35),(.88,.22)]
emit('dice',1.05,lambda t,d,r:sum(((r.random()*2-1)*.45+math.sin(2*math.pi*(190+i*31)*t)*.55)*math.exp(-(t-at)*65)*amp if at<=t<at+.09 else 0 for i,(at,amp) in enumerate(impacts))*.65)
# Chapter-two bells: original additive bronze partials, three separate strikes.
emit('bells',6.4,lambda t,d,r:sum(sum(math.sin(2*math.pi*196*ratio*(t-at))*math.exp(-(t-at)*decay)*gain for ratio,decay,gain in [(1,1.1,.20),(2.01,1.4,.12),(2.76,1.8,.08),(4.07,2.2,.05)])*min(1,(t-at)*130) if t>=at else 0 for at in [.05,1.65,3.25]))
print('Generated nine original local WAV cues, including the chapter-two bells.')

# Contact layers: original deterministic transients, body and short material tails.
def impact_body(kind):
 low=[0.]
 def sample(t,d,r):
  noise=r.random()*2-1;low[0]+=(noise-low[0])*.18
  attack=min(1,t/.0015);body=math.sin(2*math.pi*(115*t-100*t*t))*math.exp(-t*32)
  crack=(noise-low[0])*math.exp(-t*95);thud=low[0]*math.exp(-t*22)
  if kind=='armor':
   value=.52*crack+sum(math.sin(2*math.pi*f*t)*math.exp(-t*k)*g for f,k,g in [(1140,24,.22),(1870,36,.12),(2730,50,.08)])
  elif kind=='fire':value=.65*low[0]*math.exp(-t*17)+.28*body+.23*crack
  elif kind=='lightning':value=.45*crack+.25*math.sin(2*math.pi*(1700*t-2200*t*t))*math.exp(-t*45)+.28*body
  else:
   weight={'flesh':1,'heavy':1.35,'critical':1.2,'kill':1.45}[kind]
   value=weight*(.58*body+.5*thud)+.48*crack
   if kind in ['heavy','kill']:value+=.22*math.sin(2*math.pi*63*t)*math.exp(-t*18)
   if kind=='critical':value+=.28*(noise-low[0])*math.exp(-max(0,t-.012)*100) if t>.012 else 0
  return math.tanh(value*1.5)*attack*min(1,(d-t)/.015)
 return sample
for kind,duration in [('flesh',.18),('heavy',.23),('critical',.23),('armor',.22),('fire',.24),('lightning',.18),('kill',.27)]:emit('impact-'+kind,duration,impact_body(kind))
print('Generated seven original material/contact impact layers.')
