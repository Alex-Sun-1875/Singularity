"""Deterministic icon extraction from existing, explicitly mapped cloud plates.

No model, download or dependency installation. Pillow/numpy/scipy are already
installed. Source plates and their generation provenance remain untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import uuid
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/encounters/cloud-world-v2'
OUTPUT=SOURCE/'equipment-runtime-v1'

def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()

def alpha_cut(image:Image.Image,max_components:int=1,paper_threshold:int=26)->Image.Image:
    """Fit the photographed paper at the crop perimeter, retaining source RGB.

    Robust least squares handles the warm paper gradient. SciPy's connected
    component filter removes detached paper noise; it does not invent pixels.
    Every output still needs the separate visual review recorded in review.json.
    """
    rgb=np.asarray(image.convert('RGB'),dtype=np.float64);h,w=rgb.shape[:2]
    yy,xx=np.mgrid[:h,:w];x=xx/max(1,w-1);y=yy/max(1,h-1)
    edge=(xx<8)|(xx>=w-8)|(yy<8)|(yy>=h-8)
    a=np.stack([np.ones_like(x),x,y],axis=-1)
    samples=a[edge];colors=rgb[edge];keep=np.ones(len(samples),dtype=bool)
    for _ in range(4):
        coefficients=np.linalg.lstsq(samples[keep],colors[keep],rcond=None)[0]
        residual=np.linalg.norm(colors-samples@coefficients,axis=1)
        keep=residual<=max(12,float(np.quantile(residual,.75)))
    distance=np.linalg.norm(rgb-a@coefficients,axis=2)
    alpha=np.clip((distance-paper_threshold)/25,0,1)
    labels,count=ndimage.label(ndimage.binary_closing(alpha>.4,iterations=2))
    sizes=np.bincount(labels.ravel());sizes[0]=0
    if count:
        cutoff=max(120,int(sizes.max()*.025))
        accepted=sorted(np.flatnonzero(sizes>=cutoff),key=lambda label:sizes[label],reverse=True)[:max_components]
        core=np.isin(labels,accepted)
        alpha*=ndimage.binary_dilation(core,iterations=3)
    result=image.convert('RGBA');result.putalpha(Image.fromarray(np.uint8(alpha*255)))
    bounds=result.getchannel('A').point(lambda v:255 if v>24 else 0).getbbox()
    if not bounds:raise ValueError('No item foreground in crop')
    return result.crop(bounds)

def mappings()->list[dict]:
    records=[]
    for region in ['R1','R2','R3','R4','U1','U2']:
        filename='drops-u2-v2.png' if region=='U2' else f'drops-{region.lower()}.png'
        for i in range(4):
            x=i%2*768;y=i//2*512
            bounds=[x,y,x+768,y+512]
            if region=='U2' and i==2:bounds=[0,450,750,1024] # selected necklace repair region, includes the complete chain
            if region=='R3' and i==2:bounds=[0,480,1050,1024] # the long curved blade extends beyond the nominal left quadrant
            records.append({'id':f'D{region}-{i+1:02}','file':filename,'rect':bounds})
    # These are authored image bounds, not equal grid cells. In particular the
    # long DE06 blade crosses its nominal grid column; a 4x2 grid clips it and
    # accidentally includes a piece of DE07's wheel shield.
    elite_bounds=[[20,60,390,435],[425,0,670,460],[690,20,1095,460],[1100,20,1536,460],
                  [25,455,315,1024],[295,435,660,1024],[665,475,1120,990],[1135,500,1536,960]]
    for i,bounds in enumerate(elite_bounds):
        records.append({'id':f'DE{i+1:02}','file':'elite-loot.png','rect':bounds})
    # Explicit permanent-item identities from the selected regional plates.
    # Existing v3 mappings keep priority; historical T03/T06/T08 are excluded.
    legacy={
      'r2-highlands.png': [('W03',[0,850,315,1254]),('A05',[300,850,635,1254]),('W09',[600,850,950,1254]),('J02',[900,850,1254,1254])],
      'r3-bellriver.png': [('W10',[0,850,330,1254]),('W12',[330,850,630,1254]),('J05',[610,850,945,1254]),('A03',[915,850,1254,1254])],
      'r4-greyrock.png': [('W06',[0,920,625,1075]),('J07',[65,1050,520,1254]),('W14',[500,870,940,1254])],
      'u1-oathcity.png': [('W16',[0,900,310,1254]),('A12',[300,880,625,1254]),('W13',[610,840,930,1254]),('A16',[900,880,1254,1254])],
      'u2-catacombs.png': [('J04',[0,920,330,1254]),('A15',[300,880,655,1254]),('J06',[600,880,930,1254])],
    }
    for file,entries in legacy.items():
        records.extend({'id':id,'file':file,'rect':bounds,'mappingAuthority':'selected regional plate permanent-item mapping in cloud-world-v2/README.md'} for id,bounds in entries)
    return records

def main()->None:
    parser=argparse.ArgumentParser();parser.add_argument('--sample',action='store_true');parser.add_argument('--install',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True);(OUTPUT/'icons').mkdir(exist_ok=True)
    catalog=json.loads((ROOT/'source-art/skills/pure-skills-v2/campaign-v8.json').read_text('utf-8'))
    definitions={item['id']:item for item in catalog['newEquipment']+catalog['legacyEquipment']}
    source_provenance=json.loads((SOURCE/'provenance.json').read_text('utf-8'))
    provenance={entry['file']:entry for entry in source_provenance['entries']}
    records=mappings()
    if args.sample:records=[record for record in records if record['id'] in ['DR1-01','DR2-03','DU2-03','DE06']]
    output=[]
    for record in records:
        source=SOURCE/record['file'];definition=definitions[record['id']]
        paired={'DR1-03','DR2-01','DR3-01','DR3-02','DU1-03','DU2-01','DU2-02','DE03','DE04','A12','A15','A16','J07'}
        with Image.open(source) as image:cut=alpha_cut(image.crop(record['rect']),2 if record['id'] in paired else 1,17 if record['id'] in ['DU2-03','DR2-04','J07'] else 26)
        # Equal icon canvas and margins preserve aspect, without warping an item.
        cut.thumbnail((440,440),Image.Resampling.LANCZOS)
        icon=Image.new('RGBA',(512,512));icon.alpha_composite(cut,((512-cut.width)//2,(512-cut.height)//2))
        target=OUTPUT/'icons'/f"{record['id'].lower()}.png";icon.save(target)
        alpha=icon.getchannel('A')
        output.append({**record,'name':definition['name'],'sourceSha256':sha(source),'sourceGeneration':provenance[record['file']]['generation'],'sourceConceptReview':provenance[record['file']]['artReview'],'output':str(target.relative_to(ROOT)).replace('\\','/'),'outputSha256':sha(target),'canvas':[512,512],'alphaExtrema':list(alpha.getextrema()),'alphaBounds':list(alpha.getbbox()),'resource':f"equipment/campaign-v1/icons/{record['id'].lower()}",'processing':'perimeter paper fit; source RGB retained; component mask; aspect-preserving thumbnail; transparent centered canvas','artAcceptance':'pending-output-visual-review'})
    manifest={'schemaVersion':1,'generation':'existing OpenAI image_gen plates only; no new generation','processing':'Pillow/numpy/scipy deterministic processing; no model invoked','sample':args.sample,'entries':output}
    (OUTPUT/('sample-manifest.json' if args.sample else 'manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    cols=4 if args.sample else 8;cell=180;rows=(len(output)+cols-1)//cols
    contact=Image.new('RGB',(cols*cell,rows*(cell+28)),(37,37,40));draw=ImageDraw.Draw(contact)
    for i,record in enumerate(output):
        x=i%cols*cell;y=i//cols*(cell+28)
        # A dark game-like well exposes parchment remnants and edge halos.
        tile=Image.new('RGBA',(cell,cell),(43,42,43,255))
        with Image.open(ROOT/record['output']) as image:
            image.thumbnail((cell-10,cell-10));tile.alpha_composite(image,((cell-image.width)//2,(cell-image.height)//2))
        contact.paste(tile.convert('RGB'),(x,y));draw.text((x+10,y+cell+5),record['id'],fill=(235,216,172))
    contact.save(OUTPUT/('sample-review.jpg' if args.sample else 'icons-review.jpg'),quality=94)
    if not args.sample:
        legacy=[record for record in output if record['id'][0]in ['W','A','J']]
        review=Image.new('RGB',(6*180,3*208),(37,37,40));draw=ImageDraw.Draw(review)
        for i,record in enumerate(legacy):
            x=i%6*180;y=i//6*208
            with Image.open(ROOT/record['output']) as icon:
                icon.thumbnail((170,170));tile=Image.new('RGBA',(180,180),(43,42,43,255));tile.alpha_composite(icon,((180-icon.width)//2,(180-icon.height)//2));review.paste(tile.convert('RGB'),(x,y));draw.text((x+10,y+185),record['id'],fill=(235,216,172))
        review.save(OUTPUT/'legacy-icons-review.jpg',quality=94)
    print(f"Prepared {len(output)} mapped icons; output review remains separate")
    if args.install:
        review=json.loads((OUTPUT/'review.json').read_text('utf-8'))
        accepted=set(review['acceptedIds']);selected=[record for record in output if record['id'] in accepted]
        assert len(selected)==len(accepted) and not args.sample
        target=ROOT/'src/cocos/assets/resources/equipment/campaign-v1';(target/'icons').mkdir(parents=True,exist_ok=True)
        def write_meta(path:Path,kind:str)->None:
            meta=path.with_name(path.name+'.meta')
            if meta.exists():return
            identifier=str(uuid.uuid5(uuid.NAMESPACE_URL,str(path.relative_to(ROOT)).replace('\\','/')))
            if kind=='image':
                template=json.loads((ROOT/'src/cocos/assets/resources/ui/icons/potion-health.png.meta').read_text('utf-8'))
                previous=template['uuid'];template=json.loads(json.dumps(template).replace(previous,identifier).replace('potion-health',path.stem))
                template['subMetas']['6c48a']['userData']['wrapModeS']='clamp-to-edge';template['subMetas']['6c48a']['userData']['wrapModeT']='clamp-to-edge'
            else:template={'ver':'1.2.0' if kind=='directory' else '2.0.1','importer':kind,'imported':True,'uuid':identifier,'files':[] if kind=='directory' else ['.json'],'subMetas':{},'userData':{}}
            meta.write_text(json.dumps(template,indent=2)+'\n','utf-8')
        write_meta(target,'directory');write_meta(target/'icons','directory')
        icons={}
        for record in selected:
            destination=target/'icons'/Path(record['output']).name;shutil.copy2(ROOT/record['output'],destination);write_meta(destination,'image')
            icons[record['id']]={'resource':record['resource'],'rect':[0,0,512,512],'sha256':record['outputSha256'],'name':record['name']}
        index=target/'index.json';index.write_text(json.dumps({'version':1,'icons':icons},ensure_ascii=False,indent=2)+'\n','utf-8');write_meta(index,'json')
        installed={'sourceManifest':str((OUTPUT/'manifest.json').relative_to(ROOT)).replace('\\','/'),'review':'review.json','count':len(selected),'runtimeIndex':str(index.relative_to(ROOT)).replace('\\','/'),'generation':'No new generation. Existing cloud source pixels processed deterministically.','acceptedIds':sorted(accepted)}
        (OUTPUT/'runtime-install.json').write_text(json.dumps(installed,ensure_ascii=False,indent=2)+'\n','utf-8')
        print(f'Installed {len(selected)} reviewed icons and independent runtime index')

if __name__=='__main__':main()
