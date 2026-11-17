"""Fit smooth shape-preserving curves to the user's red outline, not the old blade."""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.interpolate import PchipInterpolator
from PIL import Image

base=Path(__file__).resolve().parent
source=Path('C:/Users/Alexa/AppData/Local/Temp/codex-clipboard-3a56ac94-71fc-4376-abfc-7046a843b45e.png')
tail=np.array([1268.,1345.]);tip=[2570,589]
# Selected anchors follow the broad red strokes. Tiny pen jitter and the
# duplicated lower stroke are not extra edges in the intended silhouette.
outer_pixels=[[1268,1345],[1480,1352],[1820,1345],[2030,1300],[2262,1250],[2393,1150],[2487,1000],[2552,800],tip]
inner_pixels=[[1268,1345],[1618,1250],[1890,1150],[2122,1050],[2354,900],[2493,750],tip]
def fit(points):
 pixels=np.asarray(points,dtype=float)
 world=np.column_stack(((tail[1]-pixels[:,1])/210.,(pixels[:,0]-tail[0])/225.))
 lengths=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(world,axis=0),axis=1))]
 u=lengths/lengths[-1]
 return PchipInterpolator(u,world,axis=0)(np.linspace(0,1,129)).round(7).tolist()
crop=Image.open(source).crop((1240,550,2600,1385))
crop.save(base/'reference-red-outline.png')
data={
 'coordinates':'fixed local [height y, forward z] traced from the user red outline; rear endpoint is [0,0]',
 'geometryMode':'fixed-sampled-crescent','outerSamples':fit(outer_pixels),'innerSamples':fit(inner_pixels),
 'planeLift':.12,'fixedScale':1.0,'fixedGeometry':True,'fixedWorldHeight':True,
 'pulseInterval':.22,'waveLife':1.02,'visualDuration':1.52,
 'rankWaveCounts':{'1':1,'2':2,'3':2,'4':3,'5':3},
 'camera':{'centre':3.6,'height':5.9},
 'trace':{'sourceCrop':'reference-red-outline.png','sourceCropSha256':hashlib.sha256((base/'reference-red-outline.png').read_bytes()).hexdigest(),
 'tailPixel':tail.tolist(),'tipPixel':tip,'pixelsPerForwardMetre':225,'pixelsPerHeightMetre':210,
 'outerAnchorsPixels':outer_pixels,'innerAnchorsPixels':inner_pixels,'fit':'existing scipy PchipInterpolator over normalized path length; no generated image'},
 'design':'same traced high-front crescent for every wave; no per-wave scale, age-driven reshaping, or terrain-following height changes'
}
(base/'swoosh-profile.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Traced 129 samples per edge; fixed tip height:',data['outerSamples'][-1][0]+data['planeLift'])
