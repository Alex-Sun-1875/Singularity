"""Recorded knife-foley contacts for the V8 sword/arrow runtime bank.

Uses verified CC0 StarNinjas recordings as the main metal layer. The old bank,
music and elemental audio are preserved; this tool never edits TS or exports a
game. Installed NumPy/SciPy/FFmpeg only; source archives are retrieved separately and recorded. This tool makes no network or AI calls.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np
from scipy import signal


ROOT=Path(__file__).resolve().parents[4]
PROJECT=ROOT/'src/cocos'
OUT=ROOT/'source-art/audio/impact-wuxia-v8'
SOURCE=OUT/'sources/starninjas'
BASE=PROJECT/'assets/resources/audio/combat-v7'
RUNTIME=PROJECT/'assets/resources/audio/combat-v8'
RATE=44100
DEFAULT_FFMPEG=Path('C:/Program Files (x86)/Lenovo/LegionZone/2.0.30.11033/SEGamingAI/services/editor/ffmpeg.exe')
# Recorded takes and fixed playback rates change knife scale, not pitch sweeps.
# Onset alignment is measured from each recording's main transient below.
CONFIG={
 'war_slash':dict(duration=.40,takes=(8,4,3),rates=(.77,.78,.71),end=.205,decay=.052,rms=.090,support=.010),
 'war_armor':dict(duration=.48,takes=(4,8,9),rates=(.68,.70,.62),end=.235,decay=.066,rms=.100,support=.010),
 'war_finish':dict(duration=.56,takes=(8,4,6),rates=(.64,.62,.62),end=.265,decay=.074,rms=.108,support=.013),
 'bow_pierce':dict(duration=.30,takes=(5,2,7),rates=(.92,.86,.91),end=.105,decay=.021,rms=.052,support=.008),
 'bow_heavy':dict(duration=.42,takes=(4,8,5),rates=(.92,.88,.86),end=.155,decay=.034,rms=.074,support=.010),
 'bow_armor':dict(duration=.30,takes=(4,8,3),rates=(1.02,.96,.91),end=.145,decay=.031,rms=.084,support=.009),
}


def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 module=importlib.util.module_from_spec(spec);sys.modules[name]=module
 spec.loader.exec_module(module);return module


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path,data):
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def command(argv):
 result=subprocess.run([str(x) for x in argv],capture_output=True)
 if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))
 return result.stdout


def validate_source():
 """No runtime or derivative output is created before this license/hash gate."""
 path=SOURCE/'source-manifest.json'
 record=json.loads(path.read_text(encoding='utf-8'))
 if record.get('license')!='CC0-1.0' or record.get('author')!='StarNinjas':
  raise ValueError('Expected independently verified StarNinjas CC0-1.0 provenance.')
 html=SOURCE/record['licenseEvidence']['file']
 text=html.read_text(encoding='utf-8',errors='replace')
 if 'creativecommons.org/publicdomain/zero/1.0' not in text:
  raise ValueError('Primary author-page CC0 evidence is missing.')
 manifest_html=next(x for x in record['downloads'] if x['filename']==html.name)
 if digest(html)!=manifest_html['sha256']:raise ValueError('Primary page hash mismatch.')
 for archive in record['archives']:
  for entry in archive['entries']:
   if digest(SOURCE/entry['path'])!=entry['sha256']:raise ValueError('Source archive member changed.')
 return record


def decode_recording(ffmpeg,path):
 raw=command((ffmpeg,'-v','error','-i',path,'-ac','2','-ar',RATE,'-f','f32le','-c:a','pcm_f32le','-'))
 stereo=np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype(np.float64)
 if not np.isfinite(stereo).all():raise ValueError('Non-finite source decode')
 mono=stereo.mean(axis=1)
 rms=float(np.sqrt(np.mean(stereo*stereo)));fold=float(np.sqrt(np.mean(mono*mono)))
 channel='arithmetic stereo average'
 if fold<rms*.65:
  selected=int(np.argmax(np.mean(stereo*stereo,axis=0)));mono=stereo[:,selected].copy();channel=f'channel {selected}, avoids phase cancellation'
 return mono,dict(source=path.relative_to(ROOT).as_posix(),sha256=digest(path),
  decodedSeconds=len(mono)/RATE,unmodifiedStereoPeak=float(np.max(np.abs(stereo))),
  originalFloatOverFullScaleSamples=int(np.count_nonzero(np.abs(stereo)>1)),monoSelection=channel,
  note='Decoded as float; source overshoot was never clipped into integer PCM.')


def scale_rms(x,start,end,target):
 part=x[round(start*RATE):round(end*RATE)]
 return x*target/max(1e-9,float(np.sqrt(np.mean(part*part))))


def make_contact(name,variation,old,recording):
 cfg=CONFIG[name];speed=cfg['rates'][variation-1]
 original_peak=int(np.argmax(np.abs(recording)))
 begin=max(0,original_peak-round(.0025*speed*RATE))
 count=round((cfg['end']+.022)*speed*RATE)
 section=recording[begin:begin+count].copy()
 # Float processing is required: the original Vorbis contains >0dBFS peaks.
 section=signal.sosfilt(signal.butter(2,100,'highpass',fs=RATE,output='sos'),section)
 fraction=Fraction(str(speed)).limit_denominator(1000)
 section=signal.resample_poly(section,fraction.denominator,fraction.numerator)
 section=signal.sosfilt(signal.butter(2,6700 if name.startswith('war_') else 6000,
                                     'lowpass',fs=RATE,output='sos'),section)
 n=round(cfg['duration']*RATE);main=np.zeros(n,np.float64)
 main[:min(n,len(section))]=section[:n]
 t=np.arange(n)/RATE;start_decay=.038 if name.startswith('war_') else .018
 damping=np.exp(-np.maximum(0,t-start_decay)/cfg['decay'])
 damping*=np.sin(np.clip((cfg['end']-t)/.024,0,1)*np.pi/2)**2
 damping*=np.sin(np.clip(t/.00045,0,1)*np.pi/2)**2
 main*=damping
 main=scale_rms(main,.004,min(.070,cfg['end']-.018),cfg['rms'])
 # Retain only a tiny, finite part of the old low-mid contact, not its metal
 # oscillator or long resonant tail. No new modal synthesis is added.
 support=signal.sosfilt(signal.butter(2,[145,490],'bandpass',fs=RATE,output='sos'),old)
 support*=np.exp(-t/.030)*np.sin(np.clip((.095-t)/.020,0,1)*np.pi/2)**2
 support=scale_rms(support,.003,.055,cfg['support'])
 audio=main+support
 audio=signal.sosfilt(signal.butter(2,75,'highpass',fs=RATE,output='sos'),audio)
 audio[:20]*=np.linspace(0,1,20);audio[-round(.012*RATE):]*=np.linspace(1,0,round(.012*RATE))
 peak=float(np.max(np.abs(audio)));gain=min(1.,.64/max(peak,1e-12));audio*=gain
 if not np.isfinite(audio).all() or np.max(np.abs(audio))>.64001:raise ValueError('Invalid contact output')
 return audio,dict(recordedTake=cfg['takes'][variation-1],recordingCropStartSeconds=begin/RATE,
  recordingCropEndSeconds=(begin+len(recording[begin:begin+count]))/RATE,fixedPlaybackRate=speed,
  targetTransientLeadSeconds=.0025,materialEndSeconds=cfg['end'],dampingSeconds=cfg['decay'],
  independentRecordedLayerEnergyShare=float(np.sum(main*main)/max(1e-18,np.sum(main*main)+np.sum(support*support))),
  scalarSafetyGain=gain,design='Recorded metal is the main layer; tiny old low-mid support only. No added wind or modal steel ring.')


def write_runtime(path,audio):
 pcm=np.rint(audio*32767).astype('<i2')
 with wave.open(str(path),'wb') as f:
  f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes(pcm.tobytes())
 decoded=pcm.astype(np.float64)/32767
 return dict(quantizationMaximumError=float(np.max(np.abs(decoded-audio))),peak=float(np.max(np.abs(decoded))))


def render_phrase(bank,seconds,events,legacy):
 audio=np.zeros((round(seconds*RATE),2),np.float64)
 markers=[]
 for name,variant,at in events:
  mono=bank[(name,variant)]
  legacy._tap(audio,np.repeat(mono[:,None]/math.sqrt(2),2,axis=1),at,RATE,.82)
  markers.append(dict(cue=name,variation=variant,start=at,end=at+len(mono)/RATE))
 return audio,markers


def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--ffmpeg',type=Path,default=DEFAULT_FFMPEG);args=parser.parse_args(argv)
 if not args.ffmpeg.is_file():parser.error('Pass an installed FFmpeg path; nothing is downloaded.')
 source_record=validate_source()
 here=Path(__file__).resolve().parent
 legacy=load('_wuxia_pcm',here.parent/'audio-direction-v2/sfx_samples.py')
 delivery=load('_wuxia_delivery',here.parent/'audio-direction-v2/assemble_studies.py')
 matching=load('_wuxia_matching',here.parent/'audio-impact-v3/make_impact_studies.py')
 levels=load('_wuxia_levels',here.parent/'audio-impact-v4/make_burst_studies.py')
 weights=load('_wuxia_metrics',here.parent/'audio-impact-v6/make_weight_studies.py')
 metadata=load('_wuxia_metadata',PROJECT/'tools/prepare-combat-audio.py')
 delivery.STUDY=OUT
 old_files=sorted(BASE.glob('*/*.wav'))
 if len(old_files)!=45:raise ValueError('Expected a complete 45-file V7 baseline')
 protected={p.relative_to(ROOT).as_posix():digest(p) for p in old_files}
 protected_music={p.relative_to(ROOT).as_posix():digest(p) for p in (PROJECT/'assets/resources/audio/music').glob('*') if p.is_file()}
 for folder in (OUT/'clips',OUT/'audition',RUNTIME):folder.mkdir(parents=True,exist_ok=True)
 metadata.meta(RUNTIME,'directory')
 for family in metadata.FAMILIES:
  (RUNTIME/family).mkdir(exist_ok=True);metadata.meta(RUNTIME/family,'directory')
 decoded_sources={};source_analysis=[];assets=[];new_bank={};old_bank={};new_count=0;copied_count=0
 for original in old_files:
  cue,variant_text=original.stem.rsplit('_v',1);variation=int(variant_text);family=original.parent.name
  old=metadata.read_wav(original);old_bank[(cue,variation)]=old
  destination=RUNTIME/family/original.name;master=OUT/'clips'/f'{cue}_v{variation:02d}.wav'
  if cue in CONFIG:
   take=CONFIG[cue]['takes'][variation-1];recording_path=SOURCE/'extracted/clashes'/f'sword_clash.{take}.ogg'
   if take not in decoded_sources:
    decoded_sources[take],record=decode_recording(args.ffmpeg,recording_path);source_analysis.append(record)
   audio,edits=make_contact(cue,variation,old,decoded_sources[take]);legacy._write_wav(master,audio)
   quantization=write_runtime(destination,audio);new_count+=1
   item=dict(cue=cue,variation=variation,family=family.upper(),changed=True,recording=recording_path.relative_to(ROOT).as_posix(),recordingSha256=digest(recording_path),edits=edits,quantization=quantization)
  else:
   shutil.copyfile(original,destination);shutil.copyfile(original,master);audio=old;copied_count+=1
   if digest(destination)!=digest(original):raise ValueError('A preserved runtime sound changed')
   item=dict(cue=cue,variation=variation,family=family.upper(),changed=False,copiedByteExactlyFrom=original.relative_to(ROOT).as_posix())
  metadata.meta(destination,'audio-clip')
  new_meta=json.loads(Path(str(destination)+'.meta').read_text(encoding='utf-8'));old_meta=json.loads(Path(str(original)+'.meta').read_text(encoding='utf-8'))
  if new_meta['uuid']==old_meta['uuid']:raise ValueError('Copied source UUID instead of generating the V8 path UUID')
  audio_metrics=legacy.audio_metrics(audio)
  if audio_metrics['clippingSamples'] or not audio_metrics['finite'] or audio_metrics['oversampledPeakDbfs']>-.8:raise ValueError('Unsafe derived audio')
  if cue in CONFIG and abs(audio_metrics['durationSeconds']-CONFIG[cue]['duration'])>1/RATE:raise ValueError('Runtime duration changed')
  item.update(path=master.relative_to(OUT).as_posix(),runtimePath=destination.relative_to(ROOT).as_posix(),resourcePath=f'audio/combat-v8/{family}/{cue}_v{variation}',bytes=destination.stat().st_size,sha256=digest(destination),sourceMasterSha256=digest(master),metrics=audio_metrics,weight=weights.weight_metrics(audio),uuid=new_meta['uuid'])
  assets.append(item);new_bank[(cue,variation)]=audio
 if new_count!=18 or copied_count!=27:raise ValueError('Expected 18 revised and 27 byte-preserved runtime files')
 for cue in CONFIG:
  if len({digest(RUNTIME/cue[:3]/f'{cue}_v{v}.wav') for v in (1,2,3)})!=3:raise ValueError('Duplicate variation')
 # Main reel: individual contacts, then a short sword chain and arrow sequence.
 main_events=[('war_slash',1,.35),('war_armor',1,1.65),('war_finish',1,3.0),('bow_pierce',1,4.8),('bow_heavy',1,6.0),('bow_armor',1,7.2),('war_slash',1,9.0),('war_armor',2,9.40),('war_finish',3,9.82),('bow_armor',1,12.0),('bow_armor',2,12.38),('bow_heavy',3,12.76),('war_armor',3,15.0),('bow_armor',3,16.30)]
 comparison_events=[('war_slash',1,.35),('war_armor',1,1.45),('war_finish',1,2.55),('bow_pierce',1,4.05),('bow_heavy',1,4.95),('bow_armor',1,5.85),('war_slash',2,6.60),('war_armor',2,7.00),('war_finish',3,7.40)]
 outputs=[]
 with tempfile.TemporaryDirectory(prefix='sword-fire-wuxia-v8-') as temporary:
  scratch=Path(temporary)
  raw,markers=render_phrase(new_bank,18,main_events,legacy);raw_path=scratch/'main-raw.wav';legacy._write_wav(raw_path,raw)
  measured=delivery.loudness(args.ffmpeg,raw_path);target=levels.peak_target(measured)
  audio,gain,_=matching.match_linear(raw,measured,target,args.ffmpeg,scratch,'main',legacy,delivery)
  result=delivery.emit(args.ffmpeg,OUT/'audition','weapon-contacts-v8','剑与火 · 刀刃与箭头真实金属碰撞',audio,scratch)
  result.update(markers=markers,linearPresentationGain=gain,targetLufs=target);outputs.append(result)
  dump(OUT/'audition/weapon-contacts-v8.markers.json',dict(seconds=18,sections=[dict(start=0,end=8,title='单次接触'),dict(start=9,end=10.5,title='战士短连击'),dict(start=12,end=13.3,title='弓箭短连续接触')],cues=markers))
  old_phrase,pair_markers=render_phrase(old_bank,8,comparison_events,legacy);new_phrase,_=render_phrase(new_bank,8,comparison_events,legacy)
  pairs=[]
  for label,part in (('v7',old_phrase),('v8',new_phrase)):
   path=scratch/f'{label}-raw.wav';legacy._write_wav(path,part);pairs.append((label,part,delivery.loudness(args.ffmpeg,path)))
  common_target=min(levels.peak_target(level) for _,_,level in pairs)
  matched_parts=[];pair_levels=[]
  for label,part,level in pairs:
   matched,gain,measurement=matching.match_linear(part,level,common_target,args.ffmpeg,scratch,label,legacy,delivery)
   matched_parts.append(matched);pair_levels.append(dict(version=label,targetLufs=common_target,measuredPcmLufs=float(measurement['input_i']),linearGain=gain))
  if abs(pair_levels[0]['measuredPcmLufs']-pair_levels[1]['measuredPcmLufs'])>.15:raise ValueError('A/B loudness mismatch')
  comparison=np.concatenate((matched_parts[0],np.zeros((RATE,2)),matched_parts[1],np.zeros((RATE,2))))
  result=delivery.emit(args.ffmpeg,OUT/'audition','v7-v8-matched','剑与火 · V7合成与V8真实金属同响度对照',comparison,scratch)
  result.update(pairLevels=pair_levels,markers=[dict(version='v7',start=0,end=8),dict(kind='silence',start=8,end=9),dict(version='v8',start=9,end=17)]);outputs.append(result)
  dump(OUT/'audition/v7-v8-matched.markers.json',dict(seconds=18,sections=result['markers'],sameAttackPattern=pair_markers,levels=pair_levels,note='V7 0–8s, one-second gap, V8 9–17s; WAV pair loudness is matched.'))
 if any(digest(ROOT/p)!=sha for p,sha in protected.items()):raise ValueError('V7 runtime bank changed')
 if any(digest(ROOT/p)!=sha for p,sha in protected_music.items()):raise ValueError('Music changed')
 license_record=dict(author='StarNinjas',license='CC0-1.0',sourcePage=source_record['sourcePage'],licenseURL=source_record['licenseURL'],sourceEvidence=(SOURCE/'source-manifest.json').relative_to(ROOT).as_posix(),sourceEvidenceSha256=digest(SOURCE/'source-manifest.json'),attribution='Sword recordings by StarNinjas (OpenGameArt.org), CC0. Edited by the Sword and Fire project.',recordingProvenance='Author says two knives were used and the recordings were edited in Audacity; not extracted from a film soundtrack.',approvalScope='Source/declared license verified. New processing and audition are not user or device listening acceptance.')
 dump(OUT/'license-provenance.json',license_record)
 (OUT/'LICENSE-SOURCES.txt').write_text('Sword recordings by StarNinjas (OpenGameArt.org), CC0 1.0.\n'+source_record['sourcePage']+'\n'+source_record['licenseURL']+'\nPrimary author-page evidence and original archive/member hashes: sources/starninjas/source-manifest.json.\nRecorded with two knives; not a film soundtrack extraction. Project derivatives retain this provenance.\nThe unchanged procedural project sounds remain original project material.\n',encoding='utf-8')
 manifest=dict(version=8,direction='Recorded metal foley replaces the synthetic modal identity in six contact roles. Runtime implementation is unchanged by this tool.',production='CC0 two-knife recordings by StarNinjas dominate revised contacts; only a small finite old low-mid layer remains. No AI generation or new runtime dependencies; source archives retrieved separately and recorded. No added bow wind.',license=license_record,selectedSourceAnalysis=source_analysis,assets=assets,outputs=outputs,preservation=dict(newContacts=18,byteCopiedRuntimeFiles=27,oldBankUnchanged=True,musicUnchanged=True,protectedMusic=protected_music),validation=dict(runtimeClipCount=len(assets),variations=3,uniqueChangedVariations=True,allFinite=True,noClipping=True,allRuntimeMetaUsesNewUUIDv5Paths=True),totalRuntimeBytes=sum(a['bytes'] for a in assets),listeningAcceptance='Pending user audition of V8. Numerical success and verified recording provenance are not artistic acceptance.',runtimeAcceptance='Assets prepared only; root agent owns TS routing and later Web/TapTap validation.')
 dump(OUT/'manifest.json',manifest)
 print(json.dumps(dict(runtime=str(RUNTIME),clips=len(assets),changed=18,preserved=27,totalRuntimeBytes=manifest['totalRuntimeBytes'],outputs=[dict(id=x['id'],mp3=x['mp3'],seconds=x['master']['durationSeconds'],lufs=x['preview']['integratedLufs']) for x in outputs]),ensure_ascii=False))


if __name__=='__main__':main()
