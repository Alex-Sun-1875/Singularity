"""Conservative R2-1 passing-leg composite and exact-pixel four-view packing.

Uses only the checked-in cloud result and existing Pillow/scipy. The original
sheet, all other cells, upper bodies, apron hems and pickaxes are protected.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from enemy_atlas_runtime import prepare_runtime,install_runtime

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/encounters/cloud-world-v2/actor-pilot-v1'
OUTPUT=SOURCE/'miner-production-v2'
CELL=384
DIRECTIONS=['down','left','up','right']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')

# Coordinates in each 384px input cell, following the original apron hem.
# Only the side of this line BELOW the apron can change. Pickaxe tips and
# every pixel above this authored boundary remain original, including alpha.
HEMS=[
 [(0,250),(134,250),(138,247),(145,248),(152,247),(166,249),(177,251),(185,253),(194,253),(197,256),(210,257),(216,255),(223,254),(225,252),(233,252),(237,250),(241,251),(242,248),(246,249),(250,245),(254,245),(256,242),(261,242),(266,240),(272,245),(300,250),(383,250)],
 [(0,235),(109,235),(114,240),(120,244),(127,247),(134,248),(139,251),(145,250),(150,252),(157,252),(161,256),(168,254),(176,253),(187,250),(195,249),(201,247),(208,246),(217,246),(223,244),(228,246),(235,249),(240,252),(250,254),(275,254),(383,254)],
]
REGISTRATIONS=[
 dict(scale=.99909306,dx=-.29733306,dy=.3094615,upperRegionMaeBefore=.05095756,upperRegionMaeAfter=.04497563),
 dict(scale=.99743727,dx=-.32920098,dy=.36247665,upperRegionMaeBefore=.0559768,upperRegionMaeAfter=.04774702),
]
UPP=.00665
IDLE_PELVIS_X=[170,476,793,1084]
ATTACK_SUPPORT=[(166,1215),(506,1208),(785,1226),(1078,1214)]

def register(image,registration):
    """Pillow affine on premultiplied RGBA avoids transparent RGB fringes."""
    rgba=np.asarray(image.convert('RGBA'),dtype=np.float32)/255
    rgba[rgba[:,:,3]<=3/255,3]=0
    premul=rgba.copy();premul[:,:,:3]*=premul[:,:,3:4]
    s=registration['scale'];dx=registration['dx'];dy=registration['dy']
    affine=(1/s,0,192-(192+dx)/s,0,1/s,192-(192+dy)/s)
    channels=[]
    for i in range(4):
        channel=Image.fromarray(premul[:,:,i]).transform((CELL,CELL),Image.Transform.AFFINE,affine,Image.Resampling.BICUBIC)
        channels.append(np.asarray(channel))
    out=np.clip(np.stack(channels,2),0,1)
    out[:,:,:3]=np.divide(out[:,:,:3],out[:,:,3:4],out=np.zeros_like(out[:,:,:3]),where=out[:,:,3:4]>0)
    return np.rint(out*255).astype(np.uint8)

def composite():
    OUTPUT.mkdir(exist_ok=True)
    raw=SOURCE/'r2-1-sheet-v1.png';original=np.asarray(Image.open(raw).convert('RGBA'))
    input_pair=np.asarray(Image.open(SOURCE/'r2-1-side-passing-edit-input.png').convert('RGBA'))
    generated_path=SOURCE/'r2-1-side-passing-generated-v2.png'
    generated=Image.open(generated_path).convert('RGBA').resize((768,384),Image.Resampling.LANCZOS)
    result=original.copy();editable=np.zeros(original.shape[:2],bool);records=[]
    pair_review=Image.new('RGBA',(768,384*3),(56,56,60,255));draw=ImageDraw.Draw(pair_review)
    for index,(left,right) in enumerate([(314,627),(941,1254)]):
        source_cell=original[627:941,left:right];provided=input_pair[:,384*index:384*(index+1)]
        # Root's reference has only alpha<=3 noise cleared. Restore raw RGBA
        # in the compositing base so even invisible protected pixels survive.
        visible=source_cell[:,:,3]>3
        assert np.array_equal(source_cell[visible],provided[35:349,35:348][visible])
        pair=np.zeros((384,384,4),np.uint8);pair[35:349,35:348]=source_cell
        aligned=register(generated.crop((384*index,0,384*(index+1),384)),REGISTRATIONS[index])
        xs=np.arange(384);threshold=np.interp(xs,*np.asarray(HEMS[index]).T)
        # Two pixels of blending strictly BELOW the protected original apron.
        weight=np.clip((np.arange(384)[:,None]-threshold[None,:])/2,0,1)
        # The opposite pickaxe and body padding are outside the lower-leg edit.
        weight[:,:75]=0;weight[:,320:]=0
        if index==1:weight[:281,275:]=0 # original right-facing pickaxe tip
        mix=pair.copy();alpha=weight[:,:,None]
        a=pair.astype(np.float32)/255;b=aligned.astype(np.float32)/255
        pa=a.copy();pb=b.copy();pa[:,:,:3]*=pa[:,:,3:4];pb[:,:,:3]*=pb[:,:,3:4]
        blend=pa*(1-alpha)+pb*alpha
        blend[:,:,:3]=np.divide(blend[:,:,:3],blend[:,:,3:4],out=np.zeros_like(blend[:,:,:3]),where=blend[:,:,3:4]>0)
        changed=weight>0;mix[changed]=np.rint(np.clip(blend[changed],0,1)*255).astype(np.uint8)
        target=mix[35:349,35:348];mask=changed[35:349,35:348]
        result[627:941,left:right]=target;editable[627:941,left:right]=mask
        assert np.array_equal(source_cell[~mask],target[~mask])
        record=dict(direction=['left','right'][index],sourceCellRect=[left,627,right,941],pairOffset=[35,35],registration=REGISTRATIONS[index],protectedUpperBodyAndApronPixelsExact=True,protectedPickaxePixelsExact=True,editedPixels=int(np.count_nonzero(np.any(source_cell!=target,2))),maskPixels=int(mask.sum()),hem=HEMS[index])
        records.append(record)
        for row,patch in enumerate([pair,aligned,mix]):pair_review.alpha_composite(Image.fromarray(patch),(index*384,row*384))
        mask_image=np.rint(weight*255).astype(np.uint8)
        Image.fromarray(mask_image).save(OUTPUT/('side-'+['left','right'][index]+'-edit-mask.png'))
    assert np.array_equal(original[~editable],result[~editable])
    other_cells=0
    for row in range(4):
        top,bottom=[0,314,627,941,1254][row:row+2]
        for col in range(4):
            left,right=[0,314,627,941,1254][col:col+2]
            if (row,col) in [(2,1),(2,3)]:continue
            assert np.array_equal(original[top:bottom,left:right],result[top:bottom,left:right]);other_cells+=1
    target=SOURCE/'r2-1-sheet-v2-composite.png';Image.fromarray(result).save(target)
    for row,label in enumerate(['original side walk B','registered cloud lower-leg source','conservative lower-body composite']):draw.text((8,row*384+8),label,fill='white')
    pair_review.convert('RGB').save(OUTPUT/'side-composite-review.jpg',quality=95)
    report=dict(originalSha256=sha(raw),generatedSha256=sha(generated_path),compositeSha256=sha(target),cloudGeneration='completed separately: r2-1-side-passing-generation.json',registrationMethod='scipy differential_evolution fitting upper-body premultiplied luminance/alpha, similarity scale+translation only; Pillow deterministic resampling',protectedUneditedCellsExact=other_cells,allPixelsOutsideLowerLegMasksExact=True,wholeOriginalSheetPreserved=True,mirrored=False,originalBodyRescaled=False,records=records,artReview='prepared; pending separate static review',runtimeInstalled=False)
    write(OUTPUT/'composite-processing.json',report)
    return target,report

def pack(source):
    """Preserve every composite alpha>3 pixel once in a1536 source pack."""
    original=np.asarray(Image.open(source).convert('RGBA'));pixels=original.copy();pixels[pixels[:,:,3]<=3,3]=0
    labels,_=ndimage.label(pixels[:,:,3]>3);sizes=np.bincount(labels.ravel());main_ids=np.flatnonzero(sizes>10000);main_ids=main_ids[main_ids>0]
    assert len(main_ids)==16
    bodies=np.where(np.isin(labels,main_ids),labels,0)
    _,nearest=ndimage.distance_transform_edt(bodies==0,return_indices=True)
    owners=bodies[nearest[0],nearest[1]];owners[pixels[:,:,3]==0]=0
    atlas=Image.new('RGBA',(1536,1536));frames={};records={}
    for identifier in main_ids:
        ys,xs=np.where(labels==identifier);pose=min(3,int(ys.mean()/313.5));direction=min(3,int(xs.mean()/313.5));key=(pose,direction);assert key not in records
        yy,xx=np.where(owners==identifier);left,top,right,bottom=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
        patch=pixels[top:bottom,left:right].copy();patch[owners[top:bottom,left:right]!=identifier]=[0,0,0,0]
        h,w=patch.shape[:2];assert max(h,w)<CELL-32
        mask=patch[:,:,3]>=128;py,px=np.where(mask);head=mask&(np.indices(mask.shape)[0]<int(py.min())+46)
        head_x=float(np.where(head)[1].mean());head_y=float(np.where(head)[0].mean())
        paste_x=(CELL-w)//2;paste_y=(CELL-h)//2
        frame=Image.new('RGBA',(CELL,CELL));frame.paste(Image.fromarray(patch),(paste_x,paste_y))
        origin=[paste_x+IDLE_PELVIS_X[direction]-left,paste_y+float(py.max()+1)]
        if pose==3:origin=[paste_x+ATTACK_SUPPORT[direction][0]-left,paste_y+ATTACK_SUPPORT[direction][1]-top]
        records[key]=dict(direction=DIRECTIONS[direction],pose=['idle','walk-a','walk-b','attack'][pose],sourceRect=[left,top,right,bottom],atlasRect=[pose*CELL,direction*CELL,CELL,CELL],origin=origin,coreLandmark=[paste_x+head_x,paste_y+head_y],coreBasis='helmet centroid in upper46px; x pivot is pelvis projection, not weapon silhouette',alphaBounds=list(frame.getchannel('A').getbbox()),scaleFactor=1,retainedPixels=int(np.count_nonzero(patch[:,:,3])))
        assert np.array_equal(patch[owners[top:bottom,left:right]==identifier],original[top:bottom,left:right][owners[top:bottom,left:right]==identifier])
        frames[key]=frame;atlas.paste(frame,(pose*CELL,direction*CELL))
    # Walking feet project nearer/farther in the image. A moving boot toe is
    # not a rigid-body height anchor. Keep the helmet/core height continuous
    # with idle; preserve the attack's genuine crouch and planted support.
    for direction in range(4):
        idle=records[(0,direction)];height=idle['origin'][1]-idle['coreLandmark'][1];x_offset=idle['origin'][0]-idle['coreLandmark'][0]
        for pose in [1,2]:
            record=records[(pose,direction)];record['previousToeOrigin']=record['origin'][:]
            record['origin']=[record['coreLandmark'][0]+x_offset,record['coreLandmark'][1]+height]
            record['anchorBasis']='Pelvis/support-plane projection derived from the stable helmet/core; advancing toe pixels may project below this plane.'
            record['worldCoreHeightDeltaFromIdlePixels']=0
    for record in records.values():
        record['origin']=[round(v,3)for v in record['origin']];record['coreLandmark']=[round(v,3)for v in record['coreLandmark']]
        x1,y1,x2,y2=record['alphaBounds'];assert min(x1,y1)>=16 and max(x2,y2)<=CELL-16
    assert sum(record['retainedPixels']for record in records.values())==int(np.count_nonzero(pixels[:,:,3]))
    atlas.save(OUTPUT/'atlas.png');ordered=[records[(pose,direction)]for direction in range(4)for pose in range(4)]
    manifest=dict(revision='miner-pilot-v2-protected-passing-legs-ground-anchors',sourceDesign=str(source.relative_to(ROOT)).replace('\\','/'),loaded3DModel=False,image='atlas.png',columns=4,frameWidth=CELL,frameHeight=CELL,directions=DIRECTIONS,origin=ordered[0]['origin'],perFrameOrigins=[r['origin']for r in ordered],alphaBounds=[r['alphaBounds']for r in ordered],alphaThreshold=.025,frameScaleFactors={'atlas':[1]*16},camera={'worldUnitsPerPixel':UPP},actions={
        'idle':dict(image='atlas.png',frames=1,frameIndices=[0],fps=1,loop=True),
        'walk':dict(image='atlas.png',frames=2,frameIndices=[1,2],fps=3.5,loop=True,nominalSpeedMetresPerSecond=1.7),
        'attack_sword':dict(image='atlas.png',frames=3,frameIndices=[0,3,0],phaseStarts=[0,.28,.6],fps=5,loop=False),
    },limitations=['Only four actually drawn directions; no mirrored diagonal views.','Two walking drawings only. Side passing pose is now distinct, but a full multi-contact walking cycle has not been generated.','One committed pickaxe strike drawing with actual idle reused for windup/recovery.','Hit uses own idle fallback; absent death drawing hides actor.','No native3D mesh/skeleton/animation; native3D remains documented legacy.','Static contact/identity review is separate from actual game gait, turn, scale and collision acceptance.'])
    write(OUTPUT/'manifest.json',manifest)
    contact=Image.new('RGBA',(CELL*4,(CELL+30)*4),(52,52,56,255));draw=ImageDraw.Draw(contact)
    for direction in range(4):
        for pose in range(4):
            x=pose*CELL;y=direction*(CELL+30);origin=records[(pose,direction)]['origin'];contact.alpha_composite(frames[(pose,direction)],(round(x+CELL/2-origin[0]),round(y+CELL-46-origin[1])))
            draw.line((x+6,y+CELL-46,x+CELL-6,y+CELL-46),fill=(180,135,70,255));draw.text((x+8,y+CELL+5),DIRECTIONS[direction]+' / '+['idle','walk-a','walk-b','attack'][pose],fill='white')
    contact.convert('RGB').save(OUTPUT/'anchor-contact.jpg',quality=94)
    loop=[]
    for pose in [1,2]:
        preview=Image.new('RGBA',(CELL*2,CELL*2),(52,52,56,255));draw=ImageDraw.Draw(preview)
        for direction in range(4):
            x=direction%2*CELL;y=direction//2*CELL;origin=records[(pose,direction)]['origin'];preview.alpha_composite(frames[(pose,direction)],(round(x+CELL/2-origin[0]),round(y+CELL-46-origin[1])));draw.line((x+8,y+CELL-46,x+CELL-8,y+CELL-46),fill=(180,135,70,255));draw.text((x+8,y+8),DIRECTIONS[direction],fill='white')
        loop.append(preview.convert('RGB'))
    loop[0].save(OUTPUT/'walk-loop.gif',save_all=True,append_images=loop[1:],duration=286,loop=0)
    write(OUTPUT/'packing-processing.json',dict(status='source-only-awaiting-static-review',sourceSha256=sha(source),atlasSha256=sha(OUTPUT/'atlas.png'),allAlphaAbove3PixelsRetainedExactlyOnce=True,alphaCleanupThreshold=3,perFrameRescale=False,mirrored=False,directions=DIRECTIONS,worldUnitsPerPixel=UPP,scaleBasis='One global1.9m-class adult human helmet-to-ground scale, not per-frame fitting',frames=ordered,runtimeInstalled=False,runtimePlayReview='pending'))
    prepare_runtime(OUTPUT)
    return manifest

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
    target,report=composite()
    pack(target)
    if args.install:
        install_runtime(OUTPUT,'mine-worker')
        for name in ['composite-processing.json','packing-processing.json']:
            value=json.loads((OUTPUT/name).read_text('utf-8'));value.update(status='installed-pilot-awaiting-runtime-review',runtimeInstalled=True,runtimeConceptId='mine-worker',artReviewEvidence='review.json',runtimePlayReview='pending sample build');write(OUTPUT/name,value)
        value=json.loads((OUTPUT/'runtime-install.json').read_text('utf-8'));value['onlyTemplate']='R2-1';write(OUTPUT/'runtime-install.json',value)
    print('Prepared '+target.name+';14 other cells and all unmasked RGBA are byte-exact; runtime installed='+str(args.install))

if __name__=='__main__':main()
