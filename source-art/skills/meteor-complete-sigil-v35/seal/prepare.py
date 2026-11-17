"""Complete only the obscured reference engraving; retain visible RGB layers.

No model, no dependency download, no production writes. Missing short rear
segments are explicit C1 Bezier continuations of the adjacent reference lines.
Fine measured light ridges return to the 1024 coverage texture; 512 retains halo.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'src/cocos').is_dir())
OLD=ROOT/'source-art/skills/meteor-ignition-glow-v34/seal/reference-r2'
REF=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'
BOX=(216,821,578,981);CX,CY=395.48,901.09;RX,RY=164.29,61.93
N=1024;C=511.5;R=460.
source=np.asarray(Image.open(REF).convert('RGB'),dtype=float)/255
p=source[BOX[1]:BOX[3],BOX[0]:BOX[2]]
background=np.asarray(Image.open(OLD/'estimated-source-stone.png').convert('RGB'),dtype=float)/255
y,x=np.mgrid[BOX[1]:BOX[3],BOX[0]:BOX[2]]
rr=np.hypot((x-CX)/RX,(y-CY)/RY)

def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
def blur(a,sigma):
    r=int(np.ceil(sigma*3));k=np.arange(-r,r+1);k=np.exp(-k*k/(2*sigma*sigma));k/=k.sum()
    def axis(v,ax):
        pad=[(0,0)]*v.ndim;pad[ax]=(r,r)
        return np.apply_along_axis(lambda q:np.convolve(q,k,mode='valid'),ax,np.pad(v,pad,mode='reflect'))
    return axis(axis(a,0),1)
def sample(a,xx,yy):
    xx=np.clip(xx,0,a.shape[1]-1.001);yy=np.clip(yy,0,a.shape[0]-1.001)
    ix=xx.astype(int);iy=yy.astype(int);u=xx-ix;v=yy-iy
    if a.ndim==3:u=u[...,None];v=v[...,None]
    return a[iy,ix]*(1-u)*(1-v)+a[iy,ix+1]*u*(1-v)+a[iy+1,ix]*(1-u)*v+a[iy+1,ix+1]*u*v
def uv(pt):return np.array([C+(pt[0]-CX)/RX*R,C+(pt[1]-CY)/RY*R])

# The expanded silhouette removes the complete actual rock/fire shell. The
# low-frequency replacement below is harmonic, not a polygon-coloured plate.
occ_image=Image.new('L',(BOX[2]-BOX[0],BOX[3]-BOX[1]))
polygon=[(349,817),(478,817),(464,842),(446,861),(414,876),(375,883),(359,877),(350,854)]
ImageDraw.Draw(occ_image).polygon([(a-BOX[0],b-BOX[1]) for a,b in polygon],fill=255)
occ=np.asarray(occ_image.filter(ImageFilter.GaussianBlur(1.35)),dtype=float)/255
edge=1-smooth((rr-1.015)/.025)
excess=np.maximum(0,p-background)
warm=p[...,0]-p[...,2]-(background[...,0]-background[...,2])
excess*=smooth((warm-.003)/.030)[...,None]*edge[...,None]
valid=(1-occ)*edge
near=blur(excess*valid[...,None],2.6)/np.maximum(blur(valid,2.6)[...,None],.001)
ambient=np.minimum(excess,near*.84)
field=blur(ambient*valid[...,None],11)/np.maximum(blur(valid,11)[...,None],.001)
unknown=occ>.015
# Dirichlet boundary values are measured neighbouring diffuse light, with
# line peaks excluded. Jacobi makes the field continuous around all sides.
field[~unknown]=ambient[~unknown]
wx=(RX/RY)**2
for iteration in range(1800):
    average=(wx*(np.roll(field,1,axis=1)+np.roll(field,-1,axis=1))+
             np.roll(field,1,axis=0)+np.roll(field,-1,axis=0))/(2*wx+2)
    field[unknown]=average[unknown]
# Three-source-pixel overlap blends the gradient outside the physical hole.
blend=np.asarray(occ_image.filter(ImageFilter.GaussianBlur(2.5)),dtype=float)/255
clean=excess*(1-blend[...,None])+field*blend[...,None]

# Coherent source-space lines: tangent smoothing removes source-pixel beads,
# while normal-only bounded enhancement preserves curvature and RGB ratios.
height,width=clean.shape[:2];gy,gx=np.mgrid[:height,:width]
signal=blur(clean[...,0]-clean[...,2],.64)
dx=(np.roll(signal,-1,1)-np.roll(signal,1,1))*.5
dy=(np.roll(signal,-1,0)-np.roll(signal,1,0))*.5
dxx=np.roll(signal,-1,1)+np.roll(signal,1,1)-2*signal
dyy=np.roll(signal,-1,0)+np.roll(signal,1,0)-2*signal
dxy=(np.roll(np.roll(signal,-1,0),-1,1)-np.roll(np.roll(signal,-1,0),1,1)-np.roll(np.roll(signal,1,0),-1,1)+np.roll(np.roll(signal,1,0),1,1))*.25
theta=.5*np.arctan2(2*dxy,dxx-dyy)
normx=-np.sin(theta);normy=np.cos(theta);tanx=normy;tany=-normx
ridge=np.maximum(0,clean[...,0]-blur(clean[...,0],.82))
relative=ridge/np.maximum(clean[...,0],.025)
coherent=smooth((relative-.025)/.17)*(1-blend)
tangent=(sample(clean,gx+tanx*.72,gy+tany*.72)+sample(clean,gx-tanx*.72,gy-tany*.72))*.5
smoothed=clean*(1-coherent[...,None]*.32)+tangent*coherent[...,None]*.32
normal=(sample(smoothed,gx+normx*.68,gy+normy*.68)+sample(smoothed,gx-normx*.68,gy-normy*.68))*.5
contrast=smoothed[...,0]-normal[...,0]
factor=np.clip((smoothed[...,0]+contrast*.52)/np.maximum(smoothed[...,0],.005),.80,1.22)
clean=smoothed*(1+(factor-1)*coherent)[...,None]
light0=np.minimum(clean,blur(clean,2.6)*.84)
# A real coherent thin-line peak now keeps 55-70%+ of its measured energy in
# the full-resolution texture. Smooth whole-disc illumination stays in L.
light=light0*(1-coherent[...,None])+np.minimum(light0,clean*.32)*coherent[...,None]
ink=np.maximum(0,clean-light)

paths=[
 {'name':'rear-inner-boundary','points':[(350,855),(381,847),(425,850),(459,860)],'width':1.05,'anchors':[(345,858),(466,863)]},
 {'name':'rear-inner-companion','points':[(350,856.8),(381,848.8),(425,851.8),(459,861.8)],'width':.70,'anchors':[(345,858),(466,863)]},
 {'name':'central-S-hidden-root','points':[(397,866.4),(401,868.4),(411.8,873.1),(407.8,881.5)],'width':1.0,'anchors':[(409,884),(400,891)]},
 {'name':'left-return-hidden-tip','points':[(349,875),(370,867),(389.05,861.88),(401.05,869.53)],'width':1.1,'anchors':[(345,877),(352,875)]},
 {'name':'right-return-hidden-tip','points':[(443,856.2),(458,858.5),(474,863.2),(482,869.2)],'width':.9,'anchors':[(475,866),(486,872)]},
 {'name':'rear-band-flow','points':[(349,850),(362,845),(374,845),(385,849),(395,852.6),(409,850),(414,847),(420,844),(442,848),(461,856)],'width':1.05,'anchors':[(345,850),(468,860)]},
 {'name':'rear-band-companion','points':[(350,851.7),(364,847),(374,847.2),(384,850.5),(395,854),(410,851.6),(415.3,848.8),(421,846.1),(443,850.1),(462,858)],'width':.65,'anchors':[(345,853),(468,864)]},
]
def bezier(points):
    pts=np.array(points,dtype=float);out=[]
    for i in range(0,len(pts)-1,3):
        q=pts[i:i+4];t=np.linspace(0,1,240)[:,None]
        out.extend((1-t)**3*q[0]+3*(1-t)**2*t*q[1]+3*(1-t)*t*t*q[2]+t**3*q[3])
    return np.asarray(out)

# Repair is rasterised in SOURCE SPACE at six samples per source pixel. Each
# cross-section carries neighbouring measured RGB, including its gold core,
# warm body and local halo, rather than a flat vector stroke colour.
SS=6;HH=height*SS;WW=width*SS
new_ink=np.zeros((HH,WW,3),dtype=np.float32)
new_halo=np.zeros_like(new_ink)
profile_n=np.linspace(-2.8,2.8,81)
def measured_profile(anchor,tangent):
    tangent=np.asarray(tangent,float);tangent/=max(.001,np.linalg.norm(tangent))
    normal=np.array([-tangent[1],tangent[0]])
    anchor=np.asarray(anchor,float)-np.array(BOX[:2])
    seek=np.linspace(-2.4,2.4,61)
    samples=sample(excess,anchor[0]+normal[0]*seek,anchor[1]+normal[1]*seek)
    validity=1-sample(occ,anchor[0]+normal[0]*seek,anchor[1]+normal[1]*seek)
    score=(samples[:,0]-samples[:,2])*validity
    centre=anchor+normal*seek[np.argmax(score)]
    result_k=0;result_l=0
    for shift in (-.45,0,.45):
        xx=centre[0]+normal[0]*profile_n+tangent[0]*shift
        yy=centre[1]+normal[1]*profile_n+tangent[1]*shift
        result_k+=sample(ink,xx,yy)/3
        result_l+=sample(light,xx,yy)/3
    baseline=(result_l[:5].mean(axis=0)+result_l[-5:].mean(axis=0))*.5
    result_l=np.maximum(0,result_l-baseline)
    return result_k,result_l

def render_curve(curve,width_scale,anchors):
    global new_ink,new_halo
    pk0,pl0=measured_profile(anchors[0],curve[2]-curve[0])
    pk1,pl1=measured_profile(anchors[1],curve[-1]-curve[-3])
    points=(curve-np.array(BOX[:2]))*SS
    # Profile scales derive from the source's own stroke, with a bounded
    # 15% normal compression for a distinct core at the native output size.
    scale=max(.55,width_scale)*.85
    for i in range(len(points)-1):
        a,b=points[i],points[i+1];v=b-a;length2=float(v@v)
        if length2<1e-6:continue
        margin=2.85*SS*scale
        x0=max(0,int(np.floor(min(a[0],b[0])-margin)));x1=min(WW,int(np.ceil(max(a[0],b[0])+margin))+1)
        y0=max(0,int(np.floor(min(a[1],b[1])-margin)));y1=min(HH,int(np.ceil(max(a[1],b[1])+margin))+1)
        yy,xx=np.mgrid[y0:y1,x0:x1];t=np.clip(((xx-a[0])*v[0]+(yy-a[1])*v[1])/length2,0,1)
        footx=a[0]+t*v[0];footy=a[1]+t*v[1]
        distance=np.hypot(xx-footx,yy-footy)/SS/scale
        sign=np.sign((xx-a[0])*(-v[1])+(yy-a[1])*v[0]);normal=distance*sign
        progress=(i+t)/(len(points)-1)
        weights=(normal-profile_n[0])/(profile_n[-1]-profile_n[0])*(len(profile_n)-1)
        idx=np.clip(weights.astype(int),0,len(profile_n)-2);f=np.clip(weights-idx,0,1)
        def values(q0,q1):
            l0=q0[idx]*(1-f[...,None])+q0[idx+1]*f[...,None]
            l1=q1[idx]*(1-f[...,None])+q1[idx+1]*f[...,None]
            return (l0*(1-progress[...,None])+l1*progress[...,None])*(distance<2.8)[...,None]
        new_ink[y0:y1,x0:x1]=np.maximum(new_ink[y0:y1,x0:x1],values(pk0,pk1))
        new_halo[y0:y1,x0:x1]=np.maximum(new_halo[y0:y1,x0:x1],values(pl0,pl1))

for path in paths:render_curve(bezier(path['points']),path['width'],path['anchors'])
for radius,anchors in [(1.,[(345,842),(468,847)]),(.974,[(345,844),(468,850)])]:
    angle=np.linspace(0,2*np.pi,1250)
    curve=np.stack([CX+RX*radius*np.cos(angle),CY+RY*radius*np.sin(angle)],axis=-1)
    render_curve(curve,.8,anchors)

def reduce(a):
    return np.stack([np.asarray(Image.fromarray(a[...,i],'F').resize((width,height),Image.Resampling.LANCZOS)) for i in range(3)],axis=-1)
repair_k=np.maximum(0,reduce(new_ink));repair_l=np.maximum(0,reduce(new_halo))
# Only the invalid region receives repaired geometry; a smooth overlap shares
# endpoint profiles with the original line, with no hard max(L,newHalo) seam.
ink=ink*(1-blend[...,None])+repair_k*blend[...,None]
light=light+blur(repair_l,.42)*blend[...,None]*.75

oy,ox=np.mgrid[:N,:N];nu=(ox-C)/R;nv=(oy-C)/R;rad=np.hypot(nu,nv)
sx=CX+nu*RX-BOX[0];sy=CY+nv*RY-BOX[1]
clip=1-smooth((rad-1.017)/.025)
b=sample(background,sx,sy);missing=sample(blend,sx,sy)
# Bicubic interpolation (bounded at zero) reconstructs the source line edges
# in one affine pass; no second target-space unsharp amplifies pixel beads.
def cubic_sample(a,xx,yy):
    xx=np.clip(xx,1,a.shape[1]-2.001);yy=np.clip(yy,1,a.shape[0]-2.001)
    ix=xx.astype(int);iy=yy.astype(int);u=xx-ix;v=yy-iy
    def weight(t):
        t=np.abs(t);return np.where(t<=1,1.5*t**3-2.5*t**2+1,np.where(t<2,-.5*t**3+2.5*t**2-4*t+2,0))
    out=np.zeros((*xx.shape,3),float)
    for j in range(-1,3):
        for i in range(-1,3):out+=a[iy+j,ix+i]*(weight(u-i)*weight(v-j))[...,None]
    return np.maximum(out,0)
k=cubic_sample(ink,sx,sy)*clip[...,None]
l=sample(light,sx,sy)*clip[...,None]
coverage=np.clip(np.max(k/np.maximum(1-b,.2),axis=-1)*1.22,0,.97)
fg=np.clip(b+k/np.maximum(coverage[...,None],1e-7),0,1);fg[coverage<.001]=0
main=Image.fromarray(np.uint8(np.clip(np.concatenate([fg,coverage[...,None]],axis=-1),0,1)*255+.5),'RGBA')
light_rgba=np.concatenate([l,np.clip(l.max(axis=-1)/.18,0,1)[...,None]],axis=-1)
light_image=Image.fromarray(np.uint8(np.clip(light_rgba,0,1)*255+.5),'RGBA').resize((512,512),Image.Resampling.LANCZOS)
main_path=HERE/'fire-meteor-seal-colour-v35.png';main.save(main_path,optimize=True)
light_path=HERE/'fire-meteor-seal-light-v35.png';light_image.save(light_path,optimize=True)

# Reconstruct exactly the shader from the encoded images. The complete seal
# is shown on native-like dark green-grey ground, and reprojected to the SAME
# original ellipse. The meteor is NOT overlaid: the repaired rear is visible.
aa=np.asarray(main,float)/255;ll=np.asarray(light_image.resize((N,N),Image.Resampling.BILINEAR),float)/255
alpha=aa[...,3]+ll[...,3]*.006*(1-aa[...,3]);pm=aa[...,:3]*aa[...,3,None]+ll[...,:3]
ground=np.empty((N,N,3));ground[:]=np.array([39,45,42])/255
for row in range(0,N,64):ground[row:row+1]=np.array([49,55,51])/255
for col in range(0,N,64):ground[:,col:col+1]=np.array([49,55,51])/255
flat=pm+ground*(1-alpha[...,None])
px=(x-CX)/RX*R+C;py=(y-CY)/RY*R+C
projected=sample(pm,px,py)+np.array([39,45,42])/255*(1-sample(alpha,px,py)[...,None])
original=p.copy()
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
canvas=Image.new('RGB',(1512,1040),'#202420');d=ImageDraw.Draw(canvas)
d.text((18,12),'v35 后侧雕纹补齐 / 1024清晰线芯 + 512独立柔光（材质计算，非实景）',font=font,fill='#eec28e')
for title,data,at in [('原稿同角度：陨石遮住后部',(original),(18,76)),('v35同角度：完整后圈与回旋根部，无陨石遮挡',(projected),(762,76))]:
    d.text((at[0],48),title,font=small,fill='#e4c5a0')
    im=Image.fromarray(np.uint8(np.clip(data,0,1)*255+.5),'RGB').resize((724,320),Image.Resampling.LANCZOS);canvas.paste(im,at)
d.text((18,419),'完整正视：保留原可见纹样，后侧局部续接',font=small,fill='#e4c5a0')
d.text((762,419),'后侧放大：双圈、圈间曲纹、内环与三回旋根已连接',font=small,fill='#e4c5a0')
im=Image.fromarray(np.uint8(np.clip(flat,0,1)*255+.5),'RGB')
canvas.paste(im.resize((580,580),Image.Resampling.LANCZOS),(80,450))
canvas.paste(im.crop((285,30,780,525)).resize((580,580),Image.Resampling.LANCZOS),(832,450))
preview=HERE/'seal-v35-complete-reference-and-front-coherent.jpg';canvas.save(preview,quality=96,subsampling=0)
Image.fromarray(np.uint8(np.clip(flat,0,1)*255+.5),'RGB').save(HERE/'seal-v35-material-front.png')
Image.fromarray(np.uint8(missing*255+.5),'L').save(HERE/'repair-only-mask.png')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
record={'revision':'v35-complete-rear-original-rgb','source':str(REF.relative_to(ROOT)),'sourceSha256':sha(REF),'base':str(OLD.relative_to(ROOT)),
 'sourceCrop':BOX,'deprojection':{'centre':[CX,CY],'radii':[RX,RY],'targetCentre':[C,C],'targetRadius':R,'orientation':'top=far, bottom=near; no UV/range changes'},
 'visibleReference':'Original pixels and per-pixel colour variations kept; the accurate local meteor silhouette also recovers lines discarded by the older broad rectangle matte.',
 'repair':{'scope':'Only meteor silhouette, not an entire rear quadrant. C1 local Bezier continuations follow the visible inner-ring/three-return endpoints; outer rims completed as true circles only where hidden. No mirror donor, no front-diamond duplication.','meteorPolygonSource':polygon,'lightFill':'1800 Jacobi iterations, measured neighbouring diffuse Dirichlet boundary; source 2.5px soft overlap; original light colour, no average-colour triangle','paths':paths},
 'clarity':'Source-space .82px relative-ridge support allocates coherent fine peaks primarily to 1024 coverage (L cap32%); .72px tangential smoothing and .68px normal-only enhancement bounded .80..1.22 maintain original RGB ratios, followed by one bicubic affine reconstruction. No target-space unsharp. Missing line cross-sections use actual neighbouring RGB profiles at SS6, not uniform vector colour.',
 'resources':[{'name':main_path.name,'size':[1024,1024],'role':'RGB original-colour decontaminated engraving foreground, A optical coverage','sha256':sha(main_path),'gpuBytes':4194304},{'name':light_path.name,'size':[512,512],'role':'RGB measured varying warm light/halo energy, A only 0.006 support absorption','sha256':sha(light_path),'gpuBytes':1048576}],
 'totalGpuBytes':5242880,'formula':'coverage=colour.a*fade; alpha=coverage+light.a*.006*fade*(1-coverage); premul=colour.rgb*coverage+light.rgb*fade; blend ONE/ONE_MINUS_SRC_ALPHA. No fixed recolouring or global gain.',
 'preview':preview.name,'previewDeclaration':'Exact encoded two-texture shader calculation on dark green-grey ground, and SAME source ellipse projection. Not native Cocos or TapTap evidence.',
 'review':{'local':'Pending inspection of the one complete candidate','production':'Not published','native':'Pending root standard build/capture','generation':'None; deterministic NumPy/Pillow pixel processing and bounded local hidden-segment repair'}}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'preview':str(preview),'assets':record['resources']},ensure_ascii=False))
