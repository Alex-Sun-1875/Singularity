"""Attach frozen input provenance and common A/B ground/scale; JSON changes only."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
base=HERE.parent
inputs={
 'run-v3.png':'e54ff3aacd7dc5c8937ef317d02ae649fd2950923179f68736cd8f82edcd394c',
 'run-v3-b.png':'67c5c8a81dc5b1b8478fcce5c7a9904cbed605aaf2b6f1efb8e975d54a69ba72',
 'run-bow-v3.png':'58859208ae0a43fd5fa5e6395d6f6b0d63f139e1ffa65a26d93d45d8cb41682d',
 'run-bow-v3-b.png':'eaad0188c1548c71e8511c470a640285a5f875f1672d1f37056180b885f3bc26',
}
for name,sha in inputs.items():
 assert hashlib.sha256((base/name).read_bytes()).hexdigest()==sha,(name,'Frozen source changed')
m=json.loads((HERE/'metadata.json').read_text(encoding='utf-8'))
for family in ['oath','storm','silverstag','astralbow']:
 bow=family in ['silverstag','astralbow']
 ground=[247,244,244,240] if bow else [246,243,242,238]
 height=228.5 if bow else 226.0
 upp=1.5562753036437247/height
 for suffix in ['', '-b']:
  key=family+'-run-v3'+suffix; v=m[key]
  source=('run-bow-v3' if bow else 'run-v3')+suffix+'.png'
  v['measuredSolePoints']=v.get('measuredSolePoints',v['absoluteGroundPoints'])
  v['measuredBodyScaleReference']=v.get('measuredBodyScaleReference',v['bodyScaleReference'])
  v['frozenInputPNG']=str((base/source).relative_to(ROOT)).replace('\\','/')
  v['frozenInputSHA256']=inputs[source]
  v['baseRunAction']='run_bow' if bow else 'run'
  v['runPair']=family+'-run-v3'
  v['runPhases']=[5,6,7,8] if suffix else [1,2,3,4]
  v['fixedGroundByDirection']=dict(zip(['down','right','up','left'],ground))
  v['absoluteGroundPoints']=[];v['perFrameOrigins']=[]
  for idx,(rect,sole) in enumerate(zip(v['perFrameRects'],v['measuredSolePoints'])):
   row=idx//4; x,y,w,h=rect; gx=sole[0];gy=row*256+ground[row]
   end=max(y+h,gy+2);rect[3]=min((row+1)*256,end)-y
   v['absoluteGroundPoints'].append([gx,gy]);v['perFrameOrigins'].append([gx-x,gy-y])
  v['worldUnitsPerPixel']=upp
  v['bodyScaleReference']={'bodyHeightPixels':height,'targetProjectedBodyHeightMetres':1.5562753036437247,'method':'Frozen source run A/B common body scale, not sword/bow bounds. Same scale and fixed directional ground lines across all eight phases; measuredSolePoints retained separately.'}
  v['notes']='Native transparent imagegen weapon-only edit of the frozen corrected A/B. No canvas mirror, no source pixel processing. Modest generation layout drift is registered by measured dense boot support X; fixed source ground Y preserves run bounce. Runtime loop review is required.'
(HERE/'metadata.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'runPNGs':8,'frozenInputSHAVerified':True,'totalMetadataKeys':len(m),'swordRunUPP':1.5562753036437247/226,'bowRunUPP':1.5562753036437247/228.5}))
