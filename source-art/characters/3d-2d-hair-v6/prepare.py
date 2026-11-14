"""Protect the accepted drawing; construct a silhouette hull with SciPy/Pillow.
Blender performs the final native voxel remesh, smoothing, UV packing and bake.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy import ndimage as nd
BASE=Path(__file__).resolve().parent
image=np.asarray(Image.open(BASE/'hair-four-view.png').convert('RGBA'))
# Physical anchors fitted to the unchanged native head, in metres.
views={
 'front':{'box':[110,8,540,456],'axes':[0,2],'range':[[-.115,.115],[1.585,1.867]],'flip':False},
 'right':{'box':[697,26,1126,470],'axes':[1,2],'range':[[-.120,.148],[1.585,1.867]],'flip':True},
 'back':{'box':[111,645,547,1112],'axes':[0,2],'range':[[-.115,.115],[1.593,1.867]],'flip':True},
 'left':{'box':[726,642,1193,1108],'axes':[1,2],'range':[[-.120,.148],[1.585,1.867]],'flip':False}}
arrays={}
for name,v in views.items():
 x0,y0,x1,y1=v['box'];a=image[y0:y1,x0:x1].copy();mask=a[:,:,3]>90
 # Edge extension provides valid color for small projection disagreements.
 indices=nd.distance_transform_edt(~mask,return_distances=False,return_indices=True)
 rgb=a[indices[0],indices[1],:3]
 Image.fromarray(rgb).save(BASE/(name+'-extended.png'))
 Image.fromarray(a).save(BASE/(name+'.png'))
 lum=np.dot(rgb/255.,[.2126,.7152,.0722]);relief=nd.gaussian_filter(lum,1.6)-nd.gaussian_filter(lum,9)
 arrays[name+'_mask']=nd.gaussian_filter(mask.astype(float),.9).astype(np.float32)
 arrays[name+'_relief']=relief.astype(np.float32)

def project(points,name,field='mask'):
 v=views[name];a=arrays[name+'_'+field];u=(points[...,v['axes'][0]]-v['range'][0][0])/np.ptp(v['range'][0]);t=1-(points[...,2]-v['range'][1][0])/np.ptp(v['range'][1])
 if v['flip']:u=1-u
 return nd.map_coordinates(a,[t*(a.shape[0]-1),u*(a.shape[1]-1)],order=1,mode='constant',cval=0)

step=.002
lo=np.array([-.122,-.128,1.575]);dims=np.array([124,145,151])
grid=np.moveaxis(np.indices(dims),0,-1)*step+lo
front=project(grid,'front');back=project(grid,'back');right=project(grid,'right');left=project(grid,'left')
# Front holes describe the skin in front of the rear hair, not empty tunnels.
fm=arrays['front_mask']>.40;sil=np.zeros_like(fm)
for row in range(len(fm)):
 xs=np.where(fm[row])[0]
 if len(xs):sil[row,xs.min():xs.max()+1]=True
arrays['front_silhouette']=nd.gaussian_filter(sil.astype(float),1).astype(np.float32)
outline=project(grid,'front','silhouette')
side=np.maximum(right,left*.98)
density=np.minimum(np.minimum(outline,back),side)
# Preserve the asymmetric forehead opening only on the front surface.
front_gate=np.clip((.030-grid[...,1])/.025,0,1)
density=np.minimum(density,front*front_gate+1-front_gate)
# Orthographic silhouette intersection alone has square horizontal sections.
# A rounded skull prior removes those corners without replacing the drawing's
# curl outline, face opening or nape length.
rounding=(grid[...,0]/.132)**2+((grid[...,1]-.015)/.163)**2+((grid[...,2]-1.675)/.205)**2
density=np.minimum(density,np.clip((1-rounding)*24+.5,0,1))
occ=nd.gaussian_filter(density,.65)>.48
labels,n=nd.label(occ);sizes=np.bincount(labels.ravel());sizes[0]=0;occ=labels==sizes.argmax()
# Exposed voxel facets only; Blender's native OpenVDB remesh removes stair steps.
verts=[];faces=[]
corners={
 (0,-1):[(0,0,0),(0,0,1),(0,1,1),(0,1,0)],(0,1):[(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
 (1,-1):[(0,0,0),(1,0,0),(1,0,1),(0,0,1)],(1,1):[(0,1,0),(0,1,1),(1,1,1),(1,1,0)],
 (2,-1):[(0,0,0),(0,1,0),(1,1,0),(1,0,0)],(2,1):[(0,0,1),(1,0,1),(1,1,1),(0,1,1)]}
for (axis,direction),corner in corners.items():
 adjacent=np.roll(occ,-direction,axis=axis);edge=np.argwhere(occ&~adjacent)
 xyz=(edge[:,None,:]+np.array(corner)[None,:,:])*step+lo-step/2
 offset=sum(len(x)for x in verts);verts.append(xyz.reshape(-1,3));faces.append(np.arange(len(xyz)*4).reshape(-1,4)+offset)
np.savez_compressed(BASE/'hull.npz',vertices=np.concatenate(verts).astype(np.float32),faces=np.concatenate(faces).astype(np.int32),**arrays)
(BASE/'projection.json').write_text(json.dumps(views,indent=2)+'\n',encoding='utf-8',newline='\n')
print('HULL',sum(occ.ravel()),sum(len(x)for x in faces),'quads',flush=True)
