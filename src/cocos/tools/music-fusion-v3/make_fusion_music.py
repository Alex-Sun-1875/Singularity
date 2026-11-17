"""Re-orchestrate the accepted old theme with the newer orchestral momentum.

The old melody/harmony and new acoustic rhythm section share one new score
and tempo. Finished 80/120 BPM recordings are never overlaid or time-stretched.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
path = ROOT / 'src/cocos/tools/music-iron-rally-v2/make_music.py'
spec = importlib.util.spec_from_file_location('_fusion_orchestra', path)
music = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = music
spec.loader.exec_module(music)
RATE, BPM, BARS = 44100, 104, 32
BEAT = 60 / BPM
OUT = ROOT / 'source-art/audio/music-fusion-v3'
RUNTIME = ROOT / 'src/cocos/assets/resources/audio/music'
sample_instrument = music.instrument


def instrument(identifier, pitch, held):
    if identifier.startswith('original-'):
        return music.shared.instrument(identifier.removeprefix('original-').split(':')[0], pitch, held)
    return sample_instrument(identifier, pitch, held)


def score(mode):
    notes = []
    combat = mode == 'combat'
    melody, harmony = music.shared.MELODY[:8], music.shared.HARMONY[:8]
    bars = 8 if mode == 'aftermath' else BARS

    def add(kind, stem, pitch, at, held, level, pan=0, variant=0):
        notes.append(music.shared.Note(kind+':'+str(variant%2),stem,pitch,round(at,5),held,round(level,5),pan))

    for bar in range(bars):
        section, local = divmod(bar,8)
        root, chord = harmony[local]
        at = bar*4
        energy = (1.,1.08,.88,1.12)[section]
        if mode == 'aftermath':
            # The old warm F-G-Am-Dm return, voiced with the new low strings.
            root,chord = [(41,(53,60,69)),(43,(55,62,71)),(45,(57,64,72)),(38,(50,57,65))][bar//2]
            add('cello-long','body',root,at,3.4,.58,-.15)
            for i,pitch in enumerate(chord):
                add('violin-long','strings',pitch+12,at+i*.025,3.45,.32,(-.5,.22,.5)[i])
            for i,pitch in enumerate((chord[0]+12,chord[2],chord[1]+12)):
                add('original-harp','warmth',pitch,at+i*.75,1.0,.070,.30)
            if bar<3:
                add('bass-drum','percussion',36,at,.14,.38*(1-bar/3),0,bar)
            if bar in (0,2):
                for off,pitch,held in melody[0 if bar==0 else 1]:
                    add('original-flute','theme',pitch,at+off,held,.20,.02)
            if bar in (6,7):
                for off,pitch,held in melody[0 if bar==6 else 7]:
                    add('original-low-flute','theme',pitch-12,at+off,held,.19,.03)
            continue

        # Original harmonic identity, with moderate sampled orchestral mass.
        add('cello-long','body',root,at+.02,3.4,.54 if combat else .50,-.15)
        for i,pitch in enumerate(chord):
            add('violin-long','strings',pitch+12,at+i*.02,3.5,.36*energy,(-.55,.25,.55)[i])
        # Old warm plucked arpeggios remain audible, below the theme and bowing.
        for i,(offset,pitch) in enumerate(zip((0,.75,1.5,2.5,3.25),
                    (root+12,chord[0]+12,chord[2],chord[1]+12,chord[0]+12))):
            add('original-lute','warmth',pitch,at+offset,.42,(.095 if combat else .13)*energy*(1 if i%2==0 else .8),-.32)
        if not combat and local in (1,3,5,7):
            add('original-harp','warmth',chord[1]+12,at+2.65,.55,.050,.35)
        # One theme in a common D-Dorian grid; brass supports rather than
        # replacing it with the unrelated V2 D-minor rally melody.
        for i,(offset,pitch,held) in enumerate(melody[local]):
            if section==2 and not combat and offset>=2:
                continue
            add('original-flute' if section!=2 else 'original-low-flute','theme',
                pitch if section!=2 else pitch-12,at+offset,held,(.22 if combat else .25)*energy,.02)
            if combat and local in (0,2,3,5,7) and (section!=2 or local>=4):
                add('horn-long','brass',pitch-12,at+offset+.012,held,.48*energy,-.10,i)
            if combat and section in (1,3) and local in (0,3,5,7):
                add('violin-long','theme',pitch,at+offset+.018,held,.30*energy,.28)
        # Momentum from the new short strings, tempered by the original space.
        count = 8 if combat else 4
        pitches=(root,root+12,root+7,root+12,root,root+12,root+7,root+12)
        for i in range(count):
            add('cello-short','ostinato',pitches[i if combat else i*2],at+i*(.5 if combat else 1),
                .32 if combat else .44,(.61 if combat else .35)*energy*(1 if i%2==0 else .76),-.23,i+bar)
        if combat and section!=2:
            for i in range(8):
                add('violin-short','ostinato',(chord[0]+12,chord[1]+12,chord[2],chord[1]+12)[i%4],
                    at+i*.5+.015,.30,(.27 if i%2==0 else .21)*energy,.33,i+bar)
        if combat:
            for offset,level in ((0,.84),(2,.64),(3.25,.25)):
                add('bass-drum','percussion',36,at+offset,.14,level*energy,0,bar)
            for i,offset in enumerate((1.5,2.75)):
                add('war-drum','percussion',36,at+offset,.13,(.33 if i==0 else .26)*energy,.22,i+bar)
            if local%2:
                add('snare','percussion',36,at+3,.10,.31*energy,.15,bar)
            if local==7:
                for i,offset in enumerate((3.5,3.75)):
                    add('snare','percussion',36,at+offset,.07,.20+.08*i,.15,i)
            if local in (0,4):
                add('trombone','brass',root,at,.8,.42*energy,-.25)
                add('cymbal','percussion',36,at,.18,.21,.35)
        else:
            add('bass-drum','percussion',36,at,.15,.56*energy,0,bar)
            add('war-drum','percussion',36,at+2.5,.13,.25*energy,.20,bar)
            if local==7:
                add('horn-short','brass',root+12,at+3.5,.24,.25,-.10)
    return notes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',type=Path,default=music.helpers.DEFAULT_FFMPEG)
    args=parser.parse_args()
    if not args.ffmpeg.is_file():parser.error('Use installed FFmpeg; no download')
    music.prepare_library()
    protected={p.relative_to(ROOT).as_posix():music.digest(p) for p in RUNTIME.iterdir()
        if p.is_file() and p.name.startswith(('embers-oaths-','iron-rally-'))}
    protected_sfx={p.relative_to(ROOT).as_posix():music.digest(p) for p in (RUNTIME.parent/'combat-v12').glob('*/*') if p.is_file()}
    music.OUT=OUT;music.TITLE='余烬与铁誓';music.TONALITY='D Dorian / original Embers and Oaths harmony'
    music.BPM=BPM;music.BEAT=BEAT;music.SECONDS=BARS*4*BEAT;music.AFTERMATH_SECONDS=8*4*BEAT
    music.TRACKS={mode:f'embers-iron-{mode}' for mode in ('explore','combat','aftermath')}
    music.score=score;music.instrument=instrument
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'audition').mkdir(exist_ok=True)
    tracks=[];audio={}
    for mode in music.TRACKS:
        report,audio[mode]=music.export(args.ffmpeg,mode);tracks.append(report)
    start=round(8*4*BEAT*RATE)
    parts=[audio['explore'][:10*RATE],audio['combat'][start:start+20*RATE],audio['aftermath'][:10*RATE]]
    preview=parts[0]
    for part in parts[1:]:
        ramp=np.linspace(0,1,RATE)[:,None]
        preview=np.concatenate((preview[:-RATE],preview[-RATE:]*(1-ramp)+part[:RATE]*ramp,part[RATE:]))
    music.delivery.STUDY=OUT
    with tempfile.TemporaryDirectory(prefix='sword-fire-music-fusion-') as temp:
        preview_record=music.delivery.emit(args.ffmpeg,OUT/'audition','embers-iron-showcase','剑与火 · 余烬与铁誓融合版',preview,Path(temp))
    if any(music.digest(ROOT/p)!=sha for p,sha in {**protected,**protected_sfx}.items()):
        raise ValueError('Prior music or release SFX changed')
    music.helpers.write_json(OUT/'manifest.json',dict(theme='余烬与铁誓 / Embers and Iron Oaths',date='2026-11-17',bpm=BPM,
        direction='Original melody, Dorian harmony, flute/plucked warmth plus newer sampled low strings, moderate brass and driving drums; re-orchestrated at one common tempo.',
        oldSource='src/cocos/tools/audio-direction-v2/music_samples.py:MELODY/HARMONY and original instruments',
        oldSourceSha256=music.digest(ROOT/'src/cocos/tools/audio-direction-v2/music_samples.py'),
        sampledSource='source-art/audio/iron-rally-v2/sources/vsco/source-manifest.json',
        production='New unified 104-BPM score using existing original synthesis and already verified CC0 orchestral recordings. No downloads, AI calls or new runtime dependencies; no mixing of finished tracks at incompatible tempos.',
        tracks=tracks,preview=preview_record,previewSections=[dict(mode='explore',start=0,end=10),dict(mode='combat',start=9,end=29),dict(mode='aftermath',start=28,end=38)],
        protectedPriorMusic=protected,protectedReleaseSfx=protected_sfx,totalRuntimeBytes=sum(t['runtimeBytes'] for t in tracks),
        listeningAcceptance='Pending user listening of the blend, distinct from numerical/runtime acceptance.',deviceAcceptance='TapTap target-device listening and real interruptions pending.'))


if __name__=='__main__':main()
