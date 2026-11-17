"""A restrained narrative study of the project's own V2 theme.

All outputs remain in source-art for listening. The active game is separately
returned to V2; BG3/PAL are reference research, never source audio or melody.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import importlib.util
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
spec=importlib.util.spec_from_file_location('_narrative_orchestra',ROOT/'src/cocos/tools/music-iron-rally-v2/make_music.py')
music=importlib.util.module_from_spec(spec);sys.modules[spec.name]=music;spec.loader.exec_module(music)
OUT=ROOT/'source-art/audio/music-narrative-v4'
BPM=112
base_score=music.score


def score(mode):
    notes=[]
    for n in base_score(mode):
        kind=n.instrument.split(':')[0]
        bar=int(n.beat//4);local=bar%8;offset=n.beat%4
        section=min(3,bar//8)
        ceiling=(1.,.95,1.,.91)[section]
        if kind=='horn-long':
            # Keep the same original theme, now phrased by middle/low strings.
            notes.append(replace(n,instrument='cello-long:0',stem='theme',level=n.level*.80*ceiling))
            if mode!='aftermath' and local in (1,5) and offset<2:
                notes.append(replace(n,level=n.level*.22,stem='brass-answer'))
        elif kind=='horn-short' or kind=='cymbal' or kind=='snare':
            continue
        elif kind=='violin-long':
            if n.stem=='melody':continue  # Remove the rising octave fanfare.
            notes.append(replace(n,level=n.level*(.37 if n.midi>76 else .64)*ceiling))
        elif kind=='violin-short':
            if abs(offset-round(offset))>.03:continue
            notes.append(replace(n,level=n.level*.40*ceiling))
        elif kind=='cello-long':
            notes.append(replace(n,level=n.level*.77))
        elif kind=='cello-short':
            notes.append(replace(n,level=n.level*.74*ceiling))
        elif kind=='bass-drum':
            if mode!='aftermath' and min(abs(offset),abs(offset-2))>.03:continue
            notes.append(replace(n,level=n.level*.66))
        elif kind=='war-drum':
            if mode=='combat' and min(abs(offset-1.25),abs(offset-3.5))>.03:continue
            notes.append(replace(n,level=n.level*.42))
        elif kind=='trombone':
            if local not in (0,4) or offset>.1:continue
            notes.append(replace(n,level=n.level*.45))
    # Long phrases keep the preferred V2 theme. A few plucks give exploration
    # a human-scale point of focus, without adding a new high-register lead.
    if mode=='explore':
        for bar in range(32):
            root,chord=music.HARMONY[bar%8]
            for offset,pitch in ((.25,root+12),(2.5,chord[1])):
                notes.append(music.shared.Note('original-lute:0','detail',pitch,bar*4+offset,.65,.085,-.3))
    return notes


sample_instrument=music.instrument
def instrument(kind,pitch,held):
    if kind.startswith('original-'):
        return music.shared.instrument(kind.removeprefix('original-').split(':')[0],pitch,held)
    return sample_instrument(kind,pitch,held)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',type=Path,default=music.helpers.DEFAULT_FFMPEG)
    args=parser.parse_args()
    if not args.ffmpeg.is_file():parser.error('Use installed FFmpeg; no download')
    music.prepare_library()
    active=ROOT/'src/cocos/assets/resources/audio/music'
    protected={p.relative_to(ROOT).as_posix():music.digest(p) for p in active.iterdir() if p.is_file()}
    protected.update({p.relative_to(ROOT).as_posix():music.digest(p) for p in (active.parent/'combat-v12').glob('*/*') if p.is_file()})
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'prepared').mkdir(exist_ok=True);(OUT/'audition').mkdir(exist_ok=True)
    music.OUT=OUT;music.RUNTIME=OUT/'prepared';music.TITLE='铁誓进军·内敛叙事小样'
    music.BPM=BPM;music.BEAT=60/BPM;music.SECONDS=32*4*60/BPM;music.AFTERMATH_SECONDS=8*4*60/BPM
    music.TRACKS={mode:f'narrative-{mode}' for mode in ('explore','combat','aftermath')}
    music.score=score;music.instrument=instrument
    music.helpers.write_meta=lambda path:None  # Listening artifacts, not imported game assets.
    tracks=[];audio={}
    for mode in music.TRACKS:
        report,audio[mode]=music.export(args.ffmpeg,mode)
        report['proposedResourcePath']=report.pop('resourcePath')
        report['preparedBytes']=report.pop('runtimeBytes')
        report['runtimeImported']=False
        music.helpers.write_json(OUT/f'music-{mode}-technical.json',report)
        tracks.append(report)
    # Equal-loudness authoring target is retained, so restraint comes from
    # register, phrasing, spacing and arrangement rather than a volume reduction.
    start=round(8*4*60/BPM*44100)
    parts=[audio['explore'][:10*44100],audio['combat'][start:start+20*44100],audio['aftermath'][:10*44100]]
    reel=parts[0]
    for part in parts[1:]:
        ramp=np.linspace(0,1,44100)[:,None]
        reel=np.concatenate((reel[:-44100],reel[-44100:]*(1-ramp)+part[:44100]*ramp,part[44100:]))
    music.delivery.STUDY=OUT
    with tempfile.TemporaryDirectory(prefix='sword-fire-narrative-') as temp:
        preview=music.delivery.emit(args.ffmpeg,OUT/'audition','narrative-study','剑与火 · 内敛叙事配乐小样',reel,Path(temp))
    if any(music.digest(ROOT/p)!=sha for p,sha in protected.items()):raise ValueError('Active/historical music or SFX changed')
    music.helpers.write_json(OUT/'manifest.json',dict(direction='Restrained narrative study of project V2 theme; middle/low strings lead, sparse horn answers and soft low pulse. No high octave doubling, snare or cymbal.',
        basis='Ironbound Rally V2, assumed from the immediately previous non-fusion version; user clarification remains welcome.',bpm=BPM,
        production='Existing verified project score, original pluck and CC0 VSCO sources; no new downloads/models/dependencies or borrowed reference melody.',
        scope='Offline listening study only; not routed into the game.',tracks=tracks,preview=preview,protectedActiveAudio=protected,
        listeningAcceptance='Pending user preference; technical rendering does not establish subjective acceptance.'))


if __name__=='__main__':main()
