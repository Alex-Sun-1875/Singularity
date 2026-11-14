"""Uniform whole-atlas production resampling for independently drawn enemies."""
from __future__ import annotations
import argparse,copy,hashlib,json,shutil,uuid
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
FACTOR=2/3

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf-8')

def coordinates(value,factor=FACTOR):
    if isinstance(value,list):return [coordinates(x,factor)for x in value]
    if isinstance(value,dict):return {key:coordinates(x,factor)for key,x in value.items()}
    if isinstance(value,(float,int)):return round(value*factor,6)
    return value

def scaled_manifest(value,factor=FACTOR):
    out={}
    for key,item in value.items():
        if key in ['frameWidth','frameHeight']:out[key]=int(round(item*factor))
        elif key in ['origin','perFrameOrigins','alphaBounds','perFrameRects','frameRectsByImage']:out[key]=coordinates(item,factor)
        elif key=='worldUnitsPerPixel':out[key]=item/factor
        elif isinstance(item,dict):out[key]=scaled_manifest(item,factor)
        else:out[key]=copy.deepcopy(item)
    return out

def prepare_runtime(source):
    source=Path(source);atlas=source/'atlas.png';manifest_path=source/'manifest.json'
    source_sha=sha(atlas);manifest_sha=sha(manifest_path)
    image=Image.open(atlas).convert('RGBA');assert image.width==image.height and image.width%4==0
    original=json.loads(manifest_path.read_text('utf-8'));source_cell=image.width//4
    assert original['frameWidth']==source_cell and original['frameHeight']==source_cell
    factor=1024/image.width
    output=source/'runtime-1024';output.mkdir(exist_ok=True)
    # One whole-image transform. No per-frame fitting, sprite resizing or
    # origin recalibration occurs at this production stage.
    image.resize((1024,1024),Image.Resampling.LANCZOS).save(output/'atlas.png')
    manifest=scaled_manifest(original,factor)
    manifest['revision']=original['revision']+'-runtime1024'
    manifest['runtimeAtlasResample']=dict(scale=factor,sourceAtlasSize=list(image.size),runtimeAtlasSize=[1024,1024],filter='Pillow LANCZOS, one whole-atlas resize',sourceAtlasSha256=source_sha,sourceManifestSha256=manifest_sha,perFrameRescale=False)
    write(output/'manifest.json',manifest)
    upp=original['camera']['worldUnitsPerPixel'];runtime_upp=manifest['camera']['worldUnitsPerPixel']
    assert abs(source_cell*upp-256*runtime_upp)<1e-10
    max_origin_error=max(abs(old*upp-new*runtime_upp)for a,b in zip(original['perFrameOrigins'],manifest['perFrameOrigins'])for old,new in zip(a,b))
    assert max_origin_error<1e-8
    assert original['frameScaleFactors']==manifest['frameScaleFactors']
    assert sha(atlas)==source_sha and sha(manifest_path)==manifest_sha
    source_bytes=image.width*image.height*4
    report=dict(status='runtime-production-resample-prepared',sourceAtlasSha256=source_sha,sourceManifestSha256=manifest_sha,sourceFilesUnchanged=True,sourceAtlasSize=list(image.size),runtimeAtlasSize=[1024,1024],runtimeAtlasSha256=sha(output/'atlas.png'),runtimeManifestSha256=sha(output/'manifest.json'),sourceCellSize=[source_cell,source_cell],runtimeCellSize=[256,256],uniformScale=factor,sourceWorldUnitsPerPixel=upp,runtimeWorldUnitsPerPixel=runtime_upp,maxWorldOriginErrorMetres=max_origin_error,frameScaleMultipliersUnchanged=True,wholeAtlasOnly=True,perFrameRescale=False,rgbaMemory=dict(sourceBytes=source_bytes,runtimeBytes=1024*1024*4,sourceMiB=source_bytes/1048576,runtimeMiB=4,thirtyTwoEnemyTypesSourceMiB=source_bytes/1048576*32,thirtyTwoEnemyTypesRuntimeMiB=128,estimateScope='RGBA8 level0 only; no mipmaps; excludes ImageAsset/driver/mesh memory'),generationStatus='existing cloud source; no new generation',staticReview='source pilot identity/anchors reviewed separately; production resize pending visual review',runtimePlayReview='pending',runtimeInstalled=False)
    write(source/'runtime-resample.json',report)
    return output,report

def install_runtime(source,concept):
    review=json.loads((Path(source)/'review.json').read_text('utf-8'))
    assert review['staticArtReview'].startswith('passed-for-pilot'),'Independent static pilot review is required before installation'
    output,report=prepare_runtime(source)
    target=ROOT/'src/cocos/assets/resources/flat2d/characters'/concept
    target.mkdir(exist_ok=True)
    for name in ['atlas.png','manifest.json']:
        path=target/name
        if not path.exists()or path.read_bytes()!=(output/name).read_bytes():shutil.copy2(output/name,path)
    for path,kind in [(target,'directory'),(target/'atlas.png','image'),(target/'manifest.json','json')]:
        meta=path.with_name(path.name+'.meta')
        if meta.exists():continue
        identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,str(path.relative_to(ROOT)).replace('\\','/')))
        if kind=='image':
            data=json.loads((ROOT/'src/cocos/assets/resources/ui/icons/potion-health.png.meta').read_text('utf-8'))
            data=json.loads(json.dumps(data).replace(data['uuid'],identifier).replace('potion-health','atlas'))
            texture=data['subMetas']['6c48a']['userData'];texture.update(wrapModeS='clamp-to-edge',wrapModeT='clamp-to-edge',mipfilter='none')
        else:data={'ver':'1.2.0'if kind=='directory'else'2.0.1','importer':kind,'imported':True,'uuid':identifier,'files':[]if kind=='directory'else['.json'],'subMetas':{},'userData':{}}
        write(meta,data)
    report['runtimeInstalled']=True;report['runtimeDirectory']=str(target.relative_to(ROOT)).replace('\\','/')
    write(Path(source)/'runtime-resample.json',report)
    install_path=Path(source)/'runtime-install.json'
    installation=json.loads(install_path.read_text('utf-8'))if install_path.exists()else dict(conceptId=concept,native3DInstalled=False)
    installation.update(runtimeDirectory=report['runtimeDirectory'],atlasSha256=sha(target/'atlas.png'),manifestSha256=sha(target/'manifest.json'),runtimeAtlasSize=[1024,1024],productionResample='runtime-resample.json')
    write(install_path,installation)
    return output,report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('--install-concept');args=parser.parse_args()
    _,report=install_runtime(args.source,args.install_concept)if args.install_concept else prepare_runtime(args.source)
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
