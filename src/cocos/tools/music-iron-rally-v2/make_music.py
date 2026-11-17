"""Compose Ironbound Rally using verified CC0 orchestral performances.

Uses the project's existing score/render, circular room, FFmpeg and Cocos
metadata helpers. All sampling occurs offline; the game plays three premixes.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / 'src/cocos'
OUT = ROOT / 'source-art/audio/iron-rally-v2'
SOURCES = OUT / 'sources/vsco'
RUNTIME = PROJECT / 'assets/resources/audio/music'
RATE, BPM, BARS = 44100, 120, 32
BEAT, SECONDS = 60 / BPM, BARS * 4 * 60 / BPM
TRACKS = {mode: f'iron-rally-{mode}' for mode in ('explore', 'combat', 'aftermath')}
TITLE = '铁誓进军'
TONALITY = 'D minor with A-major dominant'
AFTERMATH_SECONDS = 16.
FIXED_MASTER_GAINS = {}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


helpers = load('_iron_loop_helpers', PROJECT / 'tools/audio-runtime-v1/make_music_loops.py')
shared = helpers.original_instruments()
pcm = load('_iron_pcm_helpers', PROJECT / 'tools/prepare-combat-audio.py')
delivery = load('_iron_preview_helpers', PROJECT / 'tools/audio-direction-v2/assemble_studies.py')
matching = load('_iron_match_helpers', PROJECT / 'tools/audio-impact-v3/make_impact_studies.py')
legacy = load('_iron_pcm_metrics', PROJECT / 'tools/audio-direction-v2/sfx_samples.py')
CONFIG = {
    'cello-short': (.18, .13), 'violin-short': (.14, .12),
    'cello-long': (.12, .32), 'violin-long': (.10, .32),
    'horn-long': (.17, .22), 'horn-short': (.17, .14), 'trombone': (.15, .24),
    'bass-drum': (.28, .65), 'war-drum': (.24, .45), 'snare': (.16, .24), 'cymbal': (.10, .60),
}
SAMPLES = {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_library():
    manifest = json.loads((SOURCES / 'source-manifest.json').read_text(encoding='utf-8'))
    if manifest['license'] != 'CC0-1.0':
        raise ValueError('Missing verified CC0 source')
    for item in manifest['files']:
        if digest(SOURCES / item['path']) != item['sha256']:
            raise ValueError('Recorded source hash changed')
    for kind, files in manifest['groups'].items():
        rows = []
        for path in files:
            rate, data = wavfile.read(SOURCES / path)
            value = data.astype(np.float64) / (2 ** (np.iinfo(data.dtype).bits - 1)) if np.issubdtype(data.dtype, np.integer) else data.astype(np.float64)
            if value.ndim == 2:
                mono = value.mean(axis=1)
                if np.sqrt(np.mean(mono**2)) < .65 * np.sqrt(np.mean(value**2)):
                    mono = value[:, int(np.argmax(np.mean(value**2, axis=0)))]
                value = mono
            if rate != RATE:
                ratio = Fraction(RATE, rate)
                value = resample_poly(value, ratio.numerator, ratio.denominator)
            # Trim recording lead-in; retain 4ms before the first musical onset.
            envelope = np.convolve(value**2, np.ones(128)/128, mode='same')
            onset = np.flatnonzero(envelope > max(envelope.max() * .0025, 1e-10))
            if not len(onset):
                raise ValueError('Silent source: ' + path)
            value = value[max(0, int(onset[0]) - 176):]
            note = re.search(r'_([A-G]#?)(-?\d)_', path)
            # VSCO names use C3 for middle C (MIDI 60).
            root = (int(note[2]) + 2) * 12 + {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}[note[1][0]] + ('#' in note[1]) if note else 36
            rows.append((root, value, path))
        SAMPLES[kind] = rows
    return manifest


@lru_cache(maxsize=384)
def instrument(identifier, pitch, held):
    kind, _, variant = identifier.partition(':')
    variant = int(variant or 0)
    rows = SAMPLES[kind]
    root = min((r[0] for r in rows), key=lambda n: abs(n - pitch))
    choices = [row for row in rows if row[0] == root]
    _, value, _ = choices[variant % len(choices)]
    percussion = kind in ('bass-drum','war-drum','snare','cymbal')
    if not percussion:
        ratio = Fraction(2 ** ((root - pitch) / 12)).limit_denominator(2048)
        value = resample_poly(value, ratio.numerator, ratio.denominator)
    target_rms, release = CONFIG[kind]
    count = min(len(value), round((held + release) * RATE))
    sound = value[:count].copy()
    end = min(round(.21 * RATE), len(sound))
    strength = np.sqrt(np.mean(sound[round(.012 * RATE):end]**2))
    sound *= target_rms / max(1e-8, strength)
    # Preserve the recorded attack; release held notes without hard cuts.
    time = np.arange(len(sound)) / RATE
    if not percussion:
        sound *= np.cos(np.clip((time - held) / release, 0, 1) * np.pi / 2) ** 2
    sound[:88] *= np.linspace(0, 1, 88)
    fade = min(len(sound), round(.025 * RATE))
    sound[-fade:] *= np.linspace(1, 0, fade)
    sound *= min(1., .90 / max(1e-12, float(np.max(np.abs(sound)))))
    return sound.astype(np.float32)


# New D-minor progression, with dominant A major for drive into the loop head.
HARMONY = [(38,(50,57,65)),(34,(50,58,65)),(41,(53,60,69)),(33,(49,57,64)),
           (43,(50,58,67)),(34,(50,58,65)),(45,(49,57,64)),(45,(49,57,64))]
# A new rising rally motif and a lower answering phrase, in beats.
THEME = [((0,62,.75),(1,62,.35),(1.5,65,.4),(2,67,.75),(3,69,.8)),
         ((0,70,1.35),(1.5,69,.4),(2,65,.75),(3,62,.8)),
         ((0,65,.7),(1,67,.35),(1.5,69,.4),(2,72,1.4)),
         ((0,73,.7),(1,69,.7),(2,64,.75),(3,61,.8)),
         ((0,67,.7),(1,70,.7),(2,74,1.4)),
         ((0,70,.7),(1,69,.35),(1.5,67,.35),(2,65,1.4)),
         ((0,64,.7),(1,61,.7),(2,57,.7),(3,61,.7)),
         ((0,64,.7),(1,67,.35),(1.5,64,.35),(2,61,.7),(3,57,.7))]


def score(mode):
    notes = []
    combat = mode == 'combat'
    bars = 8 if mode == 'aftermath' else BARS
    def add(kind, stem, pitch, at, held, level, pan=0, variant=0):
        notes.append(shared.Note(kind + ':' + str(variant % 2), stem, pitch, round(at,5), held, level, pan))
    for bar in range(bars):
        section, local = divmod(bar, 8)
        root, chord = HARMONY[local]
        at = bar * 4
        energy = (1.,1.12,.85,1.18)[section]
        if mode == 'aftermath':
            # Same new theme settles into D minor; no triumphant boss claim.
            root, chord = [(34,(50,58,65)),(43,(50,58,67)),(45,(49,57,64)),(38,(50,57,65))][min(bar//2,3)]
            for i, pitch in enumerate(chord):
                add('violin-long','strings',pitch+12,at,3.4,.65-i*.05,(-.5,.3,.55)[i])
            add('cello-long','strings',root,at,3.4,.9,-.15)
            if bar < 4:
                add('bass-drum','percussion',36,at,.15,.6*(1-bar/5))
            if bar in (0,2,4):
                for off,pitch,held in THEME[bar//2]:
                    add('horn-long','brass',pitch-12,at+off,held,.65*(1-bar/8),-.1)
            continue
        # Sustained harmonic floor and low brass provide actual midrange mass.
        add('cello-long','strings',root,at,3.5,.65 if combat else .72,-.17)
        for i,pitch in enumerate(chord):
            add('violin-long','strings',pitch+12,at+i*.02,3.45,(.43 if combat else .48)*energy,(-.6,.25,.6)[i])
        # Distinct bowed staccato performances create the rhythmic engine.
        count = 8 if combat else 4
        pattern = (root,root+12,root+7,root+12,root,root+12,root+7,root+10)
        for i in range(count):
            add('cello-short','ostinato',pattern[i if combat else i*2],at+i*(.5 if combat else 1),.31 if combat else .44,
                (.82 if i%2==0 else .58)*energy,-.25,i+bar)
        if combat:
            upper = (chord[0]+12,chord[1]+12,chord[2],chord[1]+12)
            for i in range(8):
                add('violin-short','ostinato',upper[i%4],at+i*.5+.015,.30,(.46 if i%2==0 else .34)*energy,.32,i+bar)
        # Four clear 8-bar arrangements: motif, answer, brief space, full return.
        if combat or local in (0,1,4,5,6,7):
            if section != 2 or local >= 4:
                for i,(offset,pitch,held) in enumerate(THEME[local]):
                    add('horn-long','brass',pitch-12,at+offset,held,(.97 if combat else .68)*energy,-.08,i)
                    if combat and section in (1,3):
                        add('violin-long','melody',pitch,at+offset+.012,held,.65*energy,.28)
        if combat:
            for offset,level in ((0,1.1),(1.5,.58),(2,.88),(3.25,.55)):
                add('bass-drum','percussion',36,at+offset,.14,level*energy,0,bar)
            for i,offset in enumerate((.5,1.25,2.5,3.5)):
                add('war-drum','percussion',36,at+offset,.13,(.58 if i%2==0 else .40)*energy,(-.25,.25)[i%2],i+bar)
            for offset in (1,3):
                add('snare','percussion',36,at+offset,.10,.65*energy,.15,bar)
            if local in (3,7):
                for i in range(4):
                    add('snare','percussion',36,at+3+i*.25,.07,.25+.09*i,.12,i)
            for offset in (0,2.5):
                add('trombone','brass',root,at+offset,.72,.68*energy,-.28)
            if local in (0,4):
                add('cymbal','percussion',36,at,.2,.48*energy,.35)
        else:
            add('bass-drum','percussion',36,at,.15,.84*energy,0,bar)
            add('war-drum','percussion',36,at+2,.15,.57*energy,.2,bar)
            if local in (1,3,5,7):
                add('snare','percussion',36,at+3,.1,.38*energy,.16,bar)
            if local in (0,4):
                add('trombone','brass',root,at,1.1,.58,-.27)
        if local==7:
            add('horn-short','brass',57,at+3.5,.25,.7 if combat else .45,.1)
    return notes


def export(ffmpeg, mode):
    notes = score(mode)
    is_loop = mode != 'aftermath'
    seconds = SECONDS if is_loop else AFTERMATH_SECONDS
    if is_loop:
        helpers.RATE=RATE;helpers.BEAT=BEAT;helpers.FRAMES=round(seconds*RATE)
        audio, wraps = helpers.render(type('Sampler',(),{'instrument':staticmethod(instrument)}), notes, mode)
    else:
        # Reuse the same panning; retain the natural finite release at the end.
        audio=np.zeros((round(seconds*RATE),2),np.float32);wraps=0
        for note in notes:
            sound=instrument(note.instrument,note.midi,round(note.held*BEAT,5))*note.level
            angle=(note.pan+1)*np.pi/4;stereo=sound[:,None]*np.array((np.cos(angle),np.sin(angle)),np.float32)
            begin=round(note.beat*BEAT*RATE);count=min(len(stereo),len(audio)-begin)
            audio[begin:begin+count]+=stereo[:count]
        audio[-round(1.1*RATE):]*=np.linspace(1,0,round(1.1*RATE))[:,None]
    target = -20.5 if mode=='explore' else -19.5 if mode=='combat' else -22.
    master=OUT/f'music-{mode}-master.flac';asset=RUNTIME/(TRACKS[mode]+'.mp3')
    with tempfile.TemporaryDirectory(prefix='sword-fire-iron-rally-') as temp:
        temp=Path(temp);raw=temp/'raw.wav';wavfile.write(raw,RATE,audio)
        level=helpers.measure(ffmpeg,raw)
        gain=FIXED_MASTER_GAINS.get(mode)
        if gain is None:
            gain=min(10**((target-float(level['input_i']))/20),10**((-3.5-float(level['input_tp']))/20))
        audio*=gain;wavfile.write(raw,RATE,audio)
        helpers.command((ffmpeg,'-v','error','-nostdin','-y','-i',raw,'-c:a','flac','-sample_fmt','s32','-bits_per_raw_sample',24,master))
        encoders=helpers.command((ffmpeg,'-hide_banner','-encoders')).stdout
        codec='libmp3lame' if 'libmp3lame' in encoders else 'mp3_mf'
        encoded=temp/'encoded.mp3'
        helpers.command((ffmpeg,'-v','error','-nostdin','-y','-i',master,'-c:a',codec,'-b:a','160k','-ar',RATE,
                         '-metadata','title='+TITLE+' · '+{'explore':'行进','combat':'交战','aftermath':'战后'}[mode],encoded))
        helpers.command((ffmpeg,'-v','error','-nostdin','-y','-i',encoded,'-c:a','copy',asset))
        measured=helpers.measure(ffmpeg,asset)
        if float(measured['input_tp'])>-1 or not np.isfinite(audio).all():
            raise ValueError('Unsafe music export')
    helpers.write_meta(asset)
    helpers.write_json(OUT/f'music-{mode}-score.json',dict(mode=mode,bpm=BPM,meter='4/4',bars=32 if is_loop else 8,
        key=TONALITY,seconds=seconds,notes=[asdict(n) for n in notes]))
    report=dict(mode=mode,path=asset.relative_to(ROOT).as_posix(),resourcePath='audio/music/'+TRACKS[mode],sha256=digest(asset),
        master=master.relative_to(ROOT).as_posix(),masterSha256=digest(master),runtimeBytes=asset.stat().st_size,
        bpm=BPM,bars=32 if is_loop else 8,authoredSeconds=seconds,loop=is_loop,tailWrappedNotes=wraps,
        integratedLufs=float(measured['input_i']),truePeakDbtp=float(measured['input_tp']),scalarGain=gain,
        pcm=legacy.audio_metrics(audio),boundaryStep=float(np.max(np.abs(audio[-1]-audio[0]))),
        maximumAdjacentStep=float(np.max(np.abs(np.diff(audio,axis=0)))))
    helpers.write_json(OUT/f'music-{mode}-technical.json',report)
    print(json.dumps(report),flush=True)
    return report,audio


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',type=Path,default=helpers.DEFAULT_FFMPEG)
    args=parser.parse_args()
    if not args.ffmpeg.is_file():parser.error('Use installed FFmpeg; no download')
    source=prepare_library();OUT.mkdir(parents=True,exist_ok=True);RUNTIME.mkdir(parents=True,exist_ok=True)
    protected={p.relative_to(ROOT).as_posix():digest(p) for p in RUNTIME.glob('embers-oaths-*') if p.is_file()}
    protected_sfx={p.relative_to(ROOT).as_posix():digest(p) for p in (RUNTIME.parent/'combat-v12').glob('*/*') if p.is_file()}
    tracks=[];audio={}
    for mode in TRACKS:
        report,audio[mode]=export(args.ffmpeg,mode);tracks.append(report)
    # Standalone presentation: 10s march, 20s battle, then 10s aftermath.
    parts=[audio['explore'][:10*RATE],audio['combat'][16*RATE:36*RATE],audio['aftermath'][:10*RATE]]
    preview=parts[0]
    for part in parts[1:]:
        fade=round(1.0*RATE);ramp=np.linspace(0,1,fade)[:,None]
        preview=np.concatenate((preview[:-fade],preview[-fade:]*(1-ramp)+part[:fade]*ramp,part[fade:]))
    (OUT/'audition').mkdir(exist_ok=True);delivery.STUDY=OUT
    with tempfile.TemporaryDirectory(prefix='sword-fire-iron-preview-') as temp:
        preview_report=delivery.emit(args.ffmpeg,OUT/'audition','iron-rally-showcase','剑与火 · 铁誓进军 · 探索至交战',preview,Path(temp))
    if any(digest(ROOT/p)!=sha for p,sha in {**protected,**protected_sfx}.items()):raise ValueError('Old music or release-only SFX changed')
    helpers.write_json(OUT/'manifest.json',dict(theme='铁誓进军 / Ironbound Rally',date='2026-11-17',bpm=BPM,
        production='New original score using verified CC0 VSCO orchestral recordings; existing NumPy/SciPy and project renderer. No AI model call or new runtime dependency.',
        sourceManifest=(SOURCES/'source-manifest.json').relative_to(ROOT).as_posix(),tracks=tracks,preview=preview_report,
        previewSections=[dict(mode='explore',start=0,end=10),dict(mode='combat',start=9,end=29),dict(mode='aftermath',start=28,end=38)],
        oldMusicProtected=protected,releaseSfxProtected=protected_sfx,totalRuntimeBytes=sum(t['runtimeBytes'] for t in tracks),
        listeningAcceptance='Pending user audition; measurements do not establish musical preference.',
        deviceAcceptance='TapTap Android mix, MP3 loop gap and real interruption recovery pending.'))


if __name__=='__main__':main()
