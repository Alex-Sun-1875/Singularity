"""Pose-aware appearance adapters using existing Pillow/SciPy/ICC-Lab tools."""
from pathlib import Path
import importlib.util
import sys
from functools import lru_cache
sys.dont_write_bytecode=True
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import prepare

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

palette=load('unified_palette',HERE.parent/'local-qwen21-consistency-v2/palette/apply_palette.py')
old_body=load('unified_body_source',HERE.parent/'local-qwen21-consistency-v2/body/prepare-body.py')
Y,X=np.mgrid[:768,:512]

def hair(image,record=None):
    a=np.asarray(image);rgb=a[...,:3].astype(float)
    seed=(a[...,3]>=220)&(rgb.min(-1)>105)&(rgb.max(-1)-rgb.min(-1)<38)
    seed=ndi.binary_opening(seed,iterations=2)
    seed=ndi.binary_closing(seed,iterations=2)
    lab,n=ndi.label(seed)
    candidates=[]
    for i,sl in enumerate(ndi.find_objects(lab),1):
        if sl is None:continue
        yy,xx=sl;h=yy.stop-yy.start;w=xx.stop-xx.start;area=int((lab[sl]==i).sum())
        limit=190 if (record or {}).get('allow_large_head') else 120
        if area<100 or w<30 or h<16 or max(w/h,h/w)>2.7 or w>limit or h>limit:continue
        # Hair is a compact bright neutral area. Thin blades/shaft glints and
        # tiny white cuffs are rejected by opening, compactness and area.
        brightness=float(rgb[sl][lab[sl]==i].mean())
        keys=' '.join(v['action'] for v in (record or {}).get('refs',[]))
        relaxed=any(k in keys for k in ('death','dodge','hit'))
        if not relaxed and (yy.start+yy.stop)/2>280:continue
        prior=1 if relaxed else float(np.exp(-(((yy.start+yy.stop)/2-140)/75)**2))
        texture=float(rgb[sl][lab[sl]==i].mean(-1).std())
        score=area*(.8+.2*area/(w*h))*(brightness/145)**(2 if relaxed else 8)*prior*np.clip(texture/18,.35,2)**2
        candidates.append((score,i,[xx.start,yy.start,xx.stop,yy.stop],area))
    if not candidates:raise ValueError('No stable silver-hair component')
    _,i,box,area=max(candidates)
    return {'box':box,'area':area,'center':[(box[0]+box[2])/2,(box[1]+box[3])/2]},lab==i

def fix_locations():
    import json
    inv=json.loads((HERE/'inventory.json').read_text());old=json.loads((HERE/'head-locations.json').read_text())
    locations={(r['image'],r['index']):r for r in old['frames']};sheets={};count=0;errors=[]
    for r in inv['frames']:
        info=locations[(r['image'],r['index'])]['hair'];b=info['box']
        acting=any(any(k in v['action'] for k in ('hit','death','dodge')) for v in r['refs'])
        if acting or info['center'][1]>220 or b[2]-b[0]<40 or info['area']<250 or max(b[2]-b[0],b[3]-b[1])>105:
            if r['image'] not in sheets:sheets[r['image']]=Image.open(prepare.ACTOR/r['image']).convert('RGBA')
            try:info,_=hair(prepare.canvas(r,sheets),r);locations[(r['image'],r['index'])]['hair']=info;count+=1
            except ValueError:errors.append((r['image'],r['index']))
    old['frames']=list(locations.values());old['locationRefinements']=count;old['refinementErrors']=errors
    (HERE/'head-locations.json').write_text(json.dumps(old,indent=2),encoding='utf-8')
    print({'refined':count,'errors':errors},flush=True)

def acting_locations():
    import json
    inv=json.loads((HERE/'inventory.json').read_text());data=json.loads((HERE/'head-locations.json').read_text())
    locations={(r['image'],r['index']):r for r in data['frames']};images={};count=0
    for r in inv['frames']:
        if not any(any(k in v['action'] for k in ('hit','death','dodge')) for v in r['refs']):continue
        if r['image'] not in images:images[r['image']]=Image.open(prepare.ACTOR/r['image']).convert('RGBA')
        x,y,w,h=r['rect'];s=r['scale'];crop=images[r['image']].crop((x,y,x+w,y+h))
        full=crop.convert('RGBa').resize((int(round(w*s)),int(round(h*s))),Image.Resampling.BICUBIC).convert('RGBA')
        info,_=hair(full,r)
        tx,ty=256-r['origin'][0]*s,712-r['origin'][1]*s
        info['box']=[info['box'][0]+tx,info['box'][1]+ty,info['box'][2]+tx,info['box'][3]+ty]
        info['center']=[info['center'][0]+tx,info['center'][1]+ty]
        locations[(r['image'],r['index'])]['hair']=info;count+=1
    data['frames']=list(locations.values());data['actingFullCropLocations']=count
    (HERE/'head-locations.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print('Full-crop acting heads located:',count)

def reviewed_large_acting_heads():
    import json
    inv=json.loads((HERE/'inventory.json').read_text());data=json.loads((HERE/'head-locations.json').read_text())
    review=json.loads((HERE/'acting-head-review-index.json').read_text());chosen={26,28,29,48,57,59}
    keys={(r['image'],r['index']) for r in review if r['number'] in chosen}
    locations={(r['image'],r['index']):r for r in data['frames']};images={};rows=[]
    for r in inv['frames']:
        if (r['image'],r['index']) not in keys:continue
        if r['image'] not in images:images[r['image']]=Image.open(prepare.ACTOR/r['image']).convert('RGBA')
        x,y,w,h=r['rect'];s=r['scale'];crop=images[r['image']].crop((x,y,x+w,y+h))
        full=crop.convert('RGBa').resize((round(w*s),round(h*s)),Image.Resampling.BICUBIC).convert('RGBA')
        search=dict(r,allow_large_head=True);info,_=hair(full,search)
        tx,ty=256-r['origin'][0]*s,712-r['origin'][1]*s
        info['box']=[info['box'][0]+tx,info['box'][1]+ty,info['box'][2]+tx,info['box'][3]+ty]
        info['center']=[info['center'][0]+tx,info['center'][1]+ty];info['largeComponentReviewed']=True
        locations[(r['image'],r['index'])]['hair']=info
        rows.append(dict(image=r['image'],index=r['index'],hair=info))
    data['frames']=list(locations.values());data['largeActingHeadReviews']=rows
    (HERE/'head-locations.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(rows))

def reviewed_nonbow_head_rois():
    import json
    inv=json.loads((HERE/'inventory.json').read_text());data=json.loads((HERE/'head-locations.json').read_text())
    name='face-v1/hero-v6/hero-v4-hit-death-readable.png'
    # Visually reviewed normalized FULL-crop coordinates, not body-window
    # coordinates. Restricting the search separates neutral skin/collar bridges.
    rois={0:[75,0,200,100],3:[0,0,115,105],7:[0,0,120,95]}
    locations={(r['image'],r['index']):r for r in data['frames']};sheet=Image.open(prepare.ACTOR/name).convert('RGBA')
    for r in inv['frames']:
        if r['image']!=name or r['index'] not in rois:continue
        x,y,w,h=r['rect'];s=r['scale'];full=sheet.crop((x,y,x+w,y+h)).convert('RGBa').resize((round(w*s),round(h*s)),Image.Resampling.BICUBIC).convert('RGBA')
        roi=rois[r['index']];info,_=hair(full.crop(roi),dict(r,allow_large_head=True))
        tx,ty=256-r['origin'][0]*s+roi[0],712-r['origin'][1]*s+roi[1]
        info['box']=[info['box'][0]+tx,info['box'][1]+ty,info['box'][2]+tx,info['box'][3]+ty]
        info['center']=[info['center'][0]+tx,info['center'][1]+ty];info['reviewedFullCropROI']=roi
        locations[(name,r['index'])]['hair']=info
    data['frames']=list(locations.values());data['reviewedNonbowHeadROIs']=rois
    (HERE/'head-locations.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print('Applied three visually reviewed head search ROIs.')

def boxmask(box):
    im=Image.new('L',(512,768));ImageDraw.Draw(im).rectangle(box,fill=255);return np.asarray(im)>0

@lru_cache(maxsize=4)
def canonical(direction):
    im=Image.open(HERE/'references'/f'identity-{direction}.png').convert('RGBA')
    info,_=hair(im)
    if direction in ('down','up'):
        poly=old_body.SPECS['front' if direction=='down' else 'back']['source_head']
        mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(poly,fill=255)
    else:
        x0,y0,x1,y1=info['box']
        # The standing source already has the requested head and neck. Crop
        # only above its collar; nearby back-carried pommel is excluded.
        mask=Image.new('L',im.size)
        cx=(x0+x1)/2
        if direction=='right':
            poly=[(x0-4,y0-4),(x1+5,y0-4),(x1+24,y1+14),(x1+17,y1+34),(cx+22,194),(cx-20,194),(x0-3,y1+16)]
        else:
            poly=[(x0-5,y0-4),(x1+4,y0-4),(x1+3,y1+16),(cx+20,194),(cx-22,194),(x0-24,y1+34),(x0-24,y1+14)]
        ImageDraw.Draw(mask).polygon(poly,fill=255)
    a=np.asarray(im).copy();a[np.asarray(mask)==0]=0
    return Image.fromarray(a),info


def retarget_head(image,record,info):
    """Use standing head pixels for upright poses; retain acting tilt otherwise."""
    direction=record['direction'];keys=[v['action'] for v in record['refs']]
    if any(k in ('explore_idle_W01','explore_walk_W01','explore_run_W01') for k in keys):
        return image.copy(),{'method':'accepted standing-derived W01 head retained','applied':False}
    template,reference=canonical(direction)
    x0,y0,x1,y1=info['box'];cx=(x0+x1)/2;hh=y1-y0
    factor={'down':.85,'right':.65,'up':.40,'left':.65}[direction]
    neck=float(y1+hh*factor)
    neck=min(neck,y1+55)
    poly=[(x0-8,y0-6),(x1+8,y0-6),(x1+17,y1+15),
          (cx+20,neck),(cx-20,neck),(x0-17,y1+15)]
    source_mask=Image.new('L',image.size);ImageDraw.Draw(source_mask).polygon(poly,fill=255)
    mask=np.asarray(source_mask)>0
    original=np.asarray(image);rgb=original[...,:3].astype(int)
    # Original gold pommels/collar hardware near the hair are not head pixels.
    gold=(rgb[...,0]-rgb[...,1]>27)&(rgb[...,1]-rgb[...,2]>24)&(rgb[...,0]>105)
    mask&=~ndi.binary_dilation(gold,iterations=1)
    base=original.copy();base[mask]=0
    acting=any(any(word in k for word in ('death','hit','dodge')) for k in keys)
    if acting:
        # A straight standing head would erase a hit/death/dodge expression and
        # tilt. Size the original acting head around its own neck instead.
        targetarea=(reference['box'][2]-reference['box'][0])*(reference['box'][3]-reference['box'][1])
        scale=float(np.clip(np.sqrt(targetarea/max((x1-x0)*(y1-y0),1)),.55 if info.get('largeComponentReviewed') else .72,1.0))
        # Acting heads can lie sideways. Locate their neck toward the nearest
        # wine-cloth torso rather than assuming that the neck is always below.
        hc=np.asarray(info['center'],float)
        rr,gg,bb=np.moveaxis(rgb,-1,0);distance=(X-hc[0])**2+(Y-hc[1])**2
        torso=(rr>gg+8)&(rr>bb+10)&(gg-bb<14)&(original[...,3]>200)&(distance>25**2)&(distance<190**2)
        if torso.sum()>30:
            weights=1/(distance[torso]+100);point=np.array([(X[torso]*weights).sum(),(Y[torso]*weights).sum()])/weights.sum()
            vector=point-hc;vector/=max(np.linalg.norm(vector),1)
        else:vector=np.array([0.,1.])
        along=(X-hc[0])*vector[0]+(Y-hc[1])*vector[1]
        across=(X-hc[0])*(-vector[1])+(Y-hc[1])*vector[0]
        extent=max(x1-x0,y1-y0);neckdist=.72*extent+12
        neckpoint=hc+vector*neckdist
        mask=(((along-10)/(neckdist+8))**2+(across/(.60*extent+7))**2<=1)&~ndi.binary_dilation(gold,iterations=1)
        base=original.copy();base[mask]=0
        nx,ny=neckpoint
        layer=original.copy();layer[~mask]=0
        affine=(1/scale,0,nx-nx/scale,0,1/scale,ny-ny/scale)
        moved=Image.fromarray(layer).convert('RGBa').transform(image.size,Image.Transform.AFFINE,
            affine,Image.Resampling.BICUBIC).convert('RGBA')
        method='own acting head uniformly sized around original neck; tilt and expression retained'
    else:
        source_neck=194 if direction!='up' else 181
        dx=int(round(cx-reference['center'][0]));dy=int(round(neck-source_neck))
        moved=Image.new('RGBA',image.size);moved.alpha_composite(template,(dx,dy))
        method='same-direction accepted standing head at 1:1; neck-aligned integer translation'
        scale=1.0
    result=Image.alpha_composite(Image.fromarray(base),moved)
    # Preserve original neck/collar progressively below the new jaw. This
    # changes no torso, hands or equipment pixels away from the head envelope.
    out=np.asarray(result).copy();start=int(round(neck-8));end=int(round(neck+4))
    blend=(np.clip((along-(neckdist-12))/15,0,1)*mask) if acting else np.clip((Y-start)/max(end-start,1),0,1)*boxmask((cx-24,start,cx+24,end+2))
    weight=blend[...,None]
    out=np.uint8(np.clip(np.rint(out*(1-weight)+original*weight),0,255))
    out[gold]=original[gold]
    # New disconnected heads are rejected, using source acting pixels as the
    # conservative fallback rather than inventing an unseen neck on every phase.
    labels,_=ndi.label(out[...,3]>=64);sizes=np.bincount(labels.ravel());sizes[0]=0
    head_region=(np.asarray(moved)[...,3]>=128)&((along<neckdist-12) if acting else (Y<neck-10))
    connected=float((labels[head_region]==sizes.argmax()).mean()) if head_region.any() else 0
    if connected<.65:
        return image.copy(),{'applied':False,'method':'source pose retained: neck connectivity guard','connection':connected}
    record['head_protection_mask']=Image.fromarray(np.uint8(ndi.binary_dilation(mask|(np.asarray(moved)[...,3]>0),iterations=3))*255)
    return Image.fromarray(out),{'applied':True,'method':method,'scale':scale,'original_neck_xy':[cx,neck],
        'acting_neck_anchor_xy':[float(nx),float(ny)] if acting else None,
        'head_to_body_connection_fraction':connected,'standing_scale_modified':False}


def material_masks(image, info=None, extra_protect=None):
    """Colour-gated cloth only; no upright-pose row cutoffs for lying frames."""
    a=np.asarray(image);rgb=a[...,:3].astype(float);r,g,b=np.moveaxis(rgb,-1,0)
    lab=palette.lab8(image);l,ca,cb=np.moveaxis(lab,-1,0)
    sat=np.asarray(image.convert('RGB').convert('HSV'))[...,1]
    opaque=ndi.binary_erosion(a[...,3]>=245,iterations=4)
    warm=((g-b>7)&(r-g>4))|((cb>10)&(ca>2))
    protected=~opaque|ndi.binary_dilation(warm,iterations=3)
    # Preserve thin external weapon silhouettes and warm skin/leather. Bright
    # metal over the torso is also outside the cloth luminance gates below.
    broad=ndi.binary_opening(a[...,3]>=32,iterations=6)
    thin=(a[...,3]>0)&~broad
    protected|=ndi.binary_dilation(thin,iterations=2)
    hsv=np.asarray(image.convert('RGB').convert('HSV'))
    skin=(hsv[...,0]>=11)&(hsv[...,0]<=35)&(hsv[...,1]>35)&(hsv[...,2]>65)
    protected|=ndi.binary_dilation(skin,iterations=2)
    if extra_protect is not None:protected|=np.asarray(extra_protect)>0
    info=info or hair(image)[0]
    x0,y0,x1,y1=info['box']
    protected|=boxmask((x0-15,y0-8,x1+20,y1+55))
    wine=(ca>=7)&(ca<=35)&(cb>=-5)&(cb<=10)&(r>g+7)&(r>b+9)&(g-b<10)&(l>20)&(l<190)&(sat>35)
    neutral=(ca>=-5)&(ca<=8)&(cb>=-10)&(cb<=7)&(sat<80)&(l>20)&(l<173)
    # Cold charcoal fabric vs neutral gray fabric. Both follow the requested
    # dark attack palette; gradients/high-frequency source weave are retained.
    cold=cb < -1
    gates={'wine_vest':wine,'charcoal_sleeves':neutral&cold,'dark_gray_trousers':neutral&~cold}
    masks={}
    for k,m in gates.items():
        m&=~protected
        labels,_=ndi.label(m);counts=np.bincount(labels.ravel());valid=counts>=16;valid[0]=False
        m&=valid[labels]
        masks[k]=Image.fromarray(np.uint8(np.clip(ndi.distance_transform_edt(m)/2,0,1)*255))
    return masks,protected


def grade(image, reference, info=None, extra_protect=None):
    masks,protected=material_masks(image,info,extra_protect)
    if not hasattr(reference,'_unified_palette_stats'):
        refs,_=material_masks(reference);target=palette.lab8(reference)
        targetlow=ndi.gaussian_filter(target[...,0],1.2);stats={}
        for k,mask in refs.items():
            dst=np.asarray(mask)>=220
            stats[k]=None if dst.sum()<40 else (np.percentile(targetlow[dst],[25,50,75]),np.median(target[dst,1:],0))
        reference._unified_palette_stats=stats
    values=palette.lab8(image);low=ndi.gaussian_filter(values[...,0],1.2)
    result=image.copy();report={}
    for k,mask in masks.items():
        src=np.asarray(mask)>=220;targetstats=reference._unified_palette_stats[k]
        if src.sum()<40 or targetstats is None:
            report[k]={'status':'sparse-preserved','pixels':int(src.sum())};continue
        sq=np.percentile(low[src],[25,50,75]);tq,targetchroma=targetstats
        scale=float(np.clip((tq[2]-tq[0])/max(sq[2]-sq[0],1),.9,1.08))
        delta=float(tq[1]-scale*sq[1])
        chroma=np.clip(targetchroma-np.median(values[src,1:],0),-8,8)
        corrected=values.copy();corrected[...,0]+=np.clip(scale*low+delta-low,-45,45)
        corrected[...,1:]+=chroma
        color=palette.from_lab8(corrected).convert('RGBA');color.putalpha(image.getchannel('A'))
        result=Image.composite(color,result,mask)
        report[k]={'status':'graded','pixels':int(src.sum()),'L_offset':delta,'L_scale':scale,'ab_delta':chroma.tolist()}
    result.putalpha(image.getchannel('A'))
    assert np.array_equal(np.asarray(result)[protected],np.asarray(image)[protected])
    return result,report


def prepare_qwen():
    import json
    folder=HERE/'qwen-inputs';folder.mkdir(exist_ok=True)
    guide=Image.new('RGBA',(512,768));ref=guide.copy();mask=Image.new('L',guide.size)
    for i,d in enumerate(prepare.DIRECTIONS):
        source=Image.open(HERE/'references'/f'identity-{d}.png').convert('RGBA')
        cloth=Image.open(HERE/'references'/f'clothing-{d}.png').convert('RGBA')
        graded,_=grade(source,cloth)
        masks,_=material_masks(source)
        union=np.maximum.reduce([np.asarray(m) for m in masks.values()])
        xy=((i%2)*256,(i//2)*384)
        guide.paste(graded.resize((256,384),Image.Resampling.LANCZOS),xy)
        ref.paste(cloth.resize((256,384),Image.Resampling.LANCZOS),xy)
        mask.paste(Image.fromarray(union).resize((256,384),Image.Resampling.BILINEAR),xy)
    guide.save(folder/'standing-guide.png');ref.save(folder/'attack-clothing-reference.png');mask.save(folder/'standing-edit-mask.png')
    prompt='''用途：游戏角色序列帧的身份一致性与服装配色修复。图1是需要编辑的四方向站立图集，左上正面、右上右侧、左下背面、右下左侧。图2只提供衣料颜色和材质参考。保持图1的四个人物各自位置、身高、修长身材、头脸、银色短卷发、轮廓、站姿、手指、靴子、背剑与金色刺绣完全一致。只在遮罩衣料区修复接缝、纹理与色彩过渡，将背心统一成图2的深酒红/棕红色，将袖子与裤子统一成图2的深炭灰色。不要画亮灰裤子，不要增大头，不要改变人物比例，不要改手和剑，不添加配件。保留四格布局、透明背景和原有受光明暗。'''
    (folder/'standing-prompt.txt').write_text(prompt,encoding='utf-8')
    case={'name':'v3-standing-four-directions','guide':str(folder/'standing-guide.png'),'mask':str(folder/'standing-edit-mask.png'),
        'reference':str(folder/'attack-clothing-reference.png'),'prompt':str(folder/'standing-prompt.txt'),'seed':2026110703}
    (HERE/'cases.json').write_text(json.dumps([case],ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared four-direction local Qwen masked clothing repair.')


def prepare_attack():
    import json
    m=json.loads(prepare.MANIFEST.read_text());frames=prepare.inventory(m)
    locations={(r['image'],r['index']):r['hair'] for r in json.loads((HERE/'head-locations.json').read_text())['frames']}
    folder=HERE/'qwen-inputs';folder.mkdir(exist_ok=True)
    guide=Image.new('RGBA',(512,768));reference=guide.copy();mask=Image.new('L',guide.size)
    reports=[]
    for i,d in enumerate(prepare.DIRECTIONS):
        r=prepare.find(frames,'attack_sword_W01',d,1);source=prepare.canvas(r)
        changed,report=retarget_head(source,r,locations[(r['image'],r['index'])]);reports.append(report|{'direction':d})
        changed.save(folder/f'attack-{d}-guide.png')
        xy=((i%2)*256,(i//2)*384)
        guide.paste(changed.resize((256,384),Image.Resampling.LANCZOS),xy)
        reference.paste(Image.open(HERE/'references'/f'identity-{d}.png').resize((256,384),Image.Resampling.LANCZOS),xy)
        cx,ny=report.get('original_neck_xy',[256,190]);edit=Image.new('L',(512,768));dr=ImageDraw.Draw(edit)
        dr.ellipse((cx-24,ny-13,cx+24,ny+17),fill=255)
        alpha=np.asarray(changed)[...,3];e=np.asarray(edit).copy();e[alpha<245]=0
        mask.paste(Image.fromarray(e).resize((256,384),Image.Resampling.BILINEAR),xy)
    guide.save(folder/'attack-guide.png');reference.save(folder/'standing-identity-reference.png');mask.save(folder/'attack-edit-mask.png')
    prompt='''图1是四方向挥剑动作图集：左上朝前、右上朝右、左下背面、右下朝左；头部已经按图2的站姿角色对齐，图2只作为头脸身份和比例参考。只修复遮罩中的颈部、领口和衣领接缝，让皮肤与衣领连接自然。严格保留图1现有头型、银色短卷发、脸型、头部大小、身材、动作姿态、衣服的深酒红颜色、炭黑裤子、刺绣、武器完整剑尖、手指、脚锚、四格布局与透明背景。禁止放大头、改发型、改身高、改手、改剑、增加人物或配件。'''
    (folder/'attack-prompt.txt').write_text(prompt,encoding='utf-8')
    cases=json.loads((HERE/'cases.json').read_text())
    cases=[c for c in cases if c['name']!='v3-attack-four-directions']
    cases.append(dict(name='v3-attack-four-directions',guide=str(folder/'attack-guide.png'),mask=str(folder/'attack-edit-mask.png'),reference=str(folder/'standing-identity-reference.png'),prompt=str(folder/'attack-prompt.txt'),seed=2026110704))
    (HERE/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
    (HERE/'attack-head-guide-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    print(json.dumps(reports))

def detect_all():
    import json
    record=json.loads((HERE/'inventory.json').read_text())
    sheets={x['image']:Image.open(prepare.ACTOR/x['image']).convert('RGBA') for x in record['images']}
    rows=[];errors=[]
    for number,r in enumerate(record['frames'],1):
        try:
            info,_=hair(prepare.canvas(r,sheets),r);rows.append(dict(image=r['image'],index=r['index'],direction=r['direction'],hair=info))
        except ValueError as e:errors.append(dict(image=r['image'],index=r['index'],error=str(e)))
        if number%250==0:print('Located',number,'frames',flush=True)
    (HERE/'head-locations.json').write_text(json.dumps({'frames':rows,'errors':errors},indent=2),encoding='utf-8')
    print(json.dumps({'located':len(rows),'errors':errors,'canonical':{d:canonical(d)[1] for d in prepare.DIRECTIONS}}))
    board=Image.new('RGB',(800,250),'#28282a');draw=ImageDraw.Draw(board)
    for col,d in enumerate(prepare.DIRECTIONS):
        im,info=canonical(d);patch=im.crop((180,65,340,220)).resize((200,194))
        board.paste(patch,(col*200,25),patch);draw.text((col*200+5,5),d,fill='white')
    board.save(HERE/'canonical-heads-small.jpg',quality=90)

if __name__=='__main__':detect_all()
