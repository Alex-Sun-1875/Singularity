"""UrhoX UMD2/UANI resource writer retaining skin weights and joint transforms.

Format references: project-local blend_to_urhox.py and Urho3D's MIT-licensed
Graphics/Skeleton.cpp and Graphics/Animation.cpp. No external converter service.
"""
from pathlib import Path
import math
import struct

class Writer:
    def __init__(self): self.data=bytearray()
    def u32(self,n): self.data.extend(struct.pack('<I',int(n)))
    def u8(self,n): self.data.extend(struct.pack('<B',int(n)))
    def floats(self,values):
        values=list(values)
        if not all(math.isfinite(float(x)) for x in values): raise ValueError('nonfinite resource value')
        self.data.extend(struct.pack('<'+'f'*len(values),*values))
    def string(self,value):
        if '\0' in value: raise ValueError('NUL in resource string')
        self.data.extend(value.encode('utf-8')+b'\0')
    def save(self,path):
        path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(self.data)

def write_model(path,model):
    vertices,indices,bones=model['vertices'],model['indices'],model.get('bones',[])
    if not vertices or not indices or len(indices)%3: raise ValueError('non-triangle or empty mesh')
    if len(bones)>255: raise ValueError('too many skin joints')
    if any(i<0 or i>=len(vertices) for i in indices): raise ValueError('index outside vertex buffer')
    elements=[(3,0),(3,1),(2,4)] # position VECTOR3, normal VECTOR3, texcoord VECTOR2
    if bones: elements.extend([(4,6),(5,7)]) # VECTOR4 weights, UBYTE4 joint indices
    w=Writer(); w.data.extend(b'UMD2')
    w.u32(1); w.u32(len(vertices)); w.u32(len(elements))
    for kind,semantic in elements: w.u32(kind|(semantic<<8))
    w.u32(0); w.u32(0)
    for v in vertices:
        w.floats(v['p']); w.floats(v['n']); w.floats(v['uv'])
        if bones:
            influences=sorted([(int(j),float(a)) for j,a in zip(v['j'],v['w']) if a>0],key=lambda pair:pair[1],reverse=True)[:4]
            if not influences: influences=[(0,1)]
            if any(j<0 or j>=len(bones) for j,a in influences): raise ValueError('joint outside skeleton')
            total=sum(a for j,a in influences)
            weights=[a/total for j,a in influences]+[0]*(4-len(influences))
            joints=[j for j,a in influences]+[0]*(4-len(influences))
            w.floats(weights); w.data.extend(bytes(joints))
    size=2 if len(vertices)<65536 else 4
    w.u32(1); w.u32(len(indices)); w.u32(size)
    w.data.extend(struct.pack('<'+('H' if size==2 else 'I')*len(indices),*indices))
    geometries=model.get('geometries') or [dict(start=0,count=len(indices))]
    w.u32(len(geometries))
    for g in geometries:
        if g['start']<0 or g['count']<0 or g['start']+g['count']>len(indices): raise ValueError('invalid draw range')
        w.u32(0); w.u32(1); w.floats([0]); w.u32(0); w.u32(0); w.u32(0)
        w.u32(g['start']); w.u32(g['count'])
    w.u32(0) # morph targets
    w.u32(len(bones))
    for i,b in enumerate(bones):
        if b['parent']<0 or b['parent']>=len(bones): raise ValueError('invalid bone parent')
        w.string(b['name']); w.u32(b['parent'])
        w.floats(b['p']); w.floats(b['q']); w.floats(b['s']); w.floats(b['offset'])
        w.u8(2); w.floats(b.get('bounds',[-0.05,-0.05,-0.05,0.05,0.05,0.05]))
    lo=[min(v['p'][i] for v in vertices) for i in range(3)]
    hi=[max(v['p'][i] for v in vertices) for i in range(3)]
    w.floats(lo+hi)
    for g in geometries:
        w.floats([(lo[i]+hi[i])*0.5 for i in range(3)])
    w.u8(0); w.u32(0); w.u8(0); w.u32(0) # UrhoX optional UV/stroke/collision fields
    w.save(path)

def write_animation(path,name,length,tracks):
    if length<=0 or not tracks: raise ValueError('empty animation')
    w=Writer(); w.data.extend(b'UANI'); w.string(name); w.floats([length]); w.u32(len(tracks))
    for track in tracks:
        keys=track['keys']
        if not keys or any(k['time']<0 or k['time']>length+0.0001 for k in keys): raise ValueError('invalid animation timeline')
        if any(keys[i]['time']>keys[i+1]['time'] for i in range(len(keys)-1)): raise ValueError('unordered animation keys')
        w.string(track['name']); w.u8(7); w.u32(len(keys))
        for key in keys:
            w.floats([key['time']]); w.floats(key['p']); w.floats(key['q']); w.floats(key['s'])
    w.save(path)
