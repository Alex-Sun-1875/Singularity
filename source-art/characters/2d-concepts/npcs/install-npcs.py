"""Install original ImageGen PNG bytes and derive only alpha/anchor metadata.

Pillow is read-only here: no resizing, background editing, drawing or image save.
Run from any directory with the already available Python/Pillow installation.
"""
from pathlib import Path
import hashlib,json,shutil,statistics
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
SOURCE=Path(__file__).parent
DEST=ROOT/'src/cocos/assets/resources/flat2d/characters'
SPECS={
 'lorn':{'name':'洛恩','reference':'explorers-v5-elegant.png','figure':'second from left / historical BRAN label','placements':['S01-T3:t3-lorn'],'prop':'Patched wood-and-steel large shield'},
 'nightqi':{'name':'夜祈','reference':'explorers-v5-recast.png','figure':'third from left / historical LAESA label','placements':['S05:s05-nightqi'],'prop':'Longbow, quiver, high golden wavy ponytail with fine braids'},
 'kael':{'name':'凯尔','reference':'rivals-v5-balanced.png','figure':'leftmost / historical ILO label','placements':['U1-04:u104-kael'],'prop':'Map tube, measuring rope and brass plumb bob'},
 'evelyn':{'name':'伊芙琳·灰','reference':'rivals-v5-balanced.png','figure':'second from left / historical ELIN label','placements':['U1-04:u104-dinner'],'prop':'Small brass furnace lantern with warm glass'},
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return Path(path).relative_to(ROOT).as_posix()

hero_path=DEST/'raphael/manifest.json'
hero=json.loads(hero_path.read_text())
hero_bounds=hero['alphaBounds'][0]
hero_projected=(hero_bounds[3]-hero_bounds[1])*hero['camera']['worldUnitsPerPixel']
hero_scalar=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8-sig'))['profile']['height']
report={}
for identity,spec in SPECS.items():
 source=SOURCE/(identity+'-idle-directions.png')
 image=Image.open(source)
 assert image.mode=='RGBA',(identity,'Expected original RGBA PNG')
 width,height=image.size
 assert width%2==height%2==0,(identity,'2x2 atlas requires even dimensions')
 fw,fh=width//2,height//2
 alpha=image.getchannel('A')
 bounds=[];origins=[];edge_max=[];foreground_pixels=[]
 for index in range(4):
  x=index%2*fw;y=index//2*fh
  cell=alpha.crop((x,y,x+fw,y+fh))
  # Disregard alpha 1..8 edge haze in metadata, retaining original PNG bytes.
  mask=cell.point(lambda a:255 if a>8 else 0)
  box=mask.getbbox();assert box,(identity,index,'Empty figure')
  l,t,r,b=box
  assert l>2 and t>2 and r<fw-2 and b<fh-2,(identity,index,'Cropped figure',box)
  bounds.append(list(box))
  sole_top=max(t,b-max(6,round((b-t)*.075)))
  xs=[]
  for py in range(sole_top,b):
   for px in range(l,r):
    if cell.getpixel((px,py))>96:xs.append(px)
  origins.append([round(statistics.median(xs)) if xs else round((l+r)/2),b])
  edge_max.append(max(max(cell.crop((0,0,fw,1)).getdata()),max(cell.crop((0,fh-1,fw,fh)).getdata()),max(cell.crop((0,0,1,fh)).getdata()),max(cell.crop((fw-1,0,fw,fh)).getdata())))
  foreground_pixels.append(sum(v>8 for v in cell.getdata()))
 original_profile=ROOT/f'src/cocos/assets/resources/actors/{identity}/manifest.json'
 scalar=json.loads(original_profile.read_text(encoding='utf-8-sig'))['profile']['height']
 projected=hero_projected*scalar/hero_scalar
 upp=projected/(bounds[0][3]-bounds[0][1])
 reference=ROOT/'assets/concepts/revision-v5'/spec['reference']
 folder=DEST/identity;folder.mkdir(parents=True,exist_ok=True)
 atlas=folder/'atlas.png';shutil.copyfile(source,atlas)
 assert sha(atlas)==sha(source)
 manifest={
  'id':identity,'name':spec['name'],'revision':'concept-image-npc-idle-v1',
  'sourceDesign':rel(reference),'sourceDesignSHA256':sha(reference),'sourceFigure':spec['figure'],
  'generatedSource':rel(source),'generatedSourceSHA256':sha(source),'atlasSHA256':sha(atlas),
  'generation':{'tool':'built-in image_gen.imagegen','mode':'identity-preserve from approved design','promptRecord':rel(SOURCE/'generation-prompts.json'),'date':'2026-11-06','pixelEditsAfterGeneration':False},
  'loaded3DModel':False,'reusedConcept':False,'image':'atlas.png','columns':2,
  'width':width,'height':height,'frameWidth':fw,'frameHeight':fh,
  'origin':origins[0],'directions':['down','right','up','left'],
  'perFrameOrigins':origins,'alphaBounds':bounds,'alphaBoundsThreshold':8,
  'camera':{'worldUnitsPerPixel':upp},
  'scaleNormalization':{'referenceHeroManifest':rel(hero_path),'referenceHeroManifestSHA256':sha(hero_path),
    'heroProjectedHeightMetres':hero_projected,'actorHeightRatio':scalar/hero_scalar,
    'projectedFigureHeightMetres':projected,'policy':'Match current concept hero scale using existing actor height scalar only; no 3D image/model was rendered or sampled'},
  'actions':{'idle':{'image':'atlas.png','frames':1,'fps':1,'loop':True,'columns':2,'directionFrameIndices':[0,1,2,3]}},
  'chapterPlacements':spec['placements'],'signatureProp':spec['prop'],
  'limitations':['Four direction static idle only; no walking, combat or equipment-swap drawings.',
    'Side/back details are ImageGen derivations from the approved front design; minor small fasteners/straps can vary.',
    'Original generated PNG bytes retained, including sub-8-alpha antialiased edge haze.'],
 }
 (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 report[identity]={'image':rel(atlas),'imageSHA256':sha(atlas),'size':[width,height],
    'frameSize':[fw,fh],'origins':origins,'alphaBounds':bounds,'alphaThreshold':8,
    'alphaExtrema':alpha.getextrema(),'cellBorderMaxAlpha':edge_max,'nonemptyOpaqueFigures':len(bounds),
    'foregroundPixels':foreground_pixels,'originalBytesPreserved':True,'pngBytes':atlas.stat().st_size,
    'estimatedRGBABytes':width*height*4,'worldUnitsPerPixel':upp}
report['totals']={'pngBytes':sum(v['pngBytes']for v in report.values()),
                  'estimatedRGBABytes':sum(v['estimatedRGBABytes']for v in report.values()),
                  'figures':16,'npcCount':4}
(SOURCE/'alpha-and-source-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
