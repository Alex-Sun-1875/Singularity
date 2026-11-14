"""Pack the existing R2-3 cloud pilot without repainting or rescaling a frame."""
from __future__ import annotations
import argparse,hashlib,json,shutil,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
from enemy_atlas_runtime import install_runtime

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/encounters/cloud-world-v2/actor-pilot-v1'
OUTPUT=SOURCE/'mine-crawler-production-v1'
DIRECTIONS=['down','left','up','right']
CELL=384
UPP=.0065
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')

def prepare():
    OUTPUT.mkdir(exist_ok=True)
    source=SOURCE/'r2-3-sheet-v1.png';original=np.array(Image.open(source).convert('RGBA'));pixels=original.copy()
    assert pixels.shape==(1254,1254,4)
    cleared=int(np.count_nonzero((pixels[:,:,3]>0)&(pixels[:,:,3]<=3)));pixels[pixels[:,:,3]<=3,3]=0
    # The generated figures spill a few pixels over nominal cell boundaries.
    # Find their 16 separate bodies, then return detached edge pixels to the
    # nearest body. All alpha>3 RGBA values are retained exactly once.
    labels,count=ndimage.label(pixels[:,:,3]>3);sizes=np.bincount(labels.ravel());main_ids=np.flatnonzero(sizes>10000);main_ids=main_ids[main_ids>0]
    assert len(main_ids)==16
    body_labels=np.where(np.isin(labels,main_ids),labels,0)
    _,indices=ndimage.distance_transform_edt(body_labels==0,return_indices=True)
    owner=body_labels[indices[0],indices[1]];owner[pixels[:,:,3]==0]=0
    records={};frames={};atlas=Image.new('RGBA',(CELL*4,CELL*4))
    for main_id in main_ids:
        ys,xs=np.where(labels==main_id);source_row=min(3,int(ys.mean()/313.5));source_col=min(3,int(xs.mean()/313.5));key=(source_row,source_col)
        assert key not in records
        ay,ax=np.where(owner==main_id);bounds=[int(ax.min()),int(ay.min()),int(ax.max()+1),int(ay.max()+1)]
        left,top,right,bottom=bounds;patch=pixels[top:bottom,left:right].copy();patch[owner[top:bottom,left:right]!=main_id]=[0,0,0,0]
        mask=patch[:,:,3]>=128;py,px=np.where(mask);h,w=mask.shape
        assert w<CELL-32 and h<CELL-32
        # The ore hopper is a stable body landmark, unlike reaching pincers.
        # Align its screen X; foot contact owns Y. No frame is fitted to a box.
        rgb=patch[:,:,:3].astype(np.int16);luma=rgb.mean(2);grey=rgb.max(2)-rgb.min(2)
        ore=mask&(np.indices(mask.shape)[0]<int(py.min())+60)&(grey<36)&(luma>75)&(luma<215)
        ox=float(np.where(ore)[1].mean()) if ore.any() else float(px.mean())
        oy=float(np.where(ore)[0].mean()) if ore.any() else float(py.min()+25)
        contact=float(py.max()+1)
        manual=None
        if key==(0,0):
            contact=256-top;manual='source global Y256: outer load-bearing front soles; the two relaxed pincer tips extend below them and are not feet'
        if key==(3,0):
            # In the down attack the pincer tips are below the supporting feet.
            # Anchor the broad load-bearing soles, not the digging fingertips.
            contact=1175-top;manual='source global Y1175: braced support soles; digging pincer tips may extend below this ground plane'
        paste_x=(CELL-w)//2;paste_y=(CELL-h)//2
        frame=Image.new('RGBA',(CELL,CELL));frame.paste(Image.fromarray(patch),(paste_x,paste_y))
        origin=[round(paste_x+ox,3),round(paste_y+contact,3)]
        atlas.paste(frame,(source_row*CELL,source_col*CELL))
        bound=frame.getchannel('A').getbbox()
        record=dict(sourceRow=source_row,sourceColumn=source_col,direction=DIRECTIONS[source_col],pose=['idle','walk-a','walk-b','attack'][source_row],sourceRect=bounds,atlasRect=[source_row*CELL,source_col*CELL,CELL,CELL],origin=origin,coreLandmark=[round(paste_x+ox,3),round(paste_y+oy,3)],alphaBounds=list(bound),scaleFactor=1,retainedPixels=int(np.count_nonzero(patch[:,:,3])),supportContactOverride=manual)
        original_owned=original[top:bottom,left:right][owner[top:bottom,left:right]==main_id]
        assert np.array_equal(patch[owner[top:bottom,left:right]==main_id],original_owned)
        assert bound[0]>=16 and bound[1]>=16 and bound[2]<=CELL-16 and bound[3]<=CELL-16
        records[key]=record;frames[key]=frame
    assert sum(record['retainedPixels'] for record in records.values())==int(np.count_nonzero(pixels[:,:,3]))
    # A forward step projects the nearest foot lower on screen without lifting
    # the whole rigid chassis. Keep the hopper reference continuous with idle;
    # do not turn that projected toe into a higher world-space body position.
    down_idle=records[(0,0)];core_height=down_idle['origin'][1]-down_idle['coreLandmark'][1]
    for pose in [1,2]:
        record=records[(pose,0)];record['previousToeOrigin']=record['origin'][:]
        record['origin'][1]=round(record['coreLandmark'][1]+core_height,3)
        record['supportContactOverride']='Down walking pivot is the chassis/support-plane projection, aligned by the rigid hopper landmark to idle; the forward-stepping foot is not a body-height anchor.'
        record['coreHeightDeltaFromIdlePixels']=round((record['origin'][1]-record['coreLandmark'][1])-core_height,4)
    atlas.save(OUTPUT/'atlas.png')
    ordered=[records[(pose,direction)] for direction in range(4) for pose in range(4)]
    origins=[record['origin']for record in ordered];bounds=[record['alphaBounds']for record in ordered]
    manifest=dict(revision='mine-crawler-pilot-v1-ground-anchors',sourceDesign=str(source.relative_to(ROOT)).replace('\\','/'),loaded3DModel=False,image='atlas.png',columns=4,frameWidth=CELL,frameHeight=CELL,directions=DIRECTIONS,origin=origins[0],perFrameOrigins=origins,alphaBounds=bounds,alphaThreshold=.025,frameScaleFactors={'atlas':[1]*16},camera={'worldUnitsPerPixel':UPP},actions={
        'idle':dict(image='atlas.png',frames=1,frameIndices=[0],fps=1,loop=True),
        'walk':dict(image='atlas.png',frames=2,frameIndices=[1,2],fps=5,loop=True,nominalSpeedMetresPerSecond=1.35),
        'attack_sword':dict(image='atlas.png',frames=3,frameIndices=[0,3,0],phaseStarts=[0,.28,.6],fps=5,loop=False),
    },limitations=['Four actually drawn directions only; no mirrored or invented diagonal views.','Two walking contact drawings; no generated in-between frames. Cadence follows measured runtime speed.','Attack has one committed pincer drawing sampled between actual idle poses; it is not a new full windup/recovery drawing sequence.','No hit/death drawing: hit uses the documented idle fallback; death hides this actor without inventing a corpse.','Static anchor review does not replace actual collision, turn and gait play review.','Native 3D mode retains its separately documented legacy actor; this pack contains no mesh, skeleton or 3D animation.'])
    write(OUTPUT/'manifest.json',manifest)
    # Contact sheet uses a common ground anchor, preserving every source pixel.
    contact=Image.new('RGBA',(CELL*4,(CELL+30)*4),(47,47,50,255));draw=ImageDraw.Draw(contact)
    for direction in range(4):
        for pose in range(4):
            x=pose*CELL;y=direction*(CELL+30);frame=frames[(pose,direction)];origin=records[(pose,direction)]['origin'];at=(round(x+CELL/2-origin[0]),round(y+CELL-52-origin[1]));contact.alpha_composite(frame,at)
            draw.line((x+8,y+CELL-52,x+CELL-8,y+CELL-52),fill=(170,126,64,255),width=1);draw.line((x+CELL/2,y+CELL-65,x+CELL/2,y+CELL-39),fill=(215,180,100,255),width=1)
            draw.text((x+10,y+CELL+5),DIRECTIONS[direction]+' / '+['idle','walk-a','walk-b','attack'][pose],fill=(235,216,174,255))
    contact.convert('RGB').save(OUTPUT/'anchor-contact.jpg',quality=92)
    loop=[]
    for pose in [1,2]:
        preview=Image.new('RGBA',(CELL*2,CELL*2),(47,47,50,255));draw=ImageDraw.Draw(preview)
        for direction in range(4):
            x=direction%2*CELL;y=direction//2*CELL;origin=records[(pose,direction)]['origin'];preview.alpha_composite(frames[(pose,direction)],(round(x+CELL/2-origin[0]),round(y+CELL-52-origin[1])));draw.line((x+8,y+CELL-52,x+CELL-8,y+CELL-52),fill=(170,126,64,255));draw.text((x+8,y+8),DIRECTIONS[direction],fill='white')
        loop.append(preview.convert('RGB'))
    loop[0].save(OUTPUT/'walk-loop.gif',save_all=True,append_images=loop[1:],duration=200,loop=0)
    report=dict(status='static-output-prepared-awaiting-separate-review',sourceSha256=sha(source),atlasSha256=sha(OUTPUT/'atlas.png'),sourceSize=[1254,1254],sourceDirectionsActuallyObserved=DIRECTIONS,alphaCleanup={'threshold':3,'affectedPixels':cleared,'higherAlphaRgbaUnchanged':True},repacking={'frames':16,'cell':[CELL,CELL],'sourcePixelsRetainedExactlyOnce':True,'mirrored':False,'perFrameRescale':False},downWalkingCoreHeightDriftPixels=[records[(pose,0)]['coreHeightDeltaFromIdlePixels'] for pose in [1,2]],worldUnitsPerPixel=UPP,frames=ordered,runtimeInstalled=False)
    write(OUTPUT/'processing.json',report)
    return manifest,report

def install(manifest,report):
    review=json.loads((OUTPUT/'review.json').read_text('utf-8'));assert review['staticArtReview']=='passed-for-pilot'
    target=ROOT/'src/cocos/assets/resources/flat2d/characters/mine-crawler';target.mkdir(exist_ok=True)
    for name in ['atlas.png','manifest.json']:
        destination=target/name
        if not destination.exists() or destination.read_bytes()!=(OUTPUT/name).read_bytes():shutil.copy2(OUTPUT/name,destination)
    for path,kind in [(target,'directory'),(target/'atlas.png','image'),(target/'manifest.json','json')]:
        meta=path.with_name(path.name+'.meta')
        if meta.exists():continue
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,str(path.relative_to(ROOT)).replace('\\','/')))
        if kind=='image':
            data=json.loads((ROOT/'src/cocos/assets/resources/ui/icons/potion-health.png.meta').read_text('utf-8'));data=json.loads(json.dumps(data).replace(data['uuid'],identifier).replace('potion-health','atlas'));data['subMetas']['6c48a']['userData']['wrapModeS']='clamp-to-edge';data['subMetas']['6c48a']['userData']['wrapModeT']='clamp-to-edge'
        else:data={'ver':'1.2.0'if kind=='directory'else'2.0.1','importer':kind,'imported':True,'uuid':identifier,'files':[]if kind=='directory'else['.json'],'subMetas':{},'userData':{}}
        write(meta,data)
    report['runtimeInstalled']=True;write(OUTPUT/'processing.json',report)
    # Keep the reviewed exact-pixel1536 source pack; install a uniformly
    # resampled1024 production copy with inverse world-unit conversion.
    install_runtime(OUTPUT,'mine-crawler')
    write(OUTPUT/'runtime-install.json',{'conceptId':'mine-crawler','onlyTemplate':'R2-3','runtimeDirectory':str(target.relative_to(ROOT)).replace('\\','/'),'atlasSha256':sha(target/'atlas.png'),'manifestSha256':sha(target/'manifest.json'),'native3DInstalled':False})

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args();manifest,report=prepare()
    if args.install:install(manifest,report)
    print('Prepared16 exact-pixel frames, actual4 directions, static anchor contact sheet and2-contact loop; installed='+str(args.install))
if __name__=='__main__':main()
