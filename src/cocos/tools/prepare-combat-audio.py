"""Convert accepted V7 individual sources to the small runtime combat library.

No models, downloads, preview snippets, game export, or package/version changes.
Existing Creator import metadata is preserved. Newly created metadata follows
the project's stable UUIDv5 helper and adjacent audio-clip import format.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import types
import uuid
import wave

import numpy as np

PROJECT=Path(__file__).resolve().parents[1]
ROOT=PROJECT.parents[1]
SOURCE=ROOT/'source-art/audio/impact-metal-v7/clips'
OUT=PROJECT/'assets/resources/audio/combat-v7'
RECORD=ROOT/'source-art/audio/runtime-integration-v1'
NAMESPACE=uuid.UUID('da083e9d-c263-48c6-9047-5113c929e94f')
FAMILIES={
    'war':['war_swing','war_slash','war_armor','war_finish'],
    'bow':['bow_draw','bow_release','bow_pierce','bow_heavy','bow_armor'],
    'fir':['fir_charge','fir_burst','fir_wall'],
    'thu':['thu_charge','thu_crack','thu_network'],
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def meta(path,importer):
    target=Path(str(path)+'.meta')
    if target.exists():
        return
    data=dict(ver='1.2.0',importer='directory',imported=True,
              uuid=str(uuid.uuid5(NAMESPACE,path.relative_to(PROJECT).as_posix())),
              files=[],subMetas={},userData={})
    if importer=='audio-clip':
        data.update(ver='1.0.0',importer=importer,files=['.json','.wav'],userData=dict(downloadMode=0))
    elif importer=='typescript':
        data.update(ver='4.0.24',importer=importer)
    target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')


def read_wav(path):
    with wave.open(str(path),'rb') as file:
        rate,channels,width=file.getframerate(),file.getnchannels(),file.getsampwidth()
        raw=file.readframes(file.getnframes())
    if rate!=44100 or channels!=1 or width not in (2,3):
        raise ValueError(f'Unexpected accepted source format: {path}')
    if width==3:
        byte=np.frombuffer(raw,dtype=np.uint8).reshape(-1,3).astype(np.int32)
        value=byte[:,0]|(byte[:,1]<<8)|(byte[:,2]<<16)
        value=np.where(value&0x800000,value-0x1000000,value)
        return value.astype(np.float64)/8388607
    return np.frombuffer(raw,dtype='<i2').astype(np.float64)/32767


def load_bow():
    path=PROJECT/'tools/audio-impact-v7/bow_cues.py'
    module=types.ModuleType('_approved_bow_contact_runtime')
    module.__file__=str(path)
    exec(compile(path.read_text(encoding='utf-8'),str(path),'exec'),module.__dict__)
    return module


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    RECORD.mkdir(parents=True,exist_ok=True)
    meta(OUT,'directory')
    bow=load_bow()
    assets=[]
    for family,names in FAMILIES.items():
        folder=OUT/family
        folder.mkdir(exist_ok=True)
        meta(folder,'directory')
        for cue in names:
            hashes=set()
            for variation in (1,2,3):
                original=SOURCE/f'{cue}_v{variation:02d}.wav'
                if cue=='bow_armor':
                    samples=bow.synth_contact(variation=variation,material='armor',sample_rate=44100)
                    provenance=dict(sourceApi='audio-impact-v7/bow_cues.py:synth_contact(material=armor)',
                                    sourceSha256=digest(PROJECT/'tools/audio-impact-v7/bow_cues.py'))
                else:
                    samples=read_wav(original)
                    provenance=dict(source=str(original.relative_to(ROOT)).replace('\\','/'),sourceSha256=digest(original))
                if samples.ndim!=1 or not np.isfinite(samples).all() or np.max(np.abs(samples))>.64001:
                    raise ValueError(f'Invalid accepted combat source: {cue}/{variation}')
                pcm=np.rint(samples*32767).astype('<i2')
                target=folder/f'{cue}_v{variation}.wav'
                with wave.open(str(target),'wb') as file:
                    file.setnchannels(1);file.setsampwidth(2);file.setframerate(44100)
                    file.writeframes(pcm.tobytes())
                meta(target,'audio-clip')
                decoded=pcm.astype(np.float64)/32767
                error=float(np.max(np.abs(decoded-samples)))
                sha=digest(target)
                if sha in hashes or np.max(np.abs(decoded))>=1 or error>1/32767:
                    raise ValueError('Duplicate/clipped/incorrectly converted runtime source')
                hashes.add(sha)
                assets.append(dict(family=family.upper(),cue=cue,variation=variation,
                    path=str(target.relative_to(ROOT)).replace('\\','/'),resourcePath=f'audio/combat-v7/{family}/{cue}_v{variation}',
                    durationSeconds=len(samples)/44100,sampleRate=44100,channels=1,bitDepth=16,
                    bytes=target.stat().st_size,peak=float(np.max(np.abs(decoded))),clippingSamples=int(np.count_nonzero(np.abs(decoded)>=1)),
                    maximumQuantizationError=error,sha256=sha,**provenance))
    for path in (PROJECT/'assets/scripts/features/audio/common',):
        path.mkdir(parents=True,exist_ok=True);meta(path,'directory')
    for file in ('common/CombatAudioCues.ts','runtime/CombatAudio.ts'):
        path=PROJECT/'assets/scripts/features/audio'/file
        if path.exists():meta(path,'typescript')
    record=dict(production='PCM16 conversion of the accepted individual V7 source clips; elemental clips are the exact V6 sources carried into V7. Bow armor is generated with its already-auditioned V7 material API.',
                sampleRateChoice='44.1kHz mono retains the accepted steel transients and electrical sizzle; no runtime synthesis or extra audio dependency.',
                artisticAcceptance='User accepted V7 direction; this conversion is numerically checked. Runtime mixing and target-device audition remain separate.',
                runtimeAcceptance='Pending integration/browser/device verification; this tool does not export or package a game.',
                metadata='Stable UUIDv5, same namespace/path method as build-hud-render-assets.py; audio importer copied from adjacent project WAV metadata; existing metadata is preserved.',
                assets=assets,totalBytes=sum(a['bytes'] for a in assets),familyBytes={f.upper():sum(a['bytes'] for a in assets if a['family']==f.upper()) for f in FAMILIES},
                validation=dict(clipCount=len(assets),variationsPerCue=3,allFinite=True,noClipping=True,maximumQuantizationError=max(a['maximumQuantizationError'] for a in assets)))
    (RECORD/'sfx-assets.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(output=str(OUT),clips=len(assets),totalBytes=record['totalBytes'],familyBytes=record['familyBytes']),ensure_ascii=False))


if __name__=='__main__':
    main()
