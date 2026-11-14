"""Pose-derived physical sprite calibration, independent of weapon/alpha boxes."""
from pathlib import Path
import json
import collections
import numpy as np
from scipy.ndimage import gaussian_filter1d

HERE=Path(__file__).resolve().parent

def body_measure(record,pose):
    if not pose or len(pose['landmarks'])!=33:return None
    xy=np.array([[p['x'],p['y']] for p in pose['landmarks']])*record['scale']
    xyz=np.array([[p['x'],p['y'],p['z']] for p in pose['worldLandmarks']])
    visibility=np.array([p['visibility'] for p in pose['landmarks']])
    def length(a,b):
        delta=xyz[a].mean(0)-xyz[b].mean(0);l3=np.linalg.norm(delta)
        cosine=np.linalg.norm(delta[:2])/max(l3,.001)
        confidence=min(visibility[a].max(),visibility[b].max())
        if confidence<.55 or cosine<.60:return None
        return float(np.linalg.norm(xy[a].mean(0)-xy[b].mean(0))/cosine)
    torso=length([11,12],[23,24])
    thighs=[v for v in [length([23],[25]),length([24],[26])] if v is not None]
    shins=[v for v in [length([25],[27]),length([26],[28])] if v is not None]
    if torso is None or not thighs or not shins:return None
    thigh=float(np.median(thighs));shin=float(np.median(shins))
    return dict(torso=torso,thigh=thigh,shin=shin,equivalentBodyLength=torso+thigh+shin)

def main():
    inv=json.loads((HERE/'inventory.json').read_text())
    poses={(r['image'],r['index']):r for r in json.loads((HERE/'pose-landmarks.json').read_text())['frames']}
    heads={(r['image'],r['index']):r['head'] for r in json.loads((HERE.parent/'local-qwen21-unified-v3/batch-report.json').read_text())['phases']}
    refs={r['direction']:body_measure(r,poses.get((r['image'],r['index']))) for r in inv['frames'] if any(v['action']=='explore_idle_W01' for v in r['refs'])}
    if any(v is None for v in refs.values()) or len(refs)!=4:raise ValueError('Standing reference detection incomplete')
    # Images used together by one action form a shared animation family.
    components={r['image']:{r['image']} for r in inv['frames']}
    actions=collections.defaultdict(set)
    for r in inv['frames']:
        for v in r['refs']:actions[v['action']].add(r['image'])
    for names in actions.values():
        joined=set().union(*(components[n] for n in names))
        for n in joined:components[n]=joined
    families=collections.defaultdict(list);rows=[]
    for r in inv['frames']:
        measure=body_measure(r,poses.get((r['image'],r['index'])))
        raw=refs[r['direction']]['equivalentBodyLength']/measure['equivalentBodyLength'] if measure else None
        reliable=raw is not None and .80<=raw<=1.25
        row=dict(image=r['image'],index=r['index'],direction=r['direction'],phase=r['phase'],references=r['refs'],rawScale=raw if reliable else None,measure=measure)
        rows.append(row);families[(tuple(sorted(components[r['image']])),r['direction'])].append(row)
    summaries=[]
    for (images,direction),family in families.items():
        family.sort(key=lambda r:(images.index(r['image']),r['index']))
        valid=[r['rawScale'] for r in family if r['rawScale'] is not None]
        median=float(np.median(valid)) if valid else 1.0
        median=float(np.clip(median,.85,1.18))
        loop=any(any(k in v['action'] for k in ('walk','run')) for r in family for v in r['references'])
        values=np.array([r['rawScale'] if r['rawScale'] is not None else median for r in family])
        # One stable family scale, with bounded smooth phase residuals for the
        # gait cycles; no bbox-height pumping as knees lift or swords swing.
        smooth=gaussian_filter1d(np.log(values),.85,mode='wrap' if loop else 'nearest')
        factors=np.exp(.55*np.log(median)+.45*smooth) if loop else np.full(len(family),median)
        factors=np.clip(factors,median*.97,median*1.03)
        for row,factor in zip(family,factors):
            reference=any(v['action']=='explore_idle_W01' for v in row['references'])
            row['scale']=1.0 if reference else float(np.clip(factor,.85,1.18))
            # Upright idle has no knee/flight height ambiguity. Match the
            # canonical standing neck-to-ground height exactly, rather than
            # allowing pose-estimator bone uncertainty to leave a 4-6% jump
            # when the sword is drawn. Head pixels are inversely compensated.
            head=heads[(row['image'],row['index'])]
            if not reference and any('idle' in v['action'] for v in row['references']) and 'original_neck_xy' in head:
                reference_neck=181 if direction=='up' else 194
                current_neck=round(head['original_neck_xy'][1])
                row['scale']=float(np.clip((712-reference_neck)/(712-current_neck),.85,1.18))
                row['uprightStandingHeightConstraint']=True
            row['measurementInherited']=row['rawScale'] is None
            row['equivalentBodyRatioAfter']=(row['measure']['equivalentBodyLength']*row['scale']/refs[direction]['equivalentBodyLength']) if row['measure'] else None
        summaries.append(dict(images=images,direction=direction,medianScale=median,phaseScales=[r['scale'] for r in family],validMeasurements=len(valid),frames=len(family)))
    record=dict(reference='current standing explore_idle_W01; same camera/world scale',method='pose-visible torso + thigh + shin length, corrected for inferred foreshortening; stable animation-family/direction scale and bounded gait residuals',referenceBones=refs,physicalFrames=len(rows),reliableMeasurements=sum(r['rawScale'] is not None for r in rows),families=summaries,frames=rows)
    (HERE/'calibration.json').write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode())
    f=np.array([r['scale'] for r in rows]);print(json.dumps({'frames':len(rows),'measured':record['reliableMeasurements'],'scaleRange':[float(f.min()),float(f.max())],'changesOver2Percent':int((abs(f-1)>.02).sum()),'standingFrozen':True}))

if __name__=='__main__':main()
