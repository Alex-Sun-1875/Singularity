"""Deterministic composition using approved UI skin pixels and an unchanged-scale HUD.
Run with the bundled Python runtime. The fixed entry portrait is generated separately.
"""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=HERE/'assets'
UI=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
OUT.mkdir(exist_ok=True)

def sliced(name,w,h,factor=1.5,edge=48):
    im=Image.open(UI/(name+'.png')).convert('RGBA')
    out=Image.new('RGBA',(w,h))
    e=min(round(edge*factor),w//2,h//2)
    sx=(0,edge,im.width-edge,im.width);sy=(0,edge,im.height-edge,im.height)
    dx=(0,e,w-e,w);dy=(0,e,h-e,h)
    for y in range(3):
        for x in range(3):
            size=(dx[x+1]-dx[x],dy[y+1]-dy[y])
            if min(size)>0:
                tile=im.crop((sx[x],sy[y],sx[x+1],sy[y+1])).resize(size,Image.Resampling.LANCZOS)
                out.alpha_composite(tile,(dx[x],dy[y]))
    return out

def panel(name,w,h):
    w*=3;h*=3
    base=sliced('double-gold-inset-v6',w,h)
    base.alpha_composite(sliced('double-gold-frame-v6',w,h))
    base.save(OUT/(name+'.png'))

panel('notice',310,52)
panel('target-panel',306,280)
panel('target-panel-one',306,220)
panel('target-panel-empty',306,224)
panel('quest-compact',177,35)
panel('quest-expanded',177,56)

# Capsule ends follow the source height, matching DoubleGoldFrame fitHeight.
for name,w,h in [('automatic',128,25),('map-label',104,24)]:
    fw,fh=w*3,h*3
    out=Image.new('RGBA',(fw,fh))
    for source in ['menu-pill-inset-v5','menu-pill-frame-v5']:
        src=Image.open(UI/(source+'.png')).convert('RGBA')
        scale=fh/src.height;e=round(64*scale)
        for a,b,c,d in [(0,64,0,e),(64,src.width-64,e,fw-e),(src.width-64,src.width,fw-e,fw)]:
            out.alpha_composite(src.crop((a,0,b,src.height)).resize((d-c,fh),Image.Resampling.LANCZOS),(c,0))
    out.save(OUT/(name+'.png'))

source=ROOT/'source-art/ui/quest-tracker-expand-v5/collapsed-game-v8.png'
scene=Image.open(source).convert('RGBA')
# Remove only debug/old central labels; no enlarged or shifted gameplay scene.
# Clone adjacent ground, feather outside the removed text footprint.
def ground_patch(box,source_box):
    patch=scene.crop(source_box).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.BICUBIC)
    mask=Image.new('L',patch.size)
    d=ImageDraw.Draw(mask);d.rectangle((16,16,patch.width-16,patch.height-16),fill=255)
    mask=mask.filter(ImageFilter.GaussianBlur(7))
    scene.paste(patch,box[:2],mask)

ground_patch((895,-20,1690,330),(25,400,820,675))
scene=scene.resize((2532,1170),Image.Resampling.LANCZOS)
# The preview's level selector changes only the name line; other HUD pixels stay intact.
name_patch=scene.crop((606,30,627,73)).resize((294,43),Image.Resampling.BICUBIC)
scene.paste(name_patch,(332,30))
scene.save(OUT/'scene.png')

# Reuse existing pictograms; all four minimap tools share one 28px gold housing.
Image.open(UI/'hud-skill-face-v19.png').convert('RGBA').crop((300,300,724,724)).resize((144,144),Image.Resampling.LANCZOS).save(OUT/'tool-face.png')
for key in ['inventory','checks']:
    icon=Image.open(ROOT/f'src/cocos/assets/resources/ui/icons/{key}.png').convert('RGBA')
    ink=Image.new('RGBA',icon.size,(237,228,203,255));ink.putalpha(icon.getchannel('A'))
    ink.save(OUT/f'tool-{key}.png')
gear=scene.crop((2078,411,2138,471)).convert('RGB')
alpha=gear.convert('L').point(lambda p:max(0,min(255,round((p-65)*255/155))))
ink=Image.new('RGBA',gear.size,(237,228,203,255));ink.putalpha(alpha)
ink.save(OUT/'tool-settings.png')

# Keep the generated fixed entry identity separate from individual boss portraits.
fixed_source=HERE/'art/boss-entry-beast-v1-generated.png'
if fixed_source.exists():
    head=Image.open(fixed_source).convert('RGBA')
    bounds=head.getchannel('A').point(lambda p:255 if p>=12 else 0).getbbox()
    head=head.crop(bounds);head.thumbnail((88,88),Image.Resampling.LANCZOS)
    fixed=Image.new('RGBA',(96,96));fixed.alpha_composite(head,((96-head.width)//2,(96-head.height)//2))
    fixed.save(OUT/'boss-entry-beast-v1.png')

# Keep the reference row metal perimeter, remove the source skill icon remnants.
for source_name,output_name in [('prep-skill-row-v5','row'),('prep-skill-selected-v5','row-selected')]:
    im=Image.open(UI/(source_name+'.png')).convert('RGBA')
    if output_name=='row-selected':
        top=im.crop((400,0,450,12)).resize((im.width-48,12),Image.Resampling.LANCZOS)
        bottom=im.crop((400,im.height-12,450,im.height)).resize((im.width-48,12),Image.Resampling.LANCZOS)
        im.paste(top,(24,0));im.paste(bottom,(24,im.height-12))
    # Empty material is already approved in the unselected reference row.
    if output_name=='row-selected':
        mask=Image.new('L',im.size);d=ImageDraw.Draw(mask)
        d.rounded_rectangle((0,0,im.width-1,im.height-1),radius=20,fill=255)
        d.rounded_rectangle((12,12,im.width-13,im.height-13),radius=9,fill=0)
        from PIL import ImageChops
        im.putalpha(ImageChops.multiply(im.getchannel('A'),mask))
    im.save(OUT/(output_name+'.png'))

# Per-character head framing, including the beast's low face and the complete trio.
actors={'warden':'boss-r2','huntmaster':'elite-02','golem':'elite-05','oath':'elite-06','overseer':'elite-01','beast':'ridgebreaker','captain':'captain'}
portrait_crops={'warden':(92,17,164,89),'huntmaster':(100,17,172,89),
 'golem':(82,48,174,140),'oath':(44,22,204,182),
 'overseer':(95,22,167,94),'beast':(59,105,163,209),'captain':(156,17,228,89)}
for key,actor in actors.items():
    src=ROOT/f'src/cocos/assets/resources/flat2d/characters/{actor}/atlas.png'
    if not src.exists():continue
    manifest=json.loads((src.parent/'manifest.json').read_text())
    frame=Image.open(src).convert('RGBA').crop((0,0,manifest['frameWidth'],manifest['frameHeight']))
    crop=frame.crop(portrait_crops[key])
    crop=crop.resize((132,132),Image.Resampling.LANCZOS)
    # Only the face material, not the skill button's inner ornament, backs portraits.
    disc=Image.open(UI/'hud-skill-face-v19.png').convert('RGBA').crop((300,300,724,724)).resize((132,132),Image.Resampling.LANCZOS)
    disc.alpha_composite(crop)
    mask=Image.new('L',(132,132));ImageDraw.Draw(mask).ellipse((0,0,131,131),fill=255)
    disc.putalpha(ImageChops.multiply(disc.getchannel('A'),mask))
    ring=Image.open(UI/'unified-gold-ring-v16.png').convert('RGBA').resize((144,144),Image.Resampling.LANCZOS)
    result=Image.new('RGBA',(144,144));result.alpha_composite(disc,(6,6));result.alpha_composite(ring)
    result.save(OUT/(key+'.png'))

record={
 'date':'2026-11-15','method':'Pillow deterministic crop, nine-slice composition and source-pixel reuse',
 'designReferenceVersions':['quest-tracker-expand-v5 / approved v8','double-gold-frame-v6','settings-alignment-v11','rpg-alignment-v5','start-menu-v8'],
 'scene':str(source.relative_to(ROOT)),
 'sceneTransform':'Full frame resized once to 2532x1170; no crop, zoom, or relocated player/HUD',
 'removedScenePixels':'Prior central debug/encounter labels and the static name line; native preview text supplies the displayed player level',
 'frameSource':'src/cocos/assets/resources/ui/quiet-bronze/double-gold-frame-v6.png',
 'materialSource':'src/cocos/assets/resources/ui/quiet-bronze/double-gold-inset-v6.png',
 'nineSlice':{'sourceInset':48,'physicalScale':1.5,'renderDensity':3},
 'revision':'fixed-beast-entry-single-housing',
 'layout':{'panelWidth':306,'panelHeightWithTwoRows':280,'panelHeightWithOneRow':220,'emptyPanelHeight':224,'noticeSize':[310,52],'noticeTop':54,'automaticVisualBottom':46,'visibleNoticeGap':8,'rowHeight':52,'gap':8,'navigationDefault':'collapsed'},
 'eligibility':{'levelDelta':5,'inclusive':True,'chapterTabs':False,'emptyBehavior':'Show an empty state; never widen the range automatically'},
 'entry':'Explicit 首领 button on the existing lower-right minimap rim mount; map body no longer opens the list',
 'entryIdentity':{'asset':'assets/boss-entry-beast-v1.png','source':'art/boss-entry-beast-v1-generated.png','provenance':'art/boss-entry-beast-v1.provenance.json','fixedAcrossTargets':True,'intrinsicRing':False,'iconBox':20,'inventoryLabel':'背包','displayTreatment':{'brightness':0.93,'saturation':0.72,'sepia':0.18},'badge':{'right':9,'bottom':9,'diameter':11,'relationship':'Overlaps lower-right housing perimeter'}},
 'minimapTools':{'visibleDiameter':28,'hitDiameter':48,'minimumCircularHitGap':8,'commonHousing':'Only the central plain material of hud-skill-face-v19 + one outer unified-gold-ring-v16; no nested inner ornament','actions':['inventory','checks','settings','boss']},
 'noticeLifetimeMs':10000,
 'portraits':{'method':'Individual head/face framing from existing runtime identity sprites, no regenerated characters','cropRects':portrait_crops},
 'restored':['title and stag crest','enemy identity portraits','selected row','follow reminder and automatic travel actions'],
 'generatedArt':True,'implementedInGame':False,'userApproved':False,'platformValidated':False
}
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print('Prepared approved skin assets and unchanged-scale scene')
