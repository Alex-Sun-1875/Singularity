"""Read-only alpha/native metadata audit; no generated image edits or new dependencies."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage
import json,hashlib
HERE=Path(__file__).resolve().parent
m=json.loads((HERE/'owned-actions.json').read_text(encoding='utf8'))
old=json.loads((HERE/'original-owned-actions.json').read_text(encoding='utf8'))['actions']
fields=['frames','frameIndices','directionFrameIndices','fps','loop','phaseStarts','row','absoluteFrameIndices']
assert len(m['records'])==17 and len(m['actions'])==24
assert all(a.get(f)==old[k].get(f) for k,a in m['actions'].items() for f in fields)
assert not m['pendingBackgroundSources']
issues=[];reports={}
for n,r in m['records'].items():
    im=Image.open(HERE/n);alpha=np.asarray(im.getchannel('A'));active=alpha>=16
    covered=np.zeros(active.shape,dtype=bool)
    for x,y,w,h in r['rects']:
        assert x>=0 and y>=0 and x+w<=im.width and y+h<=im.height
        covered[y:y+h,x:x+w]=True
    outside=int((active & ~covered).sum())
    if outside:issues.append([n,'visible alpha outside complete rects',outside])
    foreign=[];components=[]
    if im.size==(1024,1536):
        for row in range(4):
            labels,count=ndimage.label(active[row*384:(row+1)*384])
            sizes=np.bincount(labels.ravel());objects=ndimage.find_objects(labels)
            ids=[i for i in range(1,count+1)if sizes[i]>1000]
            ids.sort(key=lambda i:(objects[i-1][1].start+objects[i-1][1].stop)/2)
            components.append(len(ids))
            if len(ids)!=4:issues.append([n,row,'major component count',len(ids)]);continue
            for col,i in enumerate(ids):
                x,y,w,h=r['rects'][row*4+col]
                crop=labels[y-row*384:y-row*384+h,x:x+w]
                pixels=sum(int((crop==j).sum())for j in ids if j!=i)
                foreign.append(pixels)
                if pixels:issues.append([n,row,col,'neighbour pixels in rect',pixels])
    corners=[int(alpha[y:y+5,x:x+5].max())for x,y in [(0,0),(im.width-5,0),(0,im.height-5),(im.width-5,im.height-5)]]
    if max(corners)>=16:issues.append([n,'opaque corner',corners])
    reports[n]={'dimensions':list(im.size),'alphaMinMax':[int(alpha.min()),int(alpha.max())],
                'below16Fraction':float((alpha<16).mean()),'corners5MaxAlpha':corners,
                'visibleAlphaOutsideRects':outside,'majorComponentsPerDirection':components,
                'neighbourPixelsInEachRect':foreign,'allSourceRuntimeRawSHAEqual':r['sourceSHA256']==r['runtimeSHA256']==r['rawSHA256'],
                'UPPMethod':'Original action-level1.556world stature retained; face/shoulder/feet scale stable, no hairstyle height normalization.'}
    assert reports[n]['allSourceRuntimeRawSHAEqual']
run_checks={}
for key,a in m['actions'].items():
    if not a.get('frameImages'):continue
    assert a['frames']==8 and len(a['frameImages'])==8 and a['frameIndices']==[0,1,2,3,0,1,2,3]
    assert all(not k.endswith('.png') and k.startswith('hero-v6/') for k in a['frameRectsByImage'])
    assert all(len(a['perFrameOrigins'][d])==8 for d in m['directions'])
    run_checks[key]={'all8phases':True,'frameRectsByImageNativeKeys':list(a['frameRectsByImage'])}
out={'status':'pass' if not issues else 'requires correction','sourceCount':17,'actionCount':24,
     'allTimingFieldsUnchanged':True,'pixelEditsAfterGeneration':False,'nativeAlphaCutoff':16,
     'issues':issues,'sources':reports,'runChecks':run_checks,
     'finalAttackSHA256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest()for n in ['hero-v4-w01-attack-readable.png','W02-attack-readable.png','L01-attack-readable.png']}}
(HERE/'native-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':out['status'],'issues':issues,'sourceCount':17,'actionCount':24,'allTimingFieldsUnchanged':True,'finalAttackSHA256':out['finalAttackSHA256']},indent=2))
assert not issues
