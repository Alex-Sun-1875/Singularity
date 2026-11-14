"""Patch four rear run calves/boots; retain existing upper pixels and sockets.

Uses existing native atlas crops, Pillow resampling and the existing shelf
packer. No new dependencies. Candidate must be visually accepted to install.
"""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,sys
import numpy as np
from PIL import Image,ImageDraw

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'local-qwen21-unified-v3'))
import prepare
spec=importlib.util.spec_from_file_location('existing_packer',ROOT/'attack-identity-v5/pack.py')
packer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=packer;spec.loader.exec_module(packer)
ACTOR=prepare.ACTOR
STAGE=HERE/'rear-run-candidate'
PHASES=[2,3,6,7]

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def build():
    manifest=json.loads((ACTOR/'manifest.json').read_text(encoding='utf8'))
    frames=prepare.inventory(manifest);action=manifest['actions']['explore_run_W01']
    images=list(dict.fromkeys(action['frameImages']));sheets={name:Image.open(ACTOR/name).convert('RGBA') for name in images}
    cloud=Image.open(HERE/'rear-run-cloud.png').convert('RGBA');cloud=cloud.resize((1088,round(cloud.height*1088/cloud.width)),Image.Resampling.LANCZOS).crop((0,0,1088,344))
    updated=copy.deepcopy(manifest);geometries={};changes=[]
    for page,name in enumerate(images):
        items=[]
        for di,direction in enumerate(manifest['directions']):
            for local in range(4):
                phase=page*4+local;r=prepare.find(frames,'explore_run_W01',direction,phase)
                x,y,w,h=r['rect'];original=sheets[name].crop((x,y,x+w,y+h));crop=original;origin=np.asarray(r['origin'],float)
                if direction=='up' and phase in PHASES:
                    donor=Image.new('RGBA',(512,768));donor.alpha_composite(cloud.crop((PHASES.index(phase)*272,0,(PHASES.index(phase)+1)*272,344)),(120,400))
                    # A small native border allows corrected ankles to expand
                    # without cutting into neighbouring packed atlas frames.
                    pad=12;canvas=Image.new('RGBA',(w+pad*2,h+pad*2));canvas.paste(original,(pad,pad));origin=origin+pad
                    scale=r['scale'];mapping=(scale,0,256-origin[0]*scale,0,scale,712-origin[1]*scale)
                    pixels=donor.convert('RGBa').transform(canvas.size,Image.Transform.AFFINE,mapping,Image.Resampling.BICUBIC).convert('RGBA')
                    old=np.asarray(canvas).copy();new=np.asarray(pixels).copy();yy=np.arange(canvas.height)*scale+712-origin[1]*scale
                    blend=np.clip((yy-475)/30,0,1);blend=blend*blend*(3-2*blend)
                    # Premultiplied interpolation avoids dark transparent rims.
                    a=np.asarray(canvas.convert('RGBa'),float);b=np.asarray(pixels.convert('RGBa'),float)
                    result=Image.fromarray(np.rint(a*(1-blend[:,None,None])+b*blend[:,None,None]).clip(0,255).astype('uint8'),'RGBa').convert('RGBA')
                    after=np.asarray(result).copy();protected=yy<475;after[protected]=old[protected];result=Image.fromarray(after)
                    assert np.array_equal(after[protected],old[protected]),'Upper body must remain byte-identical'
                    box=result.getchannel('A').getbbox();box=(max(0,box[0]-2),max(0,box[1]-2),min(result.width,box[2]+2),min(result.height,box[3]+2))
                    crop=result.crop(box);origin=origin-np.asarray(box[:2]);changes.append(dict(direction=direction,phase=phase,protectedRowsExact=True,origin=origin.tolist()))
                items.append(dict(record=dict(index=di*4+local),crop=crop,origin=origin.tolist()))
        placements,size,_=packer.shelf_placements(items);atlas=Image.new('RGBA',size);geometry={}
        for item in items:
            index=item['record']['index'];x,y,w,h=placements[index];atlas.paste(item['crop'],(x,y));geometry[index]=dict(rect=[x,y,w,h],origin=item['origin'])
        target=STAGE/name;target.parent.mkdir(parents=True,exist_ok=True);atlas.save(target);geometries[name]=geometry
    for name,a in updated['actions'].items():
        if a.get('sharedBody')!='raphael-locomotion-v3' or 'run' not in name:continue
        a['frameRectsByImage']={image.removesuffix('.png'):[geometries[image][i]['rect'] for i in range(16)] for image in images}
        a['perFrameRects']=a['frameRectsByImage'][images[0].removesuffix('.png')]
        a['perFrameOrigins']={d:[geometries[images[p//4]][di*4+p%4]['origin'] for p in range(8)] for di,d in enumerate(manifest['directions'])}
    write(STAGE/'manifest.json',updated)
    write(HERE/'rear-run-prepare.json',dict(status='candidate; art review pending',sourceManifestSHA256=sha(ACTOR/'manifest.json'),sourceFiles={n:sha(ACTOR/n) for n in images},files={n:sha(STAGE/n) for n in images},manifestSHA256=sha(STAGE/'manifest.json'),changes=changes,cloudCalls=1,scope='four up run lower bodies; exact native pixels above normalized y475 retained',socketsUnchanged=True))
    print('Prepared four rear-run local repairs; original native upper pixels retained.')

def install():
    report=json.loads((HERE/'rear-run-prepare.json').read_text(encoding='utf8'));review=json.loads((HERE/'rear-run-review.json').read_text(encoding='utf8'))
    assert review['status']=='accepted' and review['manifestSHA256']==report['manifestSHA256']
    assert sha(ACTOR/'manifest.json')==report['sourceManifestSHA256']
    for name,expected in report['sourceFiles'].items():assert sha(ACTOR/name)==expected
    for name,expected in report['files'].items():
        assert sha(STAGE/name)==expected;(ACTOR/name).write_bytes((STAGE/name).read_bytes())
    (ACTOR/'manifest.json').write_bytes((STAGE/'manifest.json').read_bytes())
    write(HERE/'rear-run-install.json',dict(status='installed; runtime review pending',manifestSHA256=sha(ACTOR/'manifest.json'),files=report['files']))
    print('Installed accepted rear run calves/boots with existing atlas UUIDs.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
    install() if args.install else build()
