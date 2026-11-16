"""Extend material-specific attack tails and electrical sizzling on v4 impacts.

Authoring only. Reuses the established PCM, encoding, level-matching and action
window helpers; all old studies and game runtime audio remain untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT/'source-art/audio/impact-tail-v5'
BASE = ROOT/'source-art/audio/impact-burst-v4'
RATE = 44100
FAMILIES = ('WAR','BOW','FIR','THU')
NAMES = dict(WAR='破军战技',BOW='逐风弓术',FIR='烈焰秘术',THU='雷霆秘术')


def load(name,path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tail_metrics(audio):
    x = np.asarray(audio,dtype=np.float64)
    energy = x*x
    total = max(float(energy.sum()),1e-18)
    def window(start,end):
        return float(energy[round(start*RATE):round(end*RATE)].sum())/total*100
    # Short windows describe sustained texture, not a subjective audibility pass.
    occupied = 0
    checked = 0
    for start in np.arange(.1,.65,.02):
        part = x[round(start*RATE):round((start+.02)*RATE)]
        checked += 1
        if len(part) and np.sqrt(np.mean(part*part)) > .003:
            occupied += 1
    return dict(energy100To350msPercent=round(window(.1,.35),4),
                energy350To650msPercent=round(window(.35,.65),4),
                energy650To1000msPercent=round(window(.65,1.),4),
                windows100To650msAboveRmsPoint003=occupied,
                windowsChecked=checked,
                note='Window energy and threshold occupancy are technical descriptors, not listening acceptance.')


def build_demo(legacy,prior,synth,family):
    previous = json.loads((BASE/'demos'/f'{family.lower()}-15s.cues.json').read_text(encoding='utf-8'))
    events = previous['cues']
    audio = np.zeros((15*RATE,2),np.float64)
    revised = []
    for original in events:
        cue = dict(original)
        mono = synth(cue['cue'],cue['variation'])
        source_duration = len(mono)/RATE
        mono,deadline = prior.preparation_window(mono,cue['cue'],cue['startSeconds'],events)
        angle = (cue['pan']+1)*np.pi/4
        legacy._tap(audio,mono[:,None]*np.array([np.cos(angle),np.sin(angle)]),
                    cue['startSeconds'],RATE,float(cue['gain']))
        if cue['startSeconds']+len(mono)/RATE > 15+1/RATE:
            raise ValueError('An extended cue would be cut by the demo boundary: '+cue['cue'])
        cue.update(sourceDurationSeconds=source_duration,durationSeconds=len(mono)/RATE,
                   releaseDeadlineSeconds=deadline,
                   revisionReason='V5 preserves V4 event gain and main contact timing, extending the material-specific tail.')
        revised.append(cue)
    return audio,revised


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    legacy = load('tail_v2_pcm',here.parent/'audio-direction-v2/sfx_samples.py')
    delivery = load('tail_v2_delivery',here.parent/'audio-direction-v2/assemble_studies.py')
    prior = load('tail_v3_helpers',here.parent/'audio-impact-v3/make_impact_studies.py')
    v4 = load('tail_v4_helpers',here.parent/'audio-impact-v4/make_burst_studies.py')
    physical = load('tail_v5_physical',here/'physical_cues.py')
    elemental = load('tail_v5_elemental',here/'elemental_cues.py')
    delivery.STUDY = OUT
    for folder in ('clips','demos','audition'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    banks = {name:bank for bank in (physical,elemental) for name in bank.CUE_DURATIONS}
    if set(banks) != set(legacy.CUE_DURATIONS):
        raise ValueError('All 14 original cue roles must remain covered')

    def synth(name,variation=1):
        audio = banks[name].synth_cue(name,variation,RATE)
        if audio.ndim!=1 or not np.isfinite(audio).all() or np.max(np.abs(audio))>.64001:
            raise ValueError(f'Invalid V5 cue: {name}/{variation}')
        return audio

    assets,deltas,hashes = [],[],set()
    for name,bank in banks.items():
        for variation in range(1,4):
            audio = synth(name,variation)
            path = OUT/'clips'/f'{name}_v{variation:02d}.wav'
            legacy._write_wav(path,audio)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            metrics = legacy.audio_metrics(audio)
            if digest in hashes or metrics['clippingSamples'] or metrics['oversampledPeakDbfs']>-1.2:
                raise ValueError('Duplicate, clipped or unsafe cue: '+str(path))
            hashes.add(digest)
            assets.append(dict(cue=name,variation=variation,path=path.relative_to(OUT).as_posix(),
                               description=bank.DESCRIPTIONS[name],sha256=digest,metrics=metrics,
                               tail=tail_metrics(audio)))
        before = delivery.read_wav(BASE/'clips'/f'{name}_v01.wav')[:,0].astype(np.float64)
        after = synth(name,1)
        count = min(len(before),len(after),round(.03*RATE))
        deltas.append(dict(cue=name,variation=1,
                           before=dict(prior.characteristics(before),tail=tail_metrics(before)),
                           after=dict(prior.characteristics(after),tail=tail_metrics(after)),
                           first30msMaxAbsoluteDifference=float(np.max(np.abs(before[:count]-after[:count])))))

    outputs,levels,raw_demos,new_demos = [],[],{},{}
    comparisons,comparison_markers,comparison_levels,baseline_hashes = [],[],[],{}
    cursor = 0
    with tempfile.TemporaryDirectory(prefix='sword-fire-impact-tail-v5-') as temporary:
        scratch = Path(temporary)
        for index,family in enumerate(FAMILIES):
            raw,events = build_demo(legacy,prior,synth,family)
            raw_demos[family] = raw
            raw_path = scratch/f'{family}-raw.wav'
            legacy._write_wav(raw_path,raw)
            raw_level = delivery.loudness(args.ffmpeg,raw_path)
            target = v4.peak_target(raw_level)
            audio,gain,_ = prior.match_linear(raw,raw_level,target,args.ffmpeg,scratch,
                                              family+'-presentation',legacy,delivery)
            new_demos[family] = audio
            cue_path = OUT/'demos'/f'{family.lower()}-15s.cues.json'
            prior.dump(cue_path,dict(profession=family,durationSeconds=15,reference='WAV timeline',
                                     globalLinearGain=gain,
                                     userFeedback='单次声音稍长，雷霆增加闪电滋滋；战士弓术各自材质尾音',cues=events))
            result = delivery.emit(args.ffmpeg,OUT/'demos',family.lower()+'-15s',
                                   NAMES[family]+' · 余音延长版',audio,scratch)
            result.update(profession=family,cues=cue_path.relative_to(OUT).as_posix(),
                          markers=[dict(start=0,end=4,title='普攻'),dict(start=4,end=8,title='代表技能'),
                                   dict(start=8,end=11,title='暴击'),dict(start=11,end=15,title='击杀')])
            outputs.append(result)
            levels.append(dict(profession=family,presentationTargetLufs=target,
                               presentationLinearGain=gain,
                               measuredMasterLufs=float(delivery.loudness(args.ffmpeg,OUT/result['wav'])['input_i'])))

            old_path = BASE/'demos'/f'{family.lower()}-15s.wav'
            baseline_hashes[str(old_path.relative_to(ROOT)).replace('\\','/')] = hashlib.sha256(old_path.read_bytes()).hexdigest()
            before = delivery.read_wav(old_path).astype(np.float64)
            before_level = delivery.loudness(args.ffmpeg,old_path)
            pair_target = min(v4.peak_target(before_level),v4.peak_target(raw_level))
            if index:
                comparisons.append(np.zeros((2*RATE,2)))
                cursor += 2*RATE
            measured_levels = []
            for version,source,level in (('v4',before,before_level),('v5',raw,raw_level)):
                if version=='v5':
                    comparisons.append(np.zeros((RATE,2)))
                    cursor += RATE
                matched,comparison_gain,measured = prior.match_linear(
                    source,level,pair_target,args.ffmpeg,scratch,family+'-'+version+'-comparison',legacy,delivery)
                comparisons.append(matched)
                measured_levels.append(float(measured['input_i']))
                comparison_markers.append(dict(profession=family,version=version,start=cursor/RATE,
                                               end=(cursor+len(matched))/RATE,targetLufs=pair_target,
                                               measuredPcmLufs=float(measured['input_i']),linearGain=comparison_gain))
                cursor += len(matched)
            if abs(measured_levels[0]-measured_levels[1])>.2:
                raise ValueError('PCM comparison loudness mismatch: '+family)
            comparison_levels.append(dict(profession=family,targetLufs=pair_target,
                                          beforeMeasuredLufs=measured_levels[0],afterMeasuredLufs=measured_levels[1]))

        parts = [(dict(id=family,title=NAMES[family],path=f'demos/{family.lower()}-15s.wav'),new_demos[family])
                 for family in FAMILIES]
        reel,markers = delivery.concatenate(parts)
        result = delivery.emit(args.ffmpeg,OUT/'audition','four-classes-v5',
                               '剑与火 · 四职业材质余音与电弧滋滋',reel,scratch)
        result['markers'] = markers
        outputs.append(result)
        result = delivery.emit(args.ffmpeg,OUT/'audition','four-classes-v4-v5',
                               '剑与火 · 四职业V4与V5无损对照',np.concatenate(comparisons),scratch)
        result['markers'] = comparison_markers
        outputs.append(result)

        # Short isolated contacts make each actual tail easy to inspect without
        # confusing a longer demonstration with a longer individual sound.
        isolated = np.zeros((16*RATE,2),np.float64)
        isolated_markers = []
        for family,name,at in [('WAR','war_finish',.35),('BOW','bow_heavy',4.35),
                               ('FIR','fir_burst',8.35),('THU','thu_crack',12.35)]:
            mono = synth(name,1)
            family_gain = next(item['presentationLinearGain'] for item in levels if item['profession']==family)
            legacy._tap(isolated,np.repeat(mono[:,None]/np.sqrt(2),2,axis=1),at,RATE,family_gain*.8)
            isolated_markers.append(dict(profession=family,cue=name,start=at,
                                         end=at+len(mono)/RATE,variation=1,gain=family_gain*.8))
        result = delivery.emit(args.ffmpeg,OUT/'audition','isolated-tails-v5',
                               '剑与火 · 四职业单发余音',isolated,scratch)
        result['markers'] = isolated_markers
        outputs.append(result)

        music_path = ROOT/'source-art/audio/direction-studies-v2/music/a-adaptive-demo/a-adaptive-demo.wav'
        music = delivery.read_wav(music_path).astype(np.float64)
        music_level = delivery.loudness(args.ffmpeg,music_path)
        music_gain = 10**((-28.-float(music_level['input_i']))/20)
        music *= music_gain
        previous_manifest = json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
        previous_mix = next(item for item in previous_manifest['outputs'] if item['id']=='in-music-v4')
        events = previous_mix['battleEvents']
        battle = np.zeros((15*RATE,2),np.float64)
        revised_events = []
        for original in events:
            event = dict(original)
            mono = synth(event['cue'],event['variation'])
            source_duration = len(mono)/RATE
            mono,deadline = prior.preparation_window(mono,event['cue'],event['startSeconds'],events)
            gain = float(event['gain'])
            family_gain = next(item['presentationLinearGain'] for item in levels if item['profession']==event['profession'])
            legacy._tap(battle,np.repeat(mono[:,None]/np.sqrt(2),2,axis=1),event['startSeconds'],RATE,gain*family_gain)
            event.update(globalFamilyGain=family_gain,sourceDurationSeconds=source_duration,
                         durationSeconds=len(mono)/RATE,releaseDeadlineSeconds=deadline)
            revised_events.append(event)
        music[15*RATE:30*RATE] += battle*.75
        result = delivery.emit(args.ffmpeg,OUT/'audition','in-music-v5',
                               '剑与火 · 电弧和材质余音与既有音乐',music,scratch)
        result.update(markers=[dict(start=0,end=15,title='探索'),dict(start=15,end=30,title='四职业交战'),
                               dict(start=30,end=45,title='战后')],offlineMix=True,
                      musicSource=str(music_path.relative_to(ROOT)).replace('\\','/'),musicLinearGain=music_gain,
                      battleLinearGain=.75,battleEvents=revised_events)
        outputs.append(result)

    manifest = dict(schemaVersion=5,date='2026-11-16',
                    userFeedback='单次音效时间稍长；雷霆加闪电滋滋，战士和弓箭手同样延长各自材质余音。',
                    production='Original deterministic material synthesis using installed NumPy/SciPy/FFmpeg; no recordings, AI model calls, downloads or new dependencies.',
                    runtimeIntegration='Offline audition only; game runtime and all older studies preserved.',
                    listeningAcceptance='Pending audition of the longer tails and electrical sizzling; metrics do not prove audibility or preference.',
                    taptapDeviceAcceptance='Not performed',
                    designNotes=dict(physical=physical.DESIGN_NOTES,elemental=elemental.DESIGN_NOTES,
                                     performance='V4 event gains and onsets are preserved; preparation is still cut at release, while contact tails may continue.'),
                    presentationLevels=levels,
                    comparison=dict(reference='PCM WAV; MP3 is a convenience preview and can shift gated loudness.',
                                    processing='Scalar gain only, no dynamics processor for matching.',
                                    baselineHashes=baseline_hashes,pairs=comparison_levels),
                    assets=assets,objectiveChanges=deltas,outputs=outputs,
                    validation=dict(uniqueSourceClips=len(hashes),all42SourceHashesUnique=len(hashes)==42,
                                    noDecodedPreviewClipping=all(item['preview']['clippingSamples']==0 for item in outputs),
                                    pcmComparisonPairsWithinPoint2Lufs=True))
    prior.dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=str(OUT),clips=len(hashes),
                          previews=[dict(path=item['mp3'],seconds=item['master']['durationSeconds'],
                                         truePeak=item['preview']['truePeakDbtp']) for item in outputs]),ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
