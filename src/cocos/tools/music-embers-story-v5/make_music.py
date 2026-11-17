"""Fuse the newest restrained study with the explicitly chosen earliest theme.

Common original Dorian harmony; old flute/pluck theme and low-string answers.
The original 15-second aftermath stays byte-identical. No finished-song overlay.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('_embers_story_tools',ROOT/'src/cocos/tools/music-iron-rally-v2/make_music.py')
music=importlib.util.module_from_spec(spec);sys.modules[spec.name]=music;spec.loader.exec_module(music)
OUT=ROOT/'source-art/audio/embers-story-v5'
RUNTIME=ROOT/'src/cocos/assets/resources/audio/music'
BPM=96;BEAT=60/BPM;RATE=44100
TRACK_PREFIX='embers-story'
TITLE='余烬与誓言·叙事融合版'
PREVIEW_NAME='embers-story-showcase'
sample_instrument=music.instrument


def instrument(kind,pitch,held):
    if kind.startswith('original-'):
        return music.shared.instrument(kind.removeprefix('original-').split(':')[0],pitch,held)
    return sample_instrument(kind,pitch,held)


def narrative_answer(local,chord):
    """Keep V4's low phrase contour, adapted to the old song's Dorian harmony."""
    answer=[]
    for offset,pitch,held in music.THEME[local]:
        pitch-=12
        if pitch%12==10:pitch+=1  # Bb -> B, the original Dorian colour.
        if pitch%12==1:pitch-=1   # C# -> C, no competing dominant-key melody.
        if offset in (0,2):
            candidates=[p for p in range(pitch-3,pitch+4) if p%12 in {n%12 for n in chord}]
            pitch=min(candidates,key=lambda p:abs(p-pitch))
        answer.append((offset,pitch,held))
    return answer


def score(mode):
    notes=[];combat=mode=='combat'
    melody,harmony=music.shared.MELODY[:8],music.shared.HARMONY[:8]
    def add(kind,stem,pitch,at,held,level,pan=0,variant=0):
        notes.append(music.shared.Note(kind+':'+str(variant%2),stem,pitch,round(at,5),held,round(level,5),pan))
    for bar in range(32):
        section,local=divmod(bar,8);root,chord=harmony[local];at=bar*4
        energy=(1.,1.05,.87,1.06)[section]
        add('cello-long','body',root,at+.02,3.45,.47 if combat else .43,-.15)
        for i,pitch in enumerate(chord):
            upper=pitch+12
            add('violin-long','strings',upper,at+i*.02,3.45,(.13 if upper>76 else .24)*energy,(-.5,.2,.5)[i])
        # Earliest Embers: original plucked arpeggio and restrained flute lead.
        for i,(offset,pitch) in enumerate(zip((0,.75,1.5,2.5,3.25),
                    (root+12,chord[0]+12,chord[2],chord[1]+12,chord[0]+12))):
            add('original-lute','warmth',pitch,at+offset,.46,(.083 if combat else .115)*energy*(1 if i%2==0 else .8),-.3)
        if local in (1,5):
            add('original-harp','detail',chord[1]+12,at+2.65,.6,.042,.32)
        if local<4:
            for offset,pitch,held in melody[local]:
                low=section==2
                add('original-low-flute' if low else 'original-flute','old-theme',pitch-12 if low else pitch,
                    at+offset,held,(.18 if combat else .20)*energy,.02)
        else:
            # The current V4 middle/low-string voice answers the old theme;
            # do not stack two unrelated lead melodies on top of each other.
            for offset,pitch,held in narrative_answer(local,chord):
                if local==4 and offset<1:continue
                add('cello-long','narrative-answer',pitch,at+offset,held,.67*energy,-.08)
            if local==7:
                for offset,pitch,held in melody[7][-1:]:
                    add('original-low-flute','old-theme-return',pitch-12,at+offset,held,.13,.06)
        # V4's low pulse, with no snare, cymbal, high octave theme or fanfare.
        offsets=(0,.5,1.5,2,2.5,3.5) if combat else (0,1.5,2.5,3.5)
        for i,offset in enumerate(offsets):
            pitch=(root,root+7,root+12,root,root+7,root+12)[i]
            add('cello-short','pulse',pitch,at+offset,.33 if combat else .43,
                (.46 if combat else .28)*energy*(1 if i%2==0 else .75),-.22,i+bar)
        if combat and section in (1,3):
            for i,offset in enumerate((1.5,3.5)):
                add('violin-short','pulse',chord[i]+12,at+offset,.30,.13*energy,.30,i+bar)
        add('bass-drum','percussion',36,at,.15,(.65 if combat else .43)*energy,0,bar)
        if combat or local%2:
            add('bass-drum','percussion',36,at+2,.13,(.46 if combat else .21)*energy,0,bar+1)
        for i,offset in enumerate((1.5,3.25) if combat else (2.5,)):
            add('war-drum','percussion',36,at+offset,.13,(.21 if combat else .16)*energy,.20,i+bar)
        if combat and local in (3,7):
            add('horn-long','soft-answer',root+12,at+2.5,1.1,.17,-.1)
    return notes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',type=Path,default=music.helpers.DEFAULT_FFMPEG)
    args=parser.parse_args()
    if not args.ffmpeg.is_file():parser.error('Use installed FFmpeg; no download')
    music.prepare_library()
    protected={p.relative_to(ROOT).as_posix():music.digest(p) for p in RUNTIME.iterdir() if p.is_file() and not p.name.startswith(TRACK_PREFIX+'-')}
    sfx={p.relative_to(ROOT).as_posix():music.digest(p) for p in (RUNTIME.parent/'combat-v12').glob('*/*') if p.is_file()}
    music.OUT=OUT;music.TITLE=TITLE;music.TONALITY='Original D Dorian harmony; V4 low answers adapted to the same harmony'
    music.BPM=BPM;music.BEAT=BEAT;music.SECONDS=80.
    music.TRACKS={mode:f'{TRACK_PREFIX}-{mode}' for mode in ('explore','combat')}
    music.score=score;music.instrument=instrument
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'audition').mkdir(exist_ok=True)
    tracks=[];audio={}
    for mode in music.TRACKS:
        report,audio[mode]=music.export(args.ffmpeg,mode);tracks.append(report)
    old=json.loads((ROOT/'source-art/audio/runtime-integration-v1/music-manifest.json').read_text(encoding='utf-8'))
    aftermath=next(t for t in old['tracks'] if t['mode']=='aftermath')
    source=ROOT/aftermath['asset']
    if music.digest(source)!=aftermath['sha256']:raise ValueError('Original aftermath hash mismatch')
    tracks.append(dict(mode='aftermath',path=aftermath['asset'],resourcePath=aftermath['resourcePath'],sha256=aftermath['sha256'],
        runtimeBytes=source.stat().st_size,bpm=80,authoredSeconds=15.,loop=False,bytePreservedOriginal=True,
        production='Original warm aftermath, independent one-shot; not required to share the fusion loop grid.'))
    raw=subprocess.check_output([str(args.ffmpeg),'-v','error','-i',str(source),'-f','f32le','-ac','2','-ar',str(RATE),'-'])
    audio['aftermath']=np.frombuffer(raw,dtype='<f4').reshape(-1,2).astype(float)
    start=round(8*4*BEAT*RATE)
    parts=[audio['explore'][:10*RATE],audio['combat'][start:start+20*RATE],audio['aftermath'][:10*RATE]]
    preview=parts[0]
    for part in parts[1:]:
        ramp=np.linspace(0,1,RATE)[:,None]
        preview=np.concatenate((preview[:-RATE],preview[-RATE:]*(1-ramp)+part[:RATE]*ramp,part[RATE:]))
    music.delivery.STUDY=OUT
    with tempfile.TemporaryDirectory(prefix='sword-fire-embers-story-') as temp:
        preview_record=music.delivery.emit(args.ffmpeg,OUT/'audition',PREVIEW_NAME,'剑与火 · '+TITLE,preview,Path(temp))
    if any(music.digest(ROOT/p)!=sha for p,sha in {**protected,**sfx}.items()):raise ValueError('Historical music or release audio changed')
    music.helpers.write_json(OUT/'manifest.json',dict(theme=TITLE,date='2026-11-17',bpm=BPM,
        userDirection='Explicit earliest flute/plucked Embers baseline, fused with the newest restrained narrative study; keep contained and avoid elevated brass/high-string fanfare.',
        production='Unified original Dorian score; old flute/pluck theme, V4 middle/low-string voice and restrained pulse, low answers harmonically adapted. No finished-track overlay, reference-game audio, downloads/models or runtime dependencies.',
        sources=['src/cocos/tools/audio-direction-v2/music_samples.py','source-art/audio/music-narrative-v4/music-combat-score.json','source-art/audio/iron-rally-v2/sources/vsco/source-manifest.json'],
        tracks=tracks,preview=preview_record,previewSections=[dict(mode='explore',start=0,end=10),dict(mode='combat',start=9,end=29),dict(mode='aftermath',start=28,end=38)],
        protectedPriorMusic=protected,protectedReleaseSfx=sfx,totalRuntimeBytes=sum(t['runtimeBytes'] for t in tracks),
        listeningAcceptance='Pending user judgement of this new blend, not inferred from the baseline choice.',deviceAcceptance='TapTap target listening and real interruptions pending.'))


if __name__=='__main__':main()
