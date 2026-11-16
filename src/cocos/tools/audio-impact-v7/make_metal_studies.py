"""Add distinct blade/arrowhead metal contacts while retaining v6 body weight.

Offline authoring only. Reuse the established PCM, encoding, level matching and
action-window tools. Fire/thunder source clips and solo demos are copied exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np

ROOT=Path(__file__).resolve().parents[4]
OUT=ROOT/'source-art/audio/impact-metal-v7'
BASE=ROOT/'source-art/audio/impact-weight-v6'
RATE=44100
FAMILIES=('WAR','BOW','FIR','THU')
NAMES=dict(WAR='破军战技',BOW='逐风弓术',FIR='烈焰秘术',THU='雷霆秘术')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg',required=True)
    args=parser.parse_args()
    here=Path(__file__).resolve().parent
    legacy=load('metal_v2_pcm',here.parent/'audio-direction-v2/sfx_samples.py')
    delivery=load('metal_v2_delivery',here.parent/'audio-direction-v2/assemble_studies.py')
    prior=load('metal_v3_match',here.parent/'audio-impact-v3/make_impact_studies.py')
    v4=load('metal_v4_levels',here.parent/'audio-impact-v4/make_burst_studies.py')
    v6=load('metal_v6_metrics',here.parent/'audio-impact-v6/make_weight_studies.py')
    war=load('metal_v7_war',here/'war_cues.py')
    bow=load('metal_v7_bow',here/'bow_cues.py')
    banks={name:bank for bank in (war,bow) for name in bank.CUE_DURATIONS}
    if set(banks)!={name for name in legacy.CUE_DURATIONS if name.startswith(('war_','bow_'))}:
        raise ValueError('V7 physical sources must cover the existing eight roles')
    delivery.STUDY=OUT
    for folder in ('clips','demos','audition'):
        (OUT/folder).mkdir(parents=True,exist_ok=True)
    old_manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))

    def synth(name,variation=1):
        if name in banks:
            audio=banks[name].synth_cue(name,variation,RATE)
        else:
            audio=delivery.read_wav(BASE/'clips'/f'{name}_v{variation:02d}.wav')[:,0].astype(np.float64)
        if audio.ndim!=1 or not np.isfinite(audio).all() or np.max(np.abs(audio))>.64001:
            raise ValueError(f'Invalid V7 source: {name}/{variation}')
        return audio

    def contact(family,material,variation=1):
        bank=war if family=='WAR' else bow
        audio=bank.synth_contact(variation=variation,material=material,sample_rate=RATE)
        if audio.ndim!=1 or not np.isfinite(audio).all() or np.max(np.abs(audio))>.64001:
            raise ValueError('Invalid material-contact source')
        return audio

    assets,deltas,hashes,preserved=[],[],set(),[]
    for previous in old_manifest['assets']:
        name,variation=previous['cue'],previous['variation']
        destination=OUT/previous['path']
        if name not in banks:
            source=BASE/previous['path']
            shutil.copyfile(source,destination)
            item=dict(previous,reusedFrom=str(source.relative_to(ROOT)).replace('\\','/'))
            if digest(source)!=digest(destination):
                raise ValueError('Elemental clip changed during copy')
            preserved.append(dict(source=item['reusedFrom'],copy=previous['path'],sha256=digest(destination)))
        else:
            audio=synth(name,variation)
            legacy._write_wav(destination,audio)
            metrics=legacy.audio_metrics(audio)
            if metrics['clippingSamples'] or metrics['oversampledPeakDbfs']>-1.2:
                raise ValueError('Unsafe physical metal source')
            item=dict(cue=name,variation=variation,path=previous['path'],
                      description=banks[name].DESCRIPTIONS[name],sha256=digest(destination),
                      metrics=metrics,weight=v6.weight_metrics(audio))
            if variation==1:
                before=delivery.read_wav(BASE/previous['path'])[:,0].astype(np.float64)
                deltas.append(dict(cue=name,before=v6.weight_metrics(before),after=v6.weight_metrics(audio)))
        if item['sha256'] in hashes:
            raise ValueError('Duplicate library source')
        hashes.add(item['sha256'])
        assets.append(item)

    outputs,levels,new_demos=[],[],{}
    comparison,comparison_markers,pairs,baseline_hashes=[],[],[],{}
    cursor=0
    with tempfile.TemporaryDirectory(prefix='sword-fire-impact-metal-v7-') as temporary:
        scratch=Path(temporary)
        for index,family in enumerate(FAMILIES):
            if family in ('FIR','THU'):
                previous=next(item for item in old_manifest['outputs'] if item.get('profession')==family)
                for key in ('wav','mp3','cues'):
                    source,destination=BASE/previous[key],OUT/previous[key]
                    shutil.copyfile(source,destination)
                    if digest(source)!=digest(destination):
                        raise ValueError('Elemental demo changed during copy')
                    preserved.append(dict(source=str(source.relative_to(ROOT)).replace('\\','/'),
                                          copy=previous[key],sha256=digest(destination)))
                result=dict(previous,reusedFrom=str((BASE/previous['wav']).relative_to(ROOT)).replace('\\','/'))
                outputs.append(result)
                level=dict(next(item for item in old_manifest['presentationLevels'] if item['profession']==family))
                levels.append(level)
                new_demos[family]=delivery.read_wav(OUT/result['wav']).astype(np.float64)
                continue

            previous=json.loads((BASE/'demos'/f'{family.lower()}-15s.cues.json').read_text(encoding='utf-8'))
            events=previous['cues']
            raw=np.zeros((15*RATE,2),np.float64)
            revised=[]
            for original in events:
                cue=dict(original)
                material='armor' if cue['cue']=='war_armor' else 'soft'
                # Same arrow release/contact timing; the third basic arrow is
                # explicitly an armoured target in this offline demonstration.
                arrow_armor=(family=='BOW' and cue['cue']=='bow_pierce'
                             and cue['section']=='basic' and cue['variation']==3)
                if arrow_armor:
                    material='armor'
                    mono=contact(family,material,cue['variation'])
                else:
                    mono=synth(cue['cue'],cue['variation'])
                source_duration=len(mono)/RATE
                mono,deadline=prior.preparation_window(mono,cue['cue'],cue['startSeconds'],events)
                angle=(cue['pan']+1)*np.pi/4
                legacy._tap(raw,mono[:,None]*np.array([np.cos(angle),np.sin(angle)]),
                            cue['startSeconds'],RATE,float(cue['gain']))
                if cue['startSeconds']+len(mono)/RATE>15+1/RATE:
                    raise ValueError('Contact crosses demo boundary')
                cue.update(material=material if cue['cue'] not in ('war_swing','bow_draw','bow_release') else 'preparation',
                           sourceApi='synth_contact' if arrow_armor else 'synth_cue',
                           sourceDurationSeconds=source_duration,durationSeconds=len(mono)/RATE,
                           releaseDeadlineSeconds=deadline,
                           revisionReason='V7 adds short metal identity over the heavy body; explicit armour contacts are marked.')
                revised.append(cue)
            raw_path=scratch/f'{family}-raw.wav'
            legacy._write_wav(raw_path,raw)
            raw_level=delivery.loudness(args.ffmpeg,raw_path)
            target=v4.peak_target(raw_level)
            audio,gain,_=prior.match_linear(raw,raw_level,target,args.ffmpeg,scratch,
                                            family+'-presentation',legacy,delivery)
            new_demos[family]=audio
            cue_path=OUT/'demos'/f'{family.lower()}-15s.cues.json'
            prior.dump(cue_path,dict(profession=family,durationSeconds=15,reference='WAV timeline',
                                     globalLinearGain=gain,userFeedback='战士和弓箭手打击需要金属碰撞感',cues=revised))
            result=delivery.emit(args.ffmpeg,OUT/'demos',family.lower()+'-15s',
                                 NAMES[family]+' · 金属接触版',audio,scratch)
            result.update(profession=family,cues=cue_path.relative_to(OUT).as_posix(),
                          markers=[dict(start=0,end=4,title='普攻与接触材质'),dict(start=4,end=8,title='代表技能'),
                                   dict(start=8,end=11,title='暴击'),dict(start=11,end=15,title='击杀')])
            outputs.append(result)
            levels.append(dict(profession=family,presentationTargetLufs=target,presentationLinearGain=gain,
                               measuredMasterLufs=float(delivery.loudness(args.ffmpeg,OUT/result['wav'])['input_i'])))

            old_path=BASE/'demos'/f'{family.lower()}-15s.wav'
            baseline_hashes[str(old_path.relative_to(ROOT)).replace('\\','/')]=digest(old_path)
            before=delivery.read_wav(old_path).astype(np.float64)
            before_level=delivery.loudness(args.ffmpeg,old_path)
            pair_target=min(v4.peak_target(before_level),v4.peak_target(raw_level))
            if index:
                comparison.append(np.zeros((2*RATE,2)))
                cursor+=2*RATE
            measured_pair=[]
            for version,source,level in (('v6',before,before_level),('v7',raw,raw_level)):
                if version=='v7':
                    comparison.append(np.zeros((RATE,2)))
                    cursor+=RATE
                matched,match_gain,measured=prior.match_linear(source,level,pair_target,args.ffmpeg,
                    scratch,family+'-'+version+'-comparison',legacy,delivery)
                comparison.append(matched)
                measured_pair.append(float(measured['input_i']))
                comparison_markers.append(dict(profession=family,version=version,start=cursor/RATE,
                    end=(cursor+len(matched))/RATE,targetLufs=pair_target,
                    measuredPcmLufs=float(measured['input_i']),linearGain=match_gain))
                cursor+=len(matched)
            if abs(measured_pair[0]-measured_pair[1])>.2:
                raise ValueError('PCM comparison loudness mismatch')
            pairs.append(dict(profession=family,targetLufs=pair_target,
                              beforeMeasuredLufs=measured_pair[0],afterMeasuredLufs=measured_pair[1]))

        parts=[(dict(id=family,title=NAMES[family],path=f'demos/{family.lower()}-15s.wav'),new_demos[family])
               for family in FAMILIES]
        for name,title,selected in [('physical-v7','剑与火 · 刀刃与箭头金属接触',parts[:2]),
                                    ('four-classes-v7','剑与火 · 四职业金属接触版',parts)]:
            reel,markers=delivery.concatenate(selected)
            result=delivery.emit(args.ffmpeg,OUT/'audition',name,title,reel,scratch)
            result['markers']=markers
            outputs.append(result)
        result=delivery.emit(args.ffmpeg,OUT/'audition','physical-v6-v7',
                             '剑与火 · 战士弓术V6与V7对照',np.concatenate(comparison),scratch)
        result['markers']=comparison_markers
        outputs.append(result)

        material_audio=np.zeros((16*RATE,2),np.float64)
        material_markers=[]
        for family,material,at in [('WAR','soft',.35),('WAR','armor',4.35),
                                    ('BOW','soft',8.35),('BOW','armor',12.35)]:
            mono=contact(family,material)
            family_gain=next(item['presentationLinearGain'] for item in levels if item['profession']==family)
            legacy._tap(material_audio,np.repeat(mono[:,None]/np.sqrt(2),2,axis=1),at,RATE,family_gain*.8)
            material_markers.append(dict(profession=family,material=material,start=at,
                                         end=at+len(mono)/RATE,variation=1,gain=family_gain*.8))
        result=delivery.emit(args.ffmpeg,OUT/'audition','material-contacts-v7',
                             '剑与火 · 普通接触与撞甲',material_audio,scratch)
        result['markers']=material_markers
        outputs.append(result)

        previous_mix=next(item for item in old_manifest['outputs'] if item['id']=='in-music-v6')
        music_path=ROOT/previous_mix['musicSource']
        music=delivery.read_wav(music_path).astype(np.float64)*float(previous_mix['musicLinearGain'])
        battle=np.zeros((15*RATE,2),np.float64)
        revised_battle=[]
        events=previous_mix['battleEvents']
        for original in events:
            event=dict(original)
            mono=synth(event['cue'],event['variation'])
            source_duration=len(mono)/RATE
            mono,deadline=prior.preparation_window(mono,event['cue'],event['startSeconds'],events)
            family_gain=next(item['presentationLinearGain'] for item in levels if item['profession']==event['profession'])
            legacy._tap(battle,np.repeat(mono[:,None]/np.sqrt(2),2,axis=1),event['startSeconds'],RATE,float(event['gain'])*family_gain)
            event.update(globalFamilyGain=family_gain,sourceDurationSeconds=source_duration,
                         durationSeconds=len(mono)/RATE,releaseDeadlineSeconds=deadline)
            revised_battle.append(event)
        music[15*RATE:30*RATE]+=battle*float(previous_mix['battleLinearGain'])
        result=delivery.emit(args.ffmpeg,OUT/'audition','in-music-v7',
                             '剑与火 · 金属接触与既有音乐',music,scratch)
        result.update(markers=previous_mix['markers'],offlineMix=True,musicSource=previous_mix['musicSource'],
                      musicLinearGain=previous_mix['musicLinearGain'],battleLinearGain=previous_mix['battleLinearGain'],
                      battleEvents=revised_battle)
        outputs.append(result)

    manifest=dict(schemaVersion=7,date='2026-11-16',
                  userFeedback='战士和弓箭手打击需要金属碰撞感；保留重量、短弓风，火雷沿用当前版本。',
                  production='Original deterministic modelling using installed NumPy/SciPy/FFmpeg; no recordings, AI calls, downloaded samples or new dependencies.',
                  runtimeIntegration='Offline audition only; no game runtime audio or former study files changed.',
                  listeningAcceptance='Pending judgement of blade/arrowhead metal identity and weight; numerical measures are not perceptual acceptance.',
                  taptapDeviceAcceptance='Not performed',
                  designNotes=dict(war=war.DESIGN_NOTES,bow=bow.DESIGN_NOTES,
                                   performance='Same V6 event onsets/gains. One basic arrow is explicitly an armour demonstration; ordinary contacts have quieter metal identity.',
                                   elemental='18 source clips and 2 complete solo demos/cue sets are byte-identical copies of V6.'),
                  presentationLevels=levels,
                  comparison=dict(reference='PCM WAV; MP3 is a convenience preview.',
                                  processing='Scalar gain only for matching.',baselineHashes=baseline_hashes,pairs=pairs),
                  assets=assets,objectiveChanges=deltas,preservedElementalFiles=preserved,outputs=outputs,
                  validation=dict(uniqueLibraryClips=len(hashes),all42LibraryHashesUnique=len(hashes)==42,
                                  copiedElementalFileCount=len(preserved),elementalCopiesByteIdentical=True,
                                  noNewPreviewClipping=all(item['preview']['clippingSamples']==0 for item in outputs),
                                  pcmComparisonPairsWithinPoint2Lufs=True))
    prior.dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=str(OUT),clips=len(hashes),elementalCopies=len(preserved),
                          previews=[dict(path=item['mp3'],seconds=item['master']['durationSeconds'],
                                         truePeak=item['preview']['truePeakDbtp']) for item in outputs]),ensure_ascii=True,indent=2))


if __name__=='__main__':
    main()
