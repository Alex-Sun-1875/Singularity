"""Read alpha to measure only the repaired OATH source; never alters image pixels."""
from pathlib import Path
from PIL import Image
import hashlib,json
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUN=ROOT/'src/cocos/assets/resources/equipment/v3'
before=json.loads((HERE/'oath-v3b-before.json').read_text(encoding='utf-8'))
path=HERE/'oath-progression-v3b.png'
im=Image.open(path);a=im.getchannel('A');mask=a.point(lambda v:255 if v>32 else 0)
assert im.size==(1774,887)
assert all(a.getpixel(pt)==0 for pt in [(0,0),(1773,0),(0,886),(1773,886)])
# Native image now contains real full-height alpha<=32 gutters between all five sets.
bounds=[0,369,683,996,1306,1774]
zones=[
 {'head':[185,138,300,261],'chest':[130,261,359,595],'hands':[300,473,360,578],'feet':[161,623,323,794],'offhand':[54,451,177,587]},
 {'head':[482,142,620,241],'chest':[447,252,668,624],'hands':[619,474,675,581],'feet':[486,625,646,795],'offhand':[373,438,468,596]},
 {'head':[815,144,950,241],'chest':[769,251,993,625],'hands':[943,474,993,579],'feet':[801,625,969,796],'offhand':[691,441,786,602]},
 {'head':[1128,123,1252,250],'chest':[1078,253,1303,632],'hands':[1256,472,1306,579],'feet':[1114,626,1281,796],'offhand':[996,439,1097,605]},
 {'head':[1406,85,1635,248],'chest':[1374,248,1661,635],'hands':[1608,472,1662,579],'feet':[1440,625,1623,800],'offhand':[1306,423,1421,622]},
]
def measure(box,pad=2):
 x0,y0,x1,y1=box;bb=mask.crop(tuple(box)).getbbox();assert bb,box
 l=max(x0,x0+bb[0]-pad);t=max(y0,y0+bb[1]-pad);r=min(x1,x0+bb[2]+pad);b=min(y1,y0+bb[3]+pad)
 return[l,t,r-l,b-t]
def measure_glove(box):
 # Detached gauntlets can share a broad search zone with a skirt corner.
 # Measure the largest connected alpha component, without editing PNG pixels.
 x0,y0,x1,y1=box;seen=set();parts=[]
 for yy in range(y0,y1):
  for xx in range(x0,x1):
   if (xx,yy)in seen or not mask.getpixel((xx,yy)):continue
   stack=[(xx,yy)];seen.add((xx,yy));points=[]
   while stack:
    px,py=stack.pop();points.append((px,py))
    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
     nx,ny=px+dx,py+dy
     if x0<=nx<x1 and y0<=ny<y1 and(nx,ny)not in seen and mask.getpixel((nx,ny)):
      seen.add((nx,ny));stack.append((nx,ny))
   parts.append(points)
 points=max(parts,key=len);l=max(x0,min(p[0]for p in points)-1);r=min(x1,max(p[0]for p in points)+2);t=max(y0,min(p[1]for p in points)-1);b=min(y1,max(p[1]for p in points)+2)
 return[l,t,r-l,b-t]
m=json.loads((RUN/'manifest.json').read_text(encoding='utf-8'))
other_before={k:v for k,v in before['manifest']['items'].items() if v['family']!='oath'}
other_current={k:v for k,v in m['items'].items() if v['family']!='oath'}
assert other_before==other_current,'Do not overwrite concurrent changes to other30'
for name,sha in before['otherImages'].items():assert hashlib.sha256((RUN/(name+'-progression.png')).read_bytes()).hexdigest()==sha
sha=hashlib.sha256(path.read_bytes()).hexdigest()
assert hashlib.sha256((RUN/path.name).read_bytes()).hexdigest()==sha
m['images']['oath']={'resource':'equipment/v3/oath-progression-v3b','width':im.width,'height':im.height,'sha256':sha}
measured=[]
for i in range(5):
 key=f'ART_OATH_{i+1}';v=m['items'][key]
 v['rect']=measure([bounds[i],0,bounds[i+1],im.height],3)
 v['slotRects']={slot:(measure_glove(box)if slot=='hands'else measure(box)) for slot,box in zones[i].items()}
 measured.append({'id':key,'rect':v['rect'],'slotRects':v['slotRects']})
for target in [HERE/'manifest.json',RUN/'manifest.json']:
 target.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
changed=[k for k,v in m['items'].items() if v!=before['manifest']['items'][k]]
assert changed==[f'ART_OATH_{i}'for i in range(1,6)],changed
for name,old in before['manifest']['images'].items():
 if name!='oath':assert m['images'][name]==old
for name,oldsha in before['actorImageSHA256'].items():
 assert hashlib.sha256((ROOT/'source-art/characters/2d-concepts/player-actions/equipment-v3'/name).read_bytes()).hexdigest()==oldsha
evidence={'resource':m['images']['oath']['resource'],'sha256':sha,'size':im.size,'sourceRuntimeBytesEqual':True,'alphaExtrema':a.getextrema(),'changedItems':changed,'other30Unchanged':True,'other6PNGUnchanged':True,'actor22PNGUnchanged':True,'threshold':32,'gutters':[{'x':x,'alphaMax':max(a.getpixel((x,y))for y in range(im.height))}for x in [369,683,996,1306]],'measured':measured,'runtimeGalleryReview':'required after next build'}
(HERE/'oath-v3b-verification.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(evidence,ensure_ascii=False))
