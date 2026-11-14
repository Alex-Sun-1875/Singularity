"""Inspect existing generated PNGs and write native sprite crop metadata.

This does not edit/resample/repaint image pixels. All artwork was generated with
the built-in image tool; prompts and original paths live in world/sources.json.
Run: python tools/model-pipeline/cocos_flat_world_assets.py
"""
from pathlib import Path
import hashlib,json
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/cocos/assets/resources/flat2d/world'
SPRITES={}
IMAGES={}

def inspect(file,names,columns,rows):
    path=OUT/file
    image=Image.open(path).convert('RGBA')
    width,height=image.size
    token=path.stem
    IMAGES[token]={'resource':'flat2d/world/'+token,'dimensions':[width,height],
                   'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    alpha=image.getchannel('A')
    for index,name in enumerate(names):
        col,row=index%columns,index//columns
        left,top=round(col*width/columns),round(row*height/rows)
        right,bottom=round((col+1)*width/columns),round((row+1)*height/rows)
        # Pixel inspection only: alpha bounds drive runtime SpriteFrame UVs.
        bounds=alpha.crop((left,top,right,bottom)).point(lambda a:255 if a>32 else 0).getbbox()
        if not bounds:raise ValueError('Empty generated sprite cell: '+name)
        x0,y0,x1,y1=bounds
        x0=max(0,x0-2);y0=max(0,y0-2);x1=min(right-left,x1+2);y1=min(bottom-top,y1+2)
        SPRITES[name]={'image':token,'rect':[left+x0,top+y0,x1-x0,y1-y0],
                       'cell':[left,top,right-left,bottom-top],
                       'source':'Built-in ImageGen painted artwork; native SpriteFrame crop only'}

inspect('world-props-v1.png',['oak','birch','pine','rocks','cottage-small','tower-small','tent','ruin','wood-fence','stone-wall','cargo','chest','table-group','shelf','signpost','forge'],4,4)
inspect('small-props-v1.png',['chair','stool','round-table','table','barrel','crate','books','lantern','jug','bowl','candlestick','firepit','grass','fern','stump','door'],4,4)
inspect('structures-v1.png',['pillar','gate','wagon','waterwheel','gravestone','crystal','rope-fence','broken-wall','footbridge'],3,3)
inspect('house-v1.png',['house'],1,1)
inspect('tower-v1.png',['tower'],1,1)
water=OUT/'water-v1.png'
with Image.open(water) as image:
    IMAGES['water-v1']={'resource':'flat2d/world/water-v1','dimensions':list(image.size),'sha256':hashlib.sha256(water.read_bytes()).hexdigest()}
library=json.loads((ROOT/'src/cocos/assets/resources/environment/library.json').read_text())
aliases={key:('rocks' if key.startswith('rocks-') else 'grass' if key.startswith('grass-') else 'fern' if key.startswith('fern-') else 'oak' if key=='tree' else key) for key in library['models']}
assert all(sprite in SPRITES for sprite in aliases.values()),aliases
manifest={'version':'flat-world-v2','status':'source-ready-runtime-review-required',
 'coordinateFrame':'Existing +X/+Z metre coordinates, navigation, colliders and height fields unchanged',
 'coverage':'Every original area uses existing tiled ground/road meshes plus painted cutout objects; S01-T1 retains its validated whole-map painting',
 'images':IMAGES,'sprites':SPRITES,'sourceAssetFamilies':aliases,
 'modelDimensions':{key:model['dimensions'] for key,model in library['models'].items()},
 'groundSources':['surfaces/*-color','surfaces/pbr-v3/*-color'],
 'groundLicenses':'Existing licensed source albedos; see surfaces/pbr-v3 provenance and THIRD_PARTY_NOTICES. No normal maps or photographed models are rendered in the flat presentation.',
 'limits':['Architecture uses shared hand-painted style families; it is not a unique illustration per named building.',
           'Existing albedo scans become repeating unlit map textures; these are genuine textured assets, not newly painted terrain.',
           'Large rock footprints are covered by repeated small painted rock clusters to retain near-camera texel density.',
           'Image generation requested seamless water; actual edge quality still needs the engine visual review.',
           'Source coverage does not establish full first-chapter playthrough or physical-phone performance.']}
target=OUT/'manifest.json'
target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'images':len(IMAGES),'sprites':len(SPRITES),'modelDimensions':len(manifest['modelDimensions']),'output':str(target)},ensure_ascii=False))
