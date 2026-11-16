"""Render restrained, material-focused impact revisions and level-matched A/Bs.

Authoring only. Reuses the v2 scheduling, PCM writer and FFmpeg preview helpers;
v2 assets, music and game runtime files are never overwritten by this script.
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
from scipy import signal

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / 'source-art/audio/impact-refinement-v3'
V2 = ROOT / 'source-art/audio/direction-studies-v2'
RATE = 44100
FAMILIES = ('WAR', 'BOW', 'FIR', 'THU')
NAMES = dict(WAR='破军战技', BOW='逐风弓术', FIR='烈焰秘术', THU='雷霆秘术')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def characteristics(samples):
    """Describe energy/periodicity changes; these are not realism scores."""
    x = np.asarray(samples, dtype=np.float64)
    energy = x * x
    total = max(float(energy.sum()), 1e-18)
    # These finite events already have edge fades. A whole-file Hann window
    # would suppress the contact at the start and bias differently sized cues.
    spectrum = np.abs(np.fft.rfft(x)) ** 2
    frequencies = np.fft.rfftfreq(len(x), 1 / RATE)
    denominator = max(float(spectrum.sum()), 1e-18)
    # FFT convolution can leave tiny negative roundoff in otherwise silent tails.
    rms = np.sqrt(np.maximum(0., signal.convolve(energy, np.ones(441) / 441, mode='same')))
    active = np.flatnonzero(rms > max(float(rms.max()) * .01, 1e-12))
    segment = x[round(.02 * RATE):min(len(x), round(.17 * RATE))]
    ac = signal.correlate(segment, segment, mode='full', method='fft')[len(segment)-1:]
    minimum = round(RATE / 1800)
    maximum = min(len(ac), round(RATE / 90))
    periodicity = float(np.max(ac[minimum:maximum]) / max(ac[0], 1e-18))
    return dict(durationSeconds=len(x)/RATE,
                low45To180HzEnergyPercent=round(100 * float(spectrum[(frequencies>=45)&(frequencies<180)].sum()) / denominator, 3),
                high3500To10000HzEnergyPercent=round(100 * float(spectrum[(frequencies>=3500)&(frequencies<10000)].sum()) / denominator, 3),
                first20msEnergyPercent=round(100 * float(energy[:882].sum())/total, 3),
                energyAfter100msPercent=round(100 * float(energy[4410:].sum())/total, 3),
                effectiveEndMinus40DbSeconds=round((int(active[-1])+1)/RATE, 5) if len(active) else 0,
                periodicityPeak90To1800Hz=round(periodicity, 5))


def performance_gain(cue):
    """Keep main contact timing; lower windup beds and remove decorative doubles."""
    name, section = cue['cue'], cue['section']
    gain = float(cue['gain'])
    if (name == 'war_armor' and section == 'critical'
        or name == 'bow_pierce' and section == 'kill'
        or name == 'thu_crack' and section == 'critical' and cue['startSeconds'] > 8.62):
        return 0., 'Removed decorative extra contact; the primary contact remains.'
    factor = {'war_swing':.66, 'bow_draw':.58, 'bow_release':.88,
              'fir_charge':.62, 'fir_wall':.46, 'thu_charge':.62,
              'thu_network':.84}.get(name, 1.)
    gain *= factor
    if section in ('critical', 'kill'):
        gain = min(gain, .94)
    return gain, 'Reduced preparation/bed gain and bounded result emphasis.'


def preparation_window(audio, name, at, events):
    releases = {'bow_draw':('bow_release',), 'fir_charge':('fir_burst','fir_wall'),
                'thu_charge':('thu_crack','thu_network')}.get(name)
    if not releases:
        return audio, None
    candidates = [event['startSeconds'] for event in events
                  if event['cue'] in releases and event['startSeconds'] > at]
    deadline = min(candidates) if candidates else None
    if deadline is not None and deadline-at < len(audio)/RATE:
        length = max(2,round((deadline-at)*RATE))
        audio = audio[:length].copy()
        fade = min(length,round(.008*RATE))
        audio[-fade:] *= np.linspace(1,0,fade)
    return audio, deadline


def build_revised(legacy, synth, family):
    _, previous_cues = legacy.build_demo(family)
    output = np.zeros((15 * RATE, 2), np.float64)
    cues = []
    for original in previous_cues:
        cue = dict(original)
        gain, reason = performance_gain(cue)
        mono = synth(cue['cue'], cue['variation'])
        source_duration = len(mono)/RATE
        mono, deadline = preparation_window(mono,cue['cue'],cue['startSeconds'],previous_cues)
        angle = (cue['pan'] + 1) * np.pi / 4
        stereo = mono[:,None] * np.array([np.cos(angle), np.sin(angle)])
        legacy._tap(output, stereo, cue['startSeconds'], RATE, gain)
        cue.update(gain=gain, previousGain=original['gain'], revisionReason=reason,
                   sourceDurationSeconds=source_duration,
                   durationSeconds=len(mono)/RATE, releaseDeadlineSeconds=deadline,
                   muted=gain == 0)
        cues.append(cue)
    return output, cues


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def match_linear(audio, initial_level, target, ffmpeg, scratch, name, legacy, helpers):
    """Re-measure scalar gain: EBU absolute gating can move for sparse effects."""
    gain = 1.
    level = initial_level
    for iteration in range(5):
        delta = target - float(level['input_i'])
        if iteration and abs(delta) <= .06:
            return audio*gain, gain, level
        if float(level['input_tp']) + delta > -2.5:
            raise ValueError(f'Insufficient peak room for linear matching: {name}')
        gain *= 10**(delta/20)
        path = scratch/f'{name}-linear.wav'
        legacy._write_wav(path,audio*gain)
        level = helpers.loudness(ffmpeg,path)
    if abs(target-float(level['input_i'])) > .15:
        raise ValueError(f'Linear loudness did not converge: {name}')
    return audio*gain, gain, level


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    legacy = load('impact_v2_schedule', here.parent/'audio-direction-v2/sfx_samples.py')
    helpers = load('impact_v2_delivery', here.parent/'audio-direction-v2/assemble_studies.py')
    physical = load('impact_v3_physical', here/'physical_cues.py')
    elemental = load('impact_v3_elemental', here/'elemental_cues.py')
    helpers.STUDY = OUT
    (OUT/'clips').mkdir(parents=True, exist_ok=True)
    (OUT/'demos').mkdir(exist_ok=True)
    (OUT/'audition').mkdir(exist_ok=True)
    durations = {**physical.CUE_DURATIONS, **elemental.CUE_DURATIONS}
    if set(durations) != set(legacy.CUE_DURATIONS):
        raise ValueError('The revised cue set must cover the same 14 v2 events')

    def synth(name, variation=1):
        module = physical if name in physical.CUE_DURATIONS else elemental
        audio = module.synth_cue(name, variation, RATE)
        if audio.ndim != 1 or not np.isfinite(audio).all() or np.max(np.abs(audio)) > .58001:
            raise ValueError(f'Invalid revised cue {name}/{variation}')
        return audio

    assets, deltas, hashes = [], [], set()
    for name in durations:
        module = physical if name in physical.CUE_DURATIONS else elemental
        for variation in range(1, 4):
            audio = synth(name, variation)
            path = OUT/'clips'/f'{name}_v{variation:02d}.wav'
            legacy._write_wav(path, audio)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in hashes:
                raise ValueError('Duplicate variation: '+str(path))
            hashes.add(digest)
            metrics = legacy.audio_metrics(audio)
            if metrics['clippingSamples'] or metrics['oversampledPeakDbfs'] > -2:
                raise ValueError('Unsafe source peak: '+str(path))
            assets.append(dict(cue=name, variation=variation,
                               path=path.relative_to(OUT).as_posix(), sha256=digest,
                               description=module.DESCRIPTIONS[name], metrics=metrics))
        deltas.append(dict(cue=name, referenceVariation=1,
                           before=characteristics(legacy.synth_cue(name, 1)),
                           after=characteristics(synth(name, 1))))

    outputs, pairs, demos, levels = [], {}, {}, []
    with tempfile.TemporaryDirectory(prefix='sword-fire-impact-v3-') as temporary:
        scratch = Path(temporary)
        for family in FAMILIES:
            old_path = V2/'sfx'/f'{family.lower()}-15s.wav'
            before = helpers.read_wav(old_path).astype(np.float64)
            after, cues = build_revised(legacy, synth, family)
            new_path = scratch/f'{family}-raw.wav'
            legacy._write_wav(new_path, after)
            old_level = helpers.loudness(args.ffmpeg, old_path)
            new_level = helpers.loudness(args.ffmpeg, new_path)
            pairs[family] = dict(before=before, after=after, cues=cues,
                                 oldLevel=old_level, newLevel=new_level,
                                 baselineSha256=hashlib.sha256(old_path.read_bytes()).hexdigest())
        # Match each profession's before/after pair using only scalar gain.
        # Do not let a very short electric transient force all other families
        # to an unnecessarily quiet common LUFS. There is no dynamics processor.
        reel_parts = []
        comparison = []
        comparison_markers = []
        comparison_cursor = 0
        for index, family in enumerate(FAMILIES):
            pair = pairs[family]
            candidates = [-23.]+[float(pair[key]['input_i'])-3.5-float(pair[key]['input_tp'])
                                 for key in ('oldLevel','newLevel')]
            target = math.floor(min(candidates)*10)/10
            before, old_gain, old_measured = match_linear(
                pair['before'],pair['oldLevel'],target,args.ffmpeg,scratch,
                family+'-before',legacy,helpers)
            after, new_gain, new_measured = match_linear(
                pair['after'],pair['newLevel'],target,args.ffmpeg,scratch,
                family+'-after',legacy,helpers)
            demos[family] = after
            cue_file = OUT/'demos'/f'{family.lower()}-15s.cues.json'
            dump(cue_file, dict(profession=family, durationSeconds=15, reference='WAV time axis',
                                globalLinearGain=new_gain, userPreference='更写实、收得更克制',
                                cues=pair['cues']))
            result = helpers.emit(args.ffmpeg, OUT/'demos', family.lower()+'-15s',
                                  NAMES[family]+' · 克制材质版', after, scratch)
            result.update(profession=family, markers=
                          [dict(start=0,end=4,title='普攻'),dict(start=4,end=8,title='代表技能'),
                           dict(start=8,end=11,title='暴击'),dict(start=11,end=15,title='击杀')],
                          cues=cue_file.relative_to(OUT).as_posix())
            outputs.append(result)
            new_measured = helpers.loudness(args.ffmpeg, OUT/result['wav'])
            difference = abs(float(old_measured['input_i'])-float(new_measured['input_i']))
            if difference > .2:
                raise ValueError(f'A/B loudness difference too large: {family}: {difference}')
            levels.append(dict(profession=family, targetLufs=target,
                               beforeMeasuredLufs=float(old_measured['input_i']),
                               afterMeasuredLufs=float(new_measured['input_i']),
                               beforeLinearGain=old_gain, afterLinearGain=new_gain,
                               referencePath=str((V2/'sfx'/f'{family.lower()}-15s.wav').relative_to(ROOT)).replace('\\','/'),
                               referenceSha256=pair['baselineSha256']))
            reel_parts.append((dict(id=family,title=NAMES[family],path=result['wav']),after))
            if index:
                comparison.append(np.zeros((round(1.25*RATE),2)))
                comparison_cursor += round(1.25*RATE)
            excerpts = []
            for version, audio in [('v2', before), ('v3', after)]:
                excerpt = audio[:8*RATE].copy()
                # Excerpt ends before the critical section; prevent cutting a tail abruptly.
                fade = round(.025*RATE)
                excerpt[-fade:] *= np.linspace(1,0,fade)[:,None]
                path = scratch/f'{family}-{version}-excerpt.wav'
                legacy._write_wav(path,excerpt)
                level = helpers.loudness(args.ffmpeg,path)
                excerpts.append((version,excerpt,level))
            excerpt_target = min([target]+[float(level['input_i'])-3.5-float(level['input_tp'])
                                           for _,_,level in excerpts])
            for version, excerpt, excerpt_level in excerpts:
                if version == 'v3':
                    comparison.append(np.zeros((round(.75*RATE),2)))
                    comparison_cursor += round(.75*RATE)
                excerpt,excerpt_gain,actual_excerpt_level = match_linear(
                    excerpt,excerpt_level,excerpt_target,args.ffmpeg,scratch,
                    family+'-'+version+'-excerpt',legacy,helpers)
                comparison_markers.append(dict(profession=family, version=version,
                                               start=comparison_cursor/RATE,
                                               end=(comparison_cursor+len(excerpt))/RATE,
                                               excerptTargetLufs=excerpt_target,
                                               excerptMeasuredLufs=float(actual_excerpt_level['input_i']),
                                               excerptAdditionalLinearGain=excerpt_gain))
                comparison.append(excerpt)
                comparison_cursor += len(excerpt)
        reel, markers = helpers.concatenate(reel_parts)
        result = helpers.emit(args.ffmpeg, OUT/'audition','four-classes-v3',
                              '剑与火 · 四职业克制材质版',reel,scratch)
        result['markers'] = markers
        outputs.append(result)
        result = helpers.emit(args.ffmpeg, OUT/'audition','before-after-v2-v3',
                              '剑与火 · 四职业旧版与新版对照',np.concatenate(comparison),scratch)
        result['markers'] = comparison_markers
        outputs.append(result)

        # Reuse the existing A music without writing or redesigning its sources.
        music_path = V2/'music/a-adaptive-demo/a-adaptive-demo.wav'
        music = helpers.read_wav(music_path).astype(np.float64)
        music_level = helpers.loudness(args.ffmpeg,music_path)
        music_gain = 10**((-28.-float(music_level['input_i']))/20)
        music *= music_gain
        battle = np.zeros((15*RATE,2),np.float64)
        _, original_events, _ = legacy.build_battle_layer()
        revised_battle_events = []
        for event in original_events:
            family = event['profession']
            raw_gain = float(event['gain'])
            if event['phase'] == 'release' and event['cue'] in ('fir_burst','thu_crack'):
                raw_gain *= .4
            if event['phase'] == 'windup' or event['cue'] == 'war_swing':
                raw_gain *= .6
            family_gain = next(item['afterLinearGain'] for item in levels if item['profession']==family)
            mono = synth(event['cue'],event['variation'])
            source_duration = len(mono)/RATE
            mono,deadline = preparation_window(mono,event['cue'],event['startSeconds'],original_events)
            legacy._tap(battle,np.repeat(mono[:,None]/math.sqrt(2),2,axis=1),
                        event['startSeconds'],RATE,raw_gain*family_gain)
            revised_battle_events.append(dict(event,gain=raw_gain,globalFamilyGain=family_gain,
                                             sourceDurationSeconds=source_duration,
                                             durationSeconds=len(mono)/RATE,
                                             releaseDeadlineSeconds=deadline))
        battle_gain = .75
        music[15*RATE:30*RATE] += battle*battle_gain
        result = helpers.emit(args.ffmpeg,OUT/'audition','in-music-v3',
                              '剑与火 · 克制打击声与现有音乐混音',music,scratch)
        result.update(markers=[dict(start=0,end=15,title='探索'),dict(start=15,end=30,title='四职业交战'),
                               dict(start=30,end=45,title='战后')],
                      offlineMix=True,musicSource=str(music_path.relative_to(ROOT)).replace('\\','/'),
                      musicLinearGain=music_gain,battleLinearGain=battle_gain,
                      battleEvents=revised_battle_events)
        outputs.append(result)

    manifest = dict(schemaVersion=3,date='2026-11-16',
                    userPreference='更写实、收得更克制',
                    production='Original deterministic material-inspired synthesis; no real recordings, AI model calls, downloaded samples or new dependencies.',
                    runtimeIntegration='Offline listening revision only; game audio and previous studies preserved.',
                    listeningAcceptance='Pending user audition; energy and periodicity metrics are not perceptual quality scores.',
                    taptapDeviceAcceptance='Not performed',
                    designNotes=dict(physical=physical.DESIGN_NOTES,elemental=elemental.DESIGN_NOTES),
                    comparison=dict(gainMode='scalar only; no dynamics processing',preferredTargetLufs=-23,
                                    loudnessReference='Uncompressed PCM WAV. Lossy previews can shift gated LUFS for sparse transients; use the WAV A/B for level comparison.',
                                    crossProfessionLoudness='Each before/after pair has its own feasible target; these are not final gameplay mix balances.',
                                    cueSchedule='Main contact onsets and sections inherited from v2; decorative doubles are muted in v3.',
                                    excerptSeconds=8,excerptsMatchedSeparatelyWithScalarGain=True,pairs=levels),
                    assets=assets,objectiveChanges=deltas,outputs=outputs,
                    validation=dict(uniqueSourceClips=len(hashes),all42ClipHashesUnique=len(hashes)==42,
                                    noClipping=all(item['preview']['clippingSamples']==0 for item in outputs),
                                    allPcmComparisonLoudnessDifferencesBelowPoint2Lufs=True))
    dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=str(OUT),clips=len(hashes),
                          pairTargets=[dict(profession=item['profession'],targetLufs=item['targetLufs']) for item in levels],
                          previews=[dict(mp3=item['mp3'],seconds=item['master']['durationSeconds'],
                                         truePeak=item['preview']['truePeakDbtp']) for item in outputs]),
                     ensure_ascii=True,indent=2))


if __name__ == '__main__':
    main()
