"""Strengthen fire/thunder attack bodies on the accepted v3 material baseline.

Offline authoring only. Reuse the existing schedule, PCM/FFmpeg delivery and
linear level matching; keep every v2/v3 asset and game runtime file intact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'source-art/audio/impact-burst-v4'
BASE = ROOT/'source-art/audio/impact-refinement-v3'
RATE = 44100
FAMILIES = ('WAR','BOW','FIR','THU')
NAMES = dict(WAR='破军战技',BOW='逐风弓术',FIR='烈焰秘术',THU='雷霆秘术')


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def peak_target(level,preferred=-23.):
    return math.floor(min(preferred,float(level['input_i'])-3.8-float(level['input_tp']))*10)/10


def performance_gain(cue):
    gain = float(cue['gain'])
    name = cue['cue']
    if name in ('war_slash','war_finish','war_armor','bow_pierce','bow_heavy'):
        gain *= 1.065
    elif name in ('fir_burst','thu_crack','thu_network'):
        gain *= dict(basic=1.,signature=1.04,critical=1.08,kill=1.10).get(cue['section'],1.)
    return gain


def build_demo(legacy,prior,synth,family):
    data = json.loads((BASE/'demos'/f'{family.lower()}-15s.cues.json').read_text(encoding='utf-8'))
    events = data['cues']
    audio = np.zeros((15*RATE,2),np.float64)
    revised = []
    for previous in events:
        cue = dict(previous)
        mono = synth(cue['cue'],cue['variation'])
        source_duration = len(mono)/RATE
        mono,deadline = prior.preparation_window(mono,cue['cue'],cue['startSeconds'],events)
        gain = performance_gain(cue)
        angle = (cue['pan']+1)*np.pi/4
        stereo = mono[:,None]*np.array([np.cos(angle),np.sin(angle)])
        legacy._tap(audio,stereo,cue['startSeconds'],RATE,gain)
        cue.update(previousV3Gain=previous['gain'],gain=gain,
                   sourceDurationSeconds=source_duration,durationSeconds=len(mono)/RATE,
                   releaseDeadlineSeconds=deadline,
                   revisionReason='V4 expands elemental attack bodies; physical contact gain is only slightly reinforced.')
        revised.append(cue)
    return audio,revised


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    legacy = load('burst_v2_pcm',here.parent/'audio-direction-v2/sfx_samples.py')
    delivery = load('burst_v2_delivery',here.parent/'audio-direction-v2/assemble_studies.py')
    prior = load('burst_v3_helpers',here.parent/'audio-impact-v3/make_impact_studies.py')
    physical = load('burst_v3_physical',here.parent/'audio-impact-v3/physical_cues.py')
    prior_elemental = load('burst_v3_elemental',here.parent/'audio-impact-v3/elemental_cues.py')
    fire = load('burst_v4_fire',here/'fire_cues.py')
    thunder = load('burst_v4_thunder',here/'thunder_cues.py')
    delivery.STUDY = OUT
    for name in ('clips','demos','audition'):
        (OUT/name).mkdir(parents=True,exist_ok=True)
    banks = (physical,fire,thunder)
    cues = {name:bank for bank in banks for name in bank.CUE_DURATIONS}
    if set(cues) != set(legacy.CUE_DURATIONS):
        raise ValueError('V4 must cover the same 14 sound events')

    def synth(name,variation=1):
        audio = cues[name].synth_cue(name,variation,RATE)
        if audio.ndim != 1 or not np.isfinite(audio).all() or np.max(np.abs(audio)) > .64001:
            raise ValueError(f'Invalid V4 cue: {name}/{variation}')
        return audio

    assets,deltas,hashes = [],[],set()
    physical_sources_preserved = True
    for name,bank in cues.items():
        for variation in range(1,4):
            audio = synth(name,variation)
            path = OUT/'clips'/f'{name}_v{variation:02d}.wav'
            legacy._write_wav(path,audio)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            metrics = legacy.audio_metrics(audio)
            if digest in hashes or metrics['clippingSamples'] or metrics['oversampledPeakDbfs'] > -1.2:
                raise ValueError('Invalid, duplicate or over-peaked source: '+str(path))
            hashes.add(digest)
            if bank is physical:
                previous = BASE/'clips'/path.name
                physical_sources_preserved &= digest == hashlib.sha256(previous.read_bytes()).hexdigest()
            assets.append(dict(cue=name,variation=variation,path=path.relative_to(OUT).as_posix(),
                               description=bank.DESCRIPTIONS[name],sha256=digest,metrics=metrics,
                               sourceBank='v3-physical' if bank is physical else 'v4-elemental'))
        if bank is not physical:
            deltas.append(dict(cue=name,variation=1,
                               before=prior.characteristics(prior_elemental.synth_cue(name,1)),
                               after=prior.characteristics(synth(name,1))))
    if not physical_sources_preserved:
        raise ValueError('The accepted physical source bank must remain identical')

    outputs,levels,after_demos,raw_demos = [],[],{},{}
    baseline_hashes = {}
    with tempfile.TemporaryDirectory(prefix='sword-fire-burst-v4-') as folder:
        scratch = Path(folder)
        for family in FAMILIES:
            raw,events = build_demo(legacy,prior,synth,family)
            raw_demos[family] = raw
            raw_path = scratch/f'{family}-raw.wav'
            legacy._write_wav(raw_path,raw)
            source_level = delivery.loudness(args.ffmpeg,raw_path)
            target = peak_target(source_level)
            audio,gain,_ = prior.match_linear(raw,source_level,target,args.ffmpeg,scratch,
                                              family+'-presentation',legacy,delivery)
            after_demos[family] = audio
            cue_path = OUT/'demos'/f'{family.lower()}-15s.cues.json'
            prior.dump(cue_path,dict(profession=family,durationSeconds=15,reference='WAV timeline',
                                     globalLinearGain=gain,userFeedback='基本可以，更加爆炸，特别是火焰和雷霆',
                                     cues=events))
            result = delivery.emit(args.ffmpeg,OUT/'demos',family.lower()+'-15s',
                                   NAMES[family]+' · 爆发增强版',audio,scratch)
            result.update(profession=family,cues=cue_path.relative_to(OUT).as_posix(),
                          markers=[dict(start=0,end=4,title='普攻'),dict(start=4,end=8,title='代表技能'),
                                   dict(start=8,end=11,title='暴击'),dict(start=11,end=15,title='击杀')])
            outputs.append(result)
            levels.append(dict(profession=family,presentationTargetLufs=target,
                               presentationLinearGain=gain,
                               measuredMasterLufs=float(delivery.loudness(args.ffmpeg,OUT/result['wav'])['input_i'])))

        parts = [(dict(id=family,title=NAMES[family],path=f'demos/{family.lower()}-15s.wav'),after_demos[family])
                 for family in FAMILIES]
        reel,markers = delivery.concatenate(parts)
        result = delivery.emit(args.ffmpeg,OUT/'audition','four-classes-v4','剑与火 · 四职业爆发增强版',reel,scratch)
        result['markers'] = markers
        outputs.append(result)
        spells,markers = delivery.concatenate([item for item in parts if item[0]['id'] in ('FIR','THU')])
        result = delivery.emit(args.ffmpeg,OUT/'audition','spells-v4','剑与火 · 火焰与雷霆爆发增强',spells,scratch)
        result['markers'] = markers
        outputs.append(result)

        comparison,comparison_markers,comparison_levels = [],[],[]
        cursor = 0
        for index,family in enumerate(('FIR','THU')):
            if index:
                comparison.append(np.zeros((2*RATE,2)))
                cursor += 2*RATE
            old_path = BASE/'demos'/f'{family.lower()}-15s.wav'
            baseline_hashes[str(old_path.relative_to(ROOT)).replace('\\','/')] = hashlib.sha256(old_path.read_bytes()).hexdigest()
            before = delivery.read_wav(old_path).astype(np.float64)
            before_level = delivery.loudness(args.ffmpeg,old_path)
            new_path = scratch/f'{family}-comparison-raw.wav'
            legacy._write_wav(new_path,raw_demos[family])
            after_level = delivery.loudness(args.ffmpeg,new_path)
            target = min(peak_target(before_level),peak_target(after_level))
            pair_levels = []
            for version,audio,level in (('v3',before,before_level),('v4',raw_demos[family],after_level)):
                if version == 'v4':
                    comparison.append(np.zeros((RATE,2)))
                    cursor += RATE
                matched,gain,measured = prior.match_linear(audio,level,target,args.ffmpeg,scratch,
                                                          family+'-'+version+'-comparison',legacy,delivery)
                comparison.append(matched)
                pair_levels.append(float(measured['input_i']))
                comparison_markers.append(dict(profession=family,version=version,start=cursor/RATE,
                                               end=(cursor+len(matched))/RATE,targetLufs=target,
                                               measuredPcmLufs=float(measured['input_i']),linearGain=gain))
                cursor += len(matched)
            if abs(pair_levels[0]-pair_levels[1]) > .2:
                raise ValueError('Comparison PCM loudness mismatch: '+family)
            comparison_levels.append(dict(profession=family,targetLufs=target,
                                          beforeMeasuredLufs=pair_levels[0],afterMeasuredLufs=pair_levels[1]))
        result = delivery.emit(args.ffmpeg,OUT/'audition','spells-v3-v4',
                               '剑与火 · 火雷V3与V4无损对照',np.concatenate(comparison),scratch)
        result['markers'] = comparison_markers
        outputs.append(result)

        music_path = ROOT/'source-art/audio/direction-studies-v2/music/a-adaptive-demo/a-adaptive-demo.wav'
        music = delivery.read_wav(music_path).astype(np.float64)
        music_level = delivery.loudness(args.ffmpeg,music_path)
        music_gain = 10**((-28.-float(music_level['input_i']))/20)
        music *= music_gain
        _,events,_ = legacy.build_battle_layer()
        battle = np.zeros((15*RATE,2),np.float64)
        mixed_events = []
        for previous in events:
            event = dict(previous)
            family = event['profession']
            gain = float(event['gain'])
            if event['phase'] == 'release' and event['cue'] in ('fir_burst','thu_crack'):
                gain *= .4
            if event['phase'] == 'windup' or event['cue'] == 'war_swing':
                gain *= .6
            if family in ('WAR','BOW') and event['phase'] == 'contact':
                gain *= 1.065
            family_gain = next(item['presentationLinearGain'] for item in levels if item['profession']==family)
            mono = synth(event['cue'],event['variation'])
            source_duration = len(mono)/RATE
            mono,deadline = prior.preparation_window(mono,event['cue'],event['startSeconds'],events)
            legacy._tap(battle,np.repeat(mono[:,None]/math.sqrt(2),2,axis=1),event['startSeconds'],RATE,gain*family_gain)
            mixed_events.append(dict(event,gain=gain,globalFamilyGain=family_gain,
                                     sourceDurationSeconds=source_duration,durationSeconds=len(mono)/RATE,
                                     releaseDeadlineSeconds=deadline))
        music[15*RATE:30*RATE] += battle*.75
        result = delivery.emit(args.ffmpeg,OUT/'audition','in-music-v4',
                               '剑与火 · 爆发增强与既有音乐',music,scratch)
        result.update(markers=[dict(start=0,end=15,title='探索'),dict(start=15,end=30,title='四职业交战'),
                               dict(start=30,end=45,title='战后')],offlineMix=True,
                      musicSource=str(music_path.relative_to(ROOT)).replace('\\','/'),musicLinearGain=music_gain,
                      battleLinearGain=.75,battleEvents=mixed_events)
        outputs.append(result)

    manifest = dict(schemaVersion=4,date='2026-11-16',
                    userFeedback='V3基本可以，希望更加爆炸，特别是火焰和雷霆；保留此前材质感。',
                    production='Original deterministic synthesis; no recordings, AI audio calls, downloaded samples or new dependencies.',
                    runtimeIntegration='Offline audition revision only; game audio and all previous studies preserved.',
                    listeningAcceptance='Pending audition of the new attack bodies; V3 received basic approval, not a device acceptance.',
                    taptapDeviceAcceptance='Not performed',
                    designNotes=dict(fire=fire.DESIGN_NOTES,thunder=thunder.DESIGN_NOTES,
                                     physical='V3 physical source files are byte-identical; contact-to-preparation balance is reinforced by only 1.065x.'),
                    presentationLevels=levels,
                    comparison=dict(reference='PCM WAV; MP3 is a convenience preview and can shift gated loudness for sparse transients.',
                                    processing='Scalar gain only, no dynamics processor for matching.',
                                    schedule='Same v3 event onsets and sections; preparation remains bounded by release.',
                                    baselineHashes=baseline_hashes,pairs=comparison_levels),
                    assets=assets,objectiveChanges=deltas,outputs=outputs,
                    validation=dict(uniqueSourceClips=len(hashes),all42SourceHashesUnique=len(hashes)==42,
                                    physicalSourceBankUnchanged=physical_sources_preserved,
                                    noDecodedPreviewClipping=all(item['preview']['clippingSamples']==0 for item in outputs),
                                    pcmComparisonPairsWithinPoint2Lufs=True))
    prior.dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=str(OUT),clips=len(hashes),
                          previews=[dict(path=item['mp3'],seconds=item['master']['durationSeconds'],
                                         truePeak=item['preview']['truePeakDbtp']) for item in outputs]),ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
