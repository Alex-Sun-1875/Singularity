"""Deterministic 2D design measurements, contours and PBR detail maps.

Uses the installed Pillow, SciPy and contourpy. No generated pixels, downloads,
or replacement concept art. Blender owns triangulation, bevels and extrusion.
"""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage as ndi
from scipy.stats import theilslopes
import contourpy
from matplotlib.path import Path as MplPath

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
ROWS=json.loads((BASE/'designs.json').read_text(encoding='utf-8'))
HAMMERS={'W03','DE05'}
REVERSE={'DR3-03','DR4-03','DE06'}
LENGTH={'W01':1.06,'W02':1.08,'W03':.88,'W04':1.12,'W05':1.12,'W06':1.15,
 'W07':1.28,'W08':1.33,'W09':1.35,'W10':1.35,'W11':1.02,'W12':1.68,
 'W13':1.72,'W14':1.68,'DR2-03':.72,'DR3-03':.94,'DR4-03':1.13,'DU1-04':.82,
 'DU2-04':1.28,'DE02':1.4,'DE05':.92,'DE06':1.18,'L01':1.25,'L02':1.36}
(BASE/'prepared').mkdir(exist_ok=True)
(BASE/'textures').mkdir(exist_ok=True)

def major(mask):
    label,n=ndi.label(mask);sizes=np.bincount(label.ravel());sizes[0]=0
    return label==sizes.argmax() if n else mask

def paths(mask):
    # Mature marching squares and Matplotlib's path simplification retain holes.
    a=np.pad(ndi.gaussian_filter(mask.astype(float),.55),2)
    rings=contourpy.contour_generator(z=a,line_type='Separate').lines(.5)
    result=[]
    for ring in rings:
        ring-=2
        if len(ring)<8:continue
        area=abs(np.sum(ring[:-1,0]*ring[1:,1]-ring[1:,0]*ring[:-1,1]))/2
        if area<7:continue
        p=MplPath(ring);p.simplify_threshold=.45
        simplified=p.cleaned(simplify=True).vertices
        # cleaned() appends an ignored STOP vertex, generally (0,0).
        simplified=simplified[:-1]
        if len(simplified)>3:result.append(simplified.tolist())
    return result

def center_x(mask,y):
    yy=int(np.clip(y,0,len(mask)-1));xx=np.where(mask[max(0,yy-3):yy+4].any(axis=0))[0]
    return float(np.median(xx)) if len(xx) else mask.shape[1]/2

def material_maps(image,id,kind,metal_mask,wood_mask):
    rgba=np.asarray(image).astype(float)/255;rgb=rgba[:,:,:3];alpha=rgba[:,:,3]
    # Pad colors outward to avoid dark/transparent bevel seams in mipmaps.
    nearest=ndi.distance_transform_edt(alpha<.25,return_distances=False,return_indices=True)
    padded=rgb[tuple(nearest)]
    h,w=alpha.shape
    albedo=Image.fromarray(np.uint8(np.clip(padded,0,1)*255))
    target_h=1024;target_w=max(128,int(math.ceil(w/h*target_h/64))*64)
    albedo=albedo.resize((target_w,target_h),Image.Resampling.LANCZOS)
    albedo.save(BASE/'textures'/f'design-{id.lower()}-albedo.png')
    luma=.2126*rgb[:,:,0]+.7152*rgb[:,:,1]+.0722*rgb[:,:,2]
    relief=ndi.gaussian_filter(luma,.5)-ndi.gaussian_filter(luma,3)
    dy,dx=np.gradient(relief)
    normal=np.dstack((-dx*1.4,dy*1.4,np.ones_like(dx)))
    normal/=np.linalg.norm(normal,axis=2)[:,:,None]
    # UV front surfaces are projected directly from the original design.
    Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255)).resize((max(128,target_w//2),512),Image.Resampling.LANCZOS).save(BASE/'textures'/f'design-{id.lower()}-normal.png')
    metal=np.where(metal_mask,.88,.02)
    rough=np.where(metal_mask,.32,np.where(wood_mask,.65,.72))
    saturation=rgb.max(axis=2)-rgb.min(axis=2)
    gem=(saturation>.23)&((rgb[:,:,2]>rgb[:,:,0]*1.12)|(rgb[:,:,1]>rgb[:,:,0]*1.25))
    rough[gem]=.2;metal[gem]=.18
    rough=np.clip(rough+relief*.24,.16,.9)
    orm=np.dstack((np.ones_like(rough),rough,metal))
    Image.fromarray(np.uint8(orm*255)).resize((max(128,target_w//2),512),Image.Resampling.LANCZOS).save(BASE/'textures'/f'design-{id.lower()}-orm.png')

records=[]
for row in ROWS:
    id=row['id'];kind='hammer' if id in HAMMERS else row['kind']
    im=Image.open(BASE/row['reference']).convert('RGBA')
    grip=row.get('gripPixel')
    if not grip:
        a=np.array(im)[:,:,3]>100;ys,xs=np.where(major(a));cov=np.cov(np.stack((xs,ys)))
        _,basis=np.linalg.eigh(cov);axis=basis[:,-1]
        # The physical head/blade, rather than the grip, points up after rotation.
        target=np.array([1.,0.]) if id=='W06' else np.array([0.,1. if id in REVERSE else -1.])
        if axis@target<0:axis=-axis
        angle=math.degrees(math.atan2(axis[0],-axis[1]))
        im=im.rotate(angle,resample=Image.Resampling.BICUBIC,expand=True)
        if kind=='bow':
            candidate=im.crop(im.getchannel('A').getbbox());m=np.array(candidate)[:,:,3]>100;hh,ww=m.shape
            yy=np.arange(int(hh*.12),int(hh*.88));valid=np.array([y for y in yy if m[y].any()])
            edges=[np.array([np.where(m[y])[0][side] for y in valid])for side in [0,-1]]
            fits=[theilslopes(edge,valid)for edge in edges]
            errors=[np.median(abs(edge-fit[0]*valid-fit[1]))for edge,fit in zip(edges,fits)]
            which=int(np.argmin(errors));slope=fits[which][0]
            im=candidate.rotate(-math.degrees(math.atan(slope)),resample=Image.Resampling.BICUBIC,expand=True)
            if which==0:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    box=im.getchannel('A').getbbox();im=im.crop(box)
    if grip:grip=[grip[0]-box[0],grip[1]-box[1]]
    a=np.array(im);h,w=a.shape[:2];mask=a[:,:,3]>110
    # Remove very small detached glow/anti-alias remnants, retaining filigree.
    labels,n=ndi.label(mask);sizes=np.bincount(labels.ravel());keep=sizes>=max(8,mask.sum()*.00008);keep[0]=False;mask=keep[labels]
    if not grip:
        gy=h*(.87 if kind=='sword' else .73 if kind=='hammer' else .53 if kind=='bow' else .57)
        line=mask[int(gy)-2:int(gy)+3].any(axis=0);runs,n=ndi.label(line)
        largest=max(range(1,n+1),key=lambda i:(runs==i).sum())
        grip=[float(np.where(runs==largest)[0].mean()),gy]
    mpp=LENGTH[id]/h
    xscale=mpp
    if kind=='bow':
        # Reuse the calibrated native string at x=-.25; the new wooden/metal
        # body reaches the same tip plane while the physical palm stays at zero.
        yy=np.array([y for y in range(int(h*.12),int(h*.88))if mask[y].any()])
        edge=np.array([np.where(mask[y])[0][-1]for y in yy]);fit=theilslopes(edge,yy)
        string_x=float(fit[0]*h*.5+fit[1])
        xscale=mpp
        for y in range(int(h*.10),int(h*.90)):
            sx=int(fit[0]*y+fit[1]);mask[y,max(0,sx-4):min(w,sx+5)]=False
        if id=='W10':mask[int(h*.43):int(h*.58),int(grip[0]+w*.16):]=False
        mask=ndi.binary_closing(mask,iterations=1)
        labels,n=ndi.label(mask);sizes=np.bincount(labels.ravel());keep=sizes>=max(12,mask.sum()*.02);keep[0]=False;mask=keep[labels]
    metal_mask=np.ones((h,w),bool);wood_mask=np.zeros((h,w),bool)
    if kind in ['bow','staff']:
        # Warm wood/brown leather stays dielectric; silver inlays remain metal.
        rgb=a[:,:,:3].astype(float)/255
        warm=(rgb[:,:,0]>rgb[:,:,2]*1.12)&(rgb[:,:,0]>rgb[:,:,1]*1.05)
        greywood=np.zeros_like(mask)
        if id=='W11':greywood[:]=True
        metal_mask=~(warm|greywood);wood_mask=warm|greywood
    else:
        metal_mask[int(grip[1]-.035*h):int(grip[1]+.065*h)]=False
    material_maps(im,id,kind,metal_mask,wood_mask)
    im.save(BASE/'prepared'/f'{id}.png')
    parts=[];guard_y=None;shaft=None
    if kind=='sword':
        widths=mask.sum(axis=1);lo=int(h*.62);hi=int(h*.85)
        guard_y=lo+int(np.argmax(ndi.gaussian_filter1d(widths.astype(float),2)[lo:hi]))
        guard_span=max(7,int(h*.035));grip_end=min(h-4,int(h*.925))
        ranges=[('blade',0,guard_y-4,.0025,.0008,'steel'),('guard',guard_y-guard_span,guard_y+guard_span,.008,.0018,'steel'),('pommel',grip_end,h,.010,.003,'steel')]
        shaft=[guard_y+guard_span,grip_end]
    elif kind=='hammer':
        ranges=[('head',0,int(h*.30),.060 if id=='DE05' else .046,.009,'bronze')]
        shaft=[int(h*.265),int(h*.95)]
        ranges.append(('pommel',int(h*.94),h,.019,.006,'bronze'))
    elif kind=='staff':
        # Curved, round shaft; the ornate head retains its actual holes.
        head_end=int(h*(.24 if id not in ['DR2-03','DU1-04'] else .36))
        ranges=[('head',0,head_end,.014,.003,'wood' if id=='W11' else 'bronze')]
        shaft=[head_end-2,int(h*.96)]
        ranges.append(('ferrule',int(h*.95),h,.018,.004,'steel'))
    else:
        ranges=[('limbs',0,h,.006,.002,'wood')]
    for name,top,bottom,depth,bevel,edge in ranges:
        part=mask.copy();part[:top]=False;part[bottom:]=False
        if kind=='sword' and name=='guard':
            half=max(3,int(w*.075));cx=int(grip[0])
            part[:guard_y-5,max(0,cx-half):min(w,cx+half)]=False
        parts.append({'name':name,'contours':paths(part),'depth':depth,'bevel':bevel,'edge':edge})
    shaft_points=[]
    if shaft:
        for yy in np.linspace(*shaft,60 if kind=='staff' else 25):
            line=mask[max(0,int(yy)-1):min(h,int(yy)+2)].any(axis=0);xx=np.where(line)[0]
            if not len(xx):continue
            # Main shaft crossing closest to the registered grip, excluding
            # side ornaments. Existing SciPy labeling supplies runs.
            runs,n=ndi.label(line);best=min(range(1,n+1),key=lambda i:abs(np.where(runs==i)[0].mean()-grip[0]));xx=np.where(runs==best)[0]
            radius=np.clip((xx[-1]-xx[0]+1)*mpp*.50,.010,.027)
            cx=xx.mean()
            if abs(yy-grip[1])<h*.055:cx=grip[0];radius=min(radius,.019)
            shaft_points.append([float(cx),float(yy),float(radius)])
    records.append({**row,'modelKind':kind,'length':LENGTH[id],'width':w,'height':h,'grip':grip,'metresPerPixel':mpp,'xScale':xscale,'mirrorX':kind=='bow','parts':parts,'shaftPoints':shaft_points,'guardY':guard_y,'gripContract':'Physical rounded grip at origin; existing hand socket/pose unchanged','normalized':'prepared/'+id+'.png'})
(BASE/'prepared/models.json').write_text(json.dumps(records,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
board=Image.new('RGB',(1440,1760),'#252929');d=ImageDraw.Draw(board)
for i,r in enumerate(records):
    im=Image.open(BASE/r['normalized']);im.thumbnail((210,365));x=i%6*240;y=i//6*440;board.paste(im,(x+(240-im.width)//2,y+60),im);d.text((x+8,y+8),r['id']+' '+r['name'],font=font,fill='#ded3b8')
board.save(BASE/'prepared/normalized.jpg',quality=95)
print('PREPARED',len(records),'physical design models')
