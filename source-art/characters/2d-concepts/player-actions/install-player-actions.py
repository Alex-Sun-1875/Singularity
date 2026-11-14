"""Copy approved ImageGen outputs verbatim and read alpha-only frame metadata.

No Pillow pixel editing, compositing, drawing, resizing or image save is used.
This installer updates the existing hero manifest without replacing its actions.
"""
from pathlib import Path
import hashlib,json,shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[4]
SOURCE=Path(__file__).parent
DEST=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
GENERATED=Path('C:/Users/Alexa/.codex/generated_images/01a1ac88-2166-7010-8a94-e094f8c74b25')
SPECS={
 'walk-bow':{'file':'exec-4257cf04-c837-40b9-919a-77558dcd2f0a.png','actions':{
   'idle_bow':{'frames':1,'frameIndices':[0],'fps':1,'loop':True},
   'walk_bow':{'frames':4,'frameIndices':[1,2,3,2],'fps':7,'loop':True}},
   'note':'ImageGen correction removed the erroneous sword from row 2 column 4. Bow and quiver retained.'},
 'walk-staff':{'file':'exec-06f6ff62-7a94-48c2-86fb-2adac1d91acf.png','actions':{
   'idle_staff':{'frames':1,'frameIndices':[0],'fps':1,'loop':True},
   'walk_staff':{'frames':4,'frameIndices':[1,2,3,2],'fps':7,'loop':True}},
   'note':'Actual staff carried in every idle/walk direction.'},
 'attack-staff':{'file':'exec-0742d272-887e-46ff-898d-d4883cc61741.png','actions':{
   'attack_staff':{'frames':4,'frameIndices':[0,1,2,3],'fps':6,'loop':False,'phaseStarts':[0,.14,.28,.62]}},
   'note':'Column 3 is the forward contact/cast pose. Staff emission at .20/.70 ~= .286 normalized gameplay phase.'},
 'hit-death':{'file':'exec-ce22cf04-c64f-4ee8-bac1-529bdb9d3a6f.png','actions':{
   'hit':{'frames':1,'frameIndices':[0],'fps':1,'loop':False},
   'death':{'frames':3,'frameIndices':[1,2,3],'fps':5,'loop':False,'phaseStarts':[0,.25,.65]}},
   'note':'Hit uses column 1 only. Death progresses through kneeling, falling and the fully horizontal final pose; shared upright hit-frame size reference.'},
 'spell-interact':{'file':'exec-d2f425e0-8c8c-444f-bd0b-b167b39f0bf6.png','actions':{
   'spell':{'frames':2,'frameIndices':[0,1],'fps':6,'loop':False,'phaseStarts':[0,.5]},
   'interact':{'frames':2,'frameIndices':[2,3],'fps':6,'loop':False,'phaseStarts':[0,.18]}},
   'note':'Spell release pose matches .25/.45 seconds; interact contact pose matches push contact .10/.50 seconds.'},
 'attack-bow':{'file':'exec-49082c2f-db79-4d35-bc6f-27a1cd941b71.png','actions':{
   'attack_bow':{'frames':4,'frameIndices':[0,1,2,3],'fps':6,'loop':False,'phaseStarts':[0,.2,.5,.75]}},
   'note':'Approved compact bow replacement with every tip inside its cell. Ready/draw/full/release; aim holds full below .75, release samples .75..1.'},
 'dodge':{'file':'C:/Users/Alexa/.codex/generated_images/01a1ac8b-4f84-7042-a97f-489a37ac8433/exec-2a698e20-3985-4475-94a0-11b2c8cd5936.png',
   'targetProjectedHeightMetres':.98,'minimumMargin':12,
   'editInput':'exec-ae0525a6-1869-4b4b-b842-c48a6da2d632.png',
   'editPromptRecord':'dodge-reframe-generation.json',
   'actions':{'dodge':{'frames':4,'frameIndices':[0,1,2,3],'fps':12,'loop':False,'phaseStarts':[0,.12,.36,.65]}},
   'note':'One ImageGen-only framing correction retained all 16 crouch/roll poses, minimum 16-pixel foreground margin. First deep crouch is 0.98m projected height, not standing scale.'},
 'run':{'file':'C:/Users/Alexa/.codex/generated_images/01a1ac8b-4f84-7042-a97f-489a37ac8433/exec-067d410b-4c06-4bc0-9100-c74a8392c631.png',
   'editInput':'exec-416e819c-b722-445d-8a8e-886603299f1c.png','editPromptRecord':'run-alpha-generation.json',
   'actions':{'run':{'frames':4,'frameIndices':[0,1,2,3],'fps':10,'loop':True}},
   'note':'ImageGen-only background extraction removed the original semitransparent grey fog, retaining the 1536x1024 layout and all sixteen running poses.'},
}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return Path(path).relative_to(ROOT).as_posix()
def pixels(image):
 return image.get_flattened_data()if hasattr(image,'get_flattened_data')else image.getdata()

manifest_path=DEST/'manifest.json'
manifest=json.loads(manifest_path.read_text(encoding='utf8'))
base_bounds=manifest['alphaBounds'][0]
base_projected=(base_bounds[3]-base_bounds[1])*manifest['camera']['worldUnitsPerPixel']
design=ROOT/manifest['sourceDesign']
records_path=SOURCE/'install-records.json'
records=json.loads(records_path.read_text(encoding='utf8'))if records_path.exists()else{}

for name,spec in SPECS.items():
 generated=GENERATED/spec['file']
 source=SOURCE/(name+'.png');shutil.copyfile(generated,source)
 image=Image.open(source)
 assert image.mode=='RGBA',(name,'RGBA required')
 w,h=image.size
 assert w%4==h%4==0,(name,'Expected regular 4 by 4 atlas')
 fw,fh=w//4,h//4
 assert fw==manifest['frameWidth']and fh==manifest['frameHeight'],(name,'Frame dimensions differ; renderer needs action frame dimensions')
 alpha=image.getchannel('A');bounds=[];origins=[];edges=[]
 threshold=32
 for row in range(4):
  for column in range(4):
   cell=alpha.crop((column*fw,row*fh,(column+1)*fw,(row+1)*fh))
   box=cell.point(lambda a:255 if a>threshold else 0).getbbox()
   assert box,(name,row,column,'Empty source frame')
   left,top,right,bottom=box;bounds.append(list(box))
   margin=min(left,top,fw-right,fh-bottom)
   assert margin>=spec.get('minimumMargin',1),(name,row,column,'Foreground touches cell edge',box)
   # Include both feet/hands in the lower support region. The old lowest-row
   # pixel median alternated between individual feet and moved run poses by
   # almost a metre despite a stable torso in the source drawing.
   support_top=max(top,bottom-round((bottom-top)*.30))
   support=cell.crop((left,support_top,right,bottom)).point(lambda a:255 if a>threshold else 0).getbbox()
   origins.append([round(left+(support[0]+support[2])/2),bottom])
   edges.append(max(max(pixels(cell.crop((0,0,fw,1)))),max(pixels(cell.crop((0,fh-1,fw,fh)))),max(pixels(cell.crop((0,0,1,fh)))),max(pixels(cell.crop((fw-1,0,fw,fh))))))
 # In all three supplied atlases, front/guard frame zero has upright head and
 # feet. Sample only the central upper-body band: bows/staff tips at the side
 # must not become a false top-of-head size reference.
 head_band=[round(fw*.42),0,round(fw*.66),round(fh*.25)]
 upper=alpha.crop(tuple(head_band)).point(lambda a:255 if a>threshold else 0).getbbox()
 assert upper,(name,'Missing central head-height reference')
 head_y=upper[1]
 body_pixels=origins[0][1]-head_y
 target_projected=spec.get('targetProjectedHeightMetres',base_projected)
 upp=target_projected/body_pixels
 target=DEST/(name+'.png');shutil.copyfile(source,target)
 assert generated.read_bytes()==source.read_bytes()==target.read_bytes()
 source_hash=sha(source)
 for action,profile in spec['actions'].items():
  manifest['actions'][action]={**profile,'image':target.name,'columns':4,
    'perFrameOrigins':origins,'originMethod':'Horizontal bounds midpoint of lower 30% alpha>32 support region; original sole Y retained',
    'alphaBounds':bounds,'alphaBoundsThreshold':threshold,
    'worldUnitsPerPixel':upp,'sourcePNG':rel(source),'sourcePNGSHA256':source_hash,
    'sourceDesign':rel(design),'sourceDesignSHA256':sha(design),
    'bodyScaleReference':{'frameIndex':0,'headSearchBand':head_band,'headTopY':head_y,
      'soleY':origins[0][1],'bodyHeightPixels':body_pixels,'targetProjectedBodyHeightMetres':target_projected,
      'method':'Central hair/head alpha top and sole in upright front/guard frame; excludes side prop tips'},
    'notes':spec['note']}
 records[name]={'generatedInput':str(generated),'generatedInputSHA256':sha(generated),
   'sourcePNG':rel(source),'sourcePNGSHA256':source_hash,'runtimePNG':rel(target),'runtimePNGSHA256':sha(target),
   'sourceDesign':rel(design),'sourceDesignSHA256':sha(design),'generationTool':'built-in image_gen.imagegen',
   'pixelEditsAfterGeneration':False,'layout':'4 columns by 4 direction rows: down/right/up/left',
   'size':[w,h],'frameSize':[fw,fh],'alphaExtrema':alpha.getextrema(),'alphaBoundsThreshold':threshold,
   'alphaBounds':bounds,'perFrameOrigins':origins,'originMethod':manifest['actions'][next(iter(spec['actions']))]['originMethod'],
   'cellBorderMaxAlpha':edges,'worldUnitsPerPixel':upp,
   'bodyScaleReference':manifest['actions'][next(iter(spec['actions']))]['bodyScaleReference'],
   'actions':list(spec['actions']),'notes':spec['note'],'pngBytes':target.stat().st_size,'estimatedRGBABytes':w*h*4}
 if spec.get('editInput'):
  edit_input=GENERATED/spec['editInput']
  records[name]['imagegenEditInput']={'path':str(edit_input),'sha256':sha(edit_input),'promptRecord':rel(SOURCE/spec['editPromptRecord'])}

manifest['actions']['attack_sword']['phaseStarts']=[0,.15,.28,.6]
manifest['actions']['attack_sword']['phaseNotes']='Gameplay contact .12-.22 seconds of .44-second sword action; contact drawing begins at normalized .28.'
manifest['sourceDesignSHA256']=sha(design)
manifest['playerActionInstallRecord']=rel(records_path)
canonical=['idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact']
manifest['canonicalActions']=canonical
manifest['canonicalCoverage']={name:name in manifest['actions']for name in canonical}
manifest['additionalWeaponVariants']=['idle_bow','walk_bow','idle_staff','walk_staff']
manifest['limitations']=[
 'Four-direction 2D drawings derived from the approved design; small generative costume details can vary across source sheets.',
 'Run/dodge/hit/death/spell/interact are shared character drawings, without separate held-bow/staff variants; held weapon idle/walk and attack variants are explicit.',
 'Equipment tiers do not each have distinct costume/weapon drawings. This manifest does not claim coverage beyond its listed actions and four weapon variants.',
 'Original generated PNG bytes retained; alphaBounds ignore alpha <=32 antialiased tails.']
manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
records_path.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({name:{key:record[key]for key in ['size','frameSize','alphaExtrema','cellBorderMaxAlpha','worldUnitsPerPixel','actions','pngBytes']}for name,record in records.items()},ensure_ascii=False,indent=2))
