"""Blend the V8 recorded steel front with V7 low-mid weight using existing tools."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from scipy import signal

ROOT=Path(__file__).resolve().parents[4]
PROJECT=ROOT/'src/cocos'
OUT=ROOT/'source-art/audio/impact-fusion-v9'
V7=PROJECT/'assets/resources/audio/combat-v7'
V8=PROJECT/'assets/resources/audio/combat-v8'
RUNTIME=PROJECT/'assets/resources/audio/combat-v9'
RATE=44100
RATIOS={'war_slash':.55,'war_armor':.60,'war_finish':.65,
        'bow_pierce':.40,'bow_heavy':.45,'bow_armor':.43}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,value):
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
 path=Path(__file__).resolve().parents[1]/'audio-impact-v8/make_wuxia_contacts.py'
 spec=importlib.util.spec_from_file_location('_fusion_v8_tools',path)
 tool=importlib.util.module_from_spec(spec);sys.modules[spec.name]=tool;spec.loader.exec_module(tool)
 metadata=tool.load('_fusion_pcm',PROJECT/'tools/prepare-combat-audio.py')
 protected={p.relative_to(ROOT).as_posix():digest(p) for base in (V7,V8) for p in base.glob('*/*.wav')}
 old_load=tool.load

 def load(name,path):
  module=old_load(name,path)
  if name=='_wuxia_delivery':
   emit=module.emit
   def fusion_emit(ffmpeg,folder,name,title,audio,scratch):
    name=name.replace('weapon-contacts-v8','weapon-contacts-v9').replace('v7-v8-matched','v8-v9-matched')
    title='剑与火 · 钢刃与重量融合' if name=='weapon-contacts-v9' else '剑与火 · V8与V9融合版同响度对照'
    return emit(ffmpeg,folder,name,title,audio,scratch)
   module.emit=fusion_emit
  return module

 def contact(name,variation,steel,recording):
  previous=V7/name[:3]/f'{name}_v{variation}.wav'
  weight=metadata.read_wav(previous)
  if len(weight)!=len(steel):raise ValueError('Contact duration differs between banks')
  war=name.startswith('war_');t=np.arange(len(steel))/RATE
  body=signal.sosfilt(signal.butter(2,[140,1150 if war else 1050],btype='bandpass',fs=RATE,output='sos'),weight)
  end=.230 if war else .155
  body*=np.sin(np.clip(t/.002,0,1)*np.pi/2)**2
  body*=np.exp(-np.maximum(0,t-(.028 if war else .018))/(.075 if war else .045))
  body*=np.sin(np.clip((end-t)/.030,0,1)*np.pi/2)**2
  a,b=round(.004*RATE),round(.070*RATE)
  steel_rms=float(np.sqrt(np.mean(steel[a:b]**2)))
  body*=steel_rms*RATIOS[name]/max(1e-12,float(np.sqrt(np.mean(body[a:b]**2))))
  # The two independently authored layers have arbitrary polarity. Avoid
  # destructive transient cancellation, without moving the recorded onset.
  polarity=-1 if float(np.dot(steel[:round(.1*RATE)],body[:round(.1*RATE)]))<0 else 1
  body*=polarity;audio=steel+body
  level_gain=steel_rms/max(1e-12,float(np.sqrt(np.mean(audio[a:b]**2))))
  audio*=level_gain
  audio[:12]*=np.linspace(0,1,12);audio[-round(.012*RATE):]*=np.linspace(1,0,round(.012*RATE))
  safety_gain=min(1.,.64/max(1e-12,float(np.max(np.abs(audio)))))
  audio*=safety_gain
  if not np.isfinite(audio).all():raise ValueError('Non-finite fusion')
  return audio,dict(steelSource=(V8/name[:3]/f'{name}_v{variation}.wav').relative_to(ROOT).as_posix(),
   steelSha256=digest(V8/name[:3]/f'{name}_v{variation}.wav'),bodySource=previous.relative_to(ROOT).as_posix(),
   bodySha256=digest(previous),bodyBandHz=[140,1150 if war else 1050],bodyEndSeconds=end,
   bodyToSteelActiveWindowRms=RATIOS[name],bodyPolarity=polarity,activeWindowSeconds=[.004,.070],
   levelMatchGain=level_gain,safetyGain=safety_gain,
   design='V8 recorded steel remains the front; V7 band-limited body and short aftermotion support it. No added wind or full-band modal layer.')

 tool.load=load;tool.make_contact=contact;tool.BASE=V8;tool.RUNTIME=RUNTIME;tool.OUT=OUT
 tool.main()
 # The reused authoring pipeline retains its V7/V8 labels internally; rewrite
 # only comparison labels and generated references, never input provenance.
 for old,new in [('weapon-contacts-v8.markers.json','weapon-contacts-v9.markers.json'),
                 ('v7-v8-matched.markers.json','v8-v9-matched.markers.json')]:
  original=OUT/'audition'/old;target=OUT/'audition'/new
  if original.exists():original.replace(target)

 def labels(value):
  if isinstance(value,dict):
   return {k:('v8' if v=='v7' else 'v9' if v=='v8' else labels(v)) if k=='version' else labels(v) for k,v in value.items()}
  if isinstance(value,list):return [labels(v) for v in value]
  if isinstance(value,str):return value.replace('weapon-contacts-v8','weapon-contacts-v9').replace('v7-v8-matched','v8-v9-matched')
  return value

 for file in (OUT/'audition').glob('*.markers.json'):
  record=labels(json.loads(file.read_text(encoding='utf-8')))
  if file.name=='v8-v9-matched.markers.json':record['note']='V8 0–8s; one-second gap; fusion V9 9–17s. Matched PCM loudness.'
  dump(file,record)
 file=OUT/'manifest.json';record=labels(json.loads(file.read_text(encoding='utf-8')))
 record['version']=9
 record['direction']='V8 recorded blade contacts blended with V7 low-mid body and short aftermotion, without full-band modal re-layering.'
 record['production']='Existing V8 recorded CC0 steel fronts plus band-limited original V7 project body. No new downloads, models or runtime dependencies.'
 for asset in record['assets']:asset['resourcePath']=asset['resourcePath'].replace('audio/combat-v8/','audio/combat-v9/')
 record['preservation']['protectedV7AndV8']=protected
 record['listeningAcceptance']='Pending user listening of the fusion ratio; technical playback and measurements are separate.'
 record['runtimeAcceptance']='Prepared for root runtime routing and Web validation.'
 if any(digest(ROOT/p)!=sha for p,sha in protected.items()):raise ValueError('A prior source bank changed')
 dump(file,record)


if __name__=='__main__':main()
