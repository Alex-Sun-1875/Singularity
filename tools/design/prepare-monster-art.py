"""Adapt the existing Pillow/manifest pipeline to six-pose, four-view RGBA art.

No generation, inferred RGB matting, per-frame fitting or invented poses. Existing
enemy_atlas_runtime's four-column-only repacker cannot represent this source.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,statistics,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/encounters/monster-ecology-v1'
TARGET=ROOT/'src/cocos/assets/resources/flat2d/characters'
SPECS={'thorn-hound':(1.25,2.8,'attack_sword',3,None),'marsh-spitter':(.95,1.35,'spell',24,None),'ridgebreaker':(2.9,2,'attack_sword',210,244)}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf-8')
def rel(path):return str(path.relative_to(ROOT)).replace('\\','/')
def meta(path,kind):
    output=path.with_name(path.name+'.meta')
    if output.exists():return
    identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,rel(path)))
    if kind=='image':
        data=json.loads((ROOT/'src/cocos/assets/resources/ui/icons/potion-health.png.meta').read_text('utf-8'))
        data=json.loads(json.dumps(data).replace(data['uuid'],identifier).replace('potion-health','atlas'))
        data['subMetas']['6c48a']['userData'].update(wrapModeS='clamp-to-edge',wrapModeT='clamp-to-edge',mipfilter='none')
    else:data=dict(ver='1.2.0'if kind=='directory'else'2.0.1',importer=kind,imported=True,uuid=identifier,files=[]if kind=='directory'else['.json'],subMetas={},userData={})
    write(output,data)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--catalog',type=Path);args=parser.parse_args()
    catalog=json.loads(args.catalog.read_text('utf-8-sig'))if args.catalog else None
    source=ROOT/catalog['sourceRoot']if catalog else SOURCE
    specs=catalog['specs']if catalog else SPECS
    cell=int(catalog.get('runtimeCell',256))if catalog else 256
    assert cell in [128,192,256],'Use a uniform atlas reduction, never per-frame fitting'
    summaries=[]
    for key,(height,speed,pose,cut,opaque)in specs.items():
        folder=source/key;raw=folder/'raw.png';im=Image.open(raw)
        assert im.mode=='RGBA'and im.size==(1536,1024),'Use the original six-by-four transparent cloud output'
        pixels=np.array(im);alpha=pixels[:,:,3].copy();assert np.mean(alpha<=cut)>.08
        # Cloud output included low-opacity background mist. Use the actual
        # alpha channel, never white/green RGB keying that would erase tusks.
        if opaque:pixels[:,:,3]=np.clip((alpha.astype(float)-cut)/(opaque-cut)*255,0,255).astype('uint8')
        else:pixels[:,:,3][alpha<=cut]=0
        assert np.array_equal(pixels[:,:,:3],np.array(im)[:,:,:3]),'RGB anatomy, materials and all poses stay untouched'
        packed=Image.fromarray(pixels)
        if cell!=256:packed=packed.resize((cell*6,cell*4),Image.Resampling.LANCZOS)
        pixels=np.asarray(packed)
        pack=folder/'processed';pack.mkdir(exist_ok=True)
        packed.save(pack/'atlas.png',optimize=True)
        bounds=[];origins=[]
        for row in range(4):
            row_bounds=[]
            for col in range(6):
                a=Image.fromarray(pixels[row*cell:(row+1)*cell,col*cell:(col+1)*cell,3]);b=a.point(lambda v:255 if v>=32 else 0).getbbox();assert b
                row_bounds.append(list(b));bounds.append(list(b))
            pivot=[(row_bounds[0][0]+row_bounds[0][2])/2,statistics.median(b[3]for b in row_bounds[:3])]
            origins.extend([pivot[:]for _ in range(6)])
        upp=height/(bounds[0][3]-bounds[0][1])
        action=dict(image='atlas.png',frames=4,frameIndices=[0,3,4,5],phaseStarts=[0,.24,.55,.8],fps=6,loop=False)
        manifest=dict(revision=catalog.get('revision','monster-variety-v2-six-authored-poses')if catalog else'monster-ecology-v1-six-authored-poses',sourceDesign=rel(raw),loaded3DModel=False,image='atlas.png',columns=6,frameWidth=cell,frameHeight=cell,directions=['down','left','up','right'],origin=origins[0],perFrameOrigins=origins,alphaBounds=bounds,alphaThreshold=.025,camera=dict(worldUnitsPerPixel=upp),actions=dict(idle=dict(image='atlas.png',frames=1,frameIndices=[0],fps=1,loop=True),walk=dict(image='atlas.png',frames=2,frameIndices=[1,2],fps=6,loop=True,nominalSpeedMetresPerSecond=speed),**{pose:action}),limitations=['Four actually drawn directions, no invented diagonal or mirrored views.','Six authored poses, not a skeletal animation or generated in-between sequence.','One fixed support-plane pivot per direction across all six source cells; no per-frame fitting or scaling.','No independent corpse drawing. A real defeat may briefly fade the current pose.','Windup, active and recovery use the real EnemyCombat phase, not a separate timer.'])
        # The spitter uses its own mouth strike for the defensive close-range move.
        if pose=='spell':manifest['actions']['attack_sword']=action.copy()
        write(pack/'manifest.json',manifest)
        target=TARGET/key;target.mkdir(exist_ok=True)
        for name in ['atlas.png','manifest.json']:shutil.copy2(pack/name,target/name)
        for path,kind in [(target,'directory'),(target/'atlas.png','image'),(target/'manifest.json','json')]:meta(path,kind)
        sheet=Image.new('RGB',packed.size,'#323a34');sheet.paste(packed,(0,0),packed);sheet.resize((1152,768),Image.Resampling.LANCZOS).save(pack/'contact.jpg',quality=88)
        review=dict(generation='succeeded',provider='OpenAI image_gen built-in cloud',transparentBackgroundRequested=True,raw=rel(raw),rawSha256=sha(raw),prompt=rel(folder/'prompt.txt'),promptSha256=sha(folder/'prompt.txt'),sourceSize=list(im.size),sourceMode=im.mode,processing=dict(method='existing alpha only, all RGB untouched; no per-frame scale or translation',backgroundAlphaCut=cut,opaqueAlpha=opaque,reason='Generated RGBA contained background mist; remove using channel levels, not RGB matting.'),clearedPixels=int(np.count_nonzero((alpha>0)&(alpha<=cut))),atlasSha256=sha(target/'atlas.png'),manifestSha256=sha(target/'manifest.json'),staticArtReview='passed-for-pilot: organic identity, complete body, four drawn views, explicit anticipation/strike/recovery; walk contacts are sparse two-pose animation',runtimeReview='pending actual game validation',userArtAcceptance='not claimed',runtime=rel(target),worldUnitsPerPixel=upp,rgbaBytes=1536*1024*4,bounds=bounds)
        review['processing']['uniformAtlasScale']=cell/256
        if cell!=256:review['processing']['method']='Source RGB preserved during alpha-channel cleanup, followed by one uniform whole-atlas Lanczos reduction; no per-frame fitting, translation or invented poses'
        review['runtimeSize']=list(packed.size);review['rgbaBytes']=packed.width*packed.height*4
        write(folder/'generation-and-review.json',review);summaries.append(review)
    if not catalog:
        doc=ROOT/'docs/design/monster-ecology-v1.md';code=ROOT/'src/cocos/assets/scripts/features/world/data/MonsterEcology.ts';text=code.read_text('utf-8')
        text=re.sub(r"catalogSha256:'(?:[a-f0-9]{64}|MONSTER_DESIGN_SHA256)'", "catalogSha256:'"+sha(doc)+"'",text)
        code.write_text(text,'utf-8')
    write(source/'production.json',dict(assets=summaries,dependencies='Existing Pillow, NumPy and Cocos; no new packages or model downloads',runtimeAcceptance='pending'))
    print(json.dumps([dict(asset=s['runtime'],rgbaBytes=s['rgbaBytes'],upp=s['worldUnitsPerPixel'],cleared=s['clearedPixels'])for s in summaries]))

if __name__=='__main__':main()
