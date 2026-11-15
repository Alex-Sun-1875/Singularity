"""HUD concept: three matching native-skinned meters, inside the original frame."""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
SOURCE=ROOT/'source-art/ui/quest-tracker-expand-v5/collapsed-game-v8.png'
FONT=ART/'rpg-serif-v2.ttf'
FRAME=(177,18,714,208)
PANEL_W,PANEL_H=537,190
INK=(237,228,203,255)
GOLD=(218,174,101,255)
COLORS={'health':(195,93,117),'resource':(123,222,180),'experience':(196,165,237)}
source=Image.open(SOURCE).convert('RGBA')
track=Image.open(ART/'bar-track.png').convert('RGBA')
fill_source=Image.open(ART/'bar-health-fill.png').convert('RGBA')

def font(size):
    return ImageFont.truetype(str(FONT),size)

def caption(image,xy,text,size,color=INK,anchor='lm'):
    d=ImageDraw.Draw(image)
    face=font(size)
    bounds=d.textbbox((0,0),text,font=face,stroke_width=1)
    x=xy[0]-bounds[2] if anchor=='rm' else xy[0]-bounds[0]
    y=xy[1]-(bounds[1]+bounds[3])/2
    d.text((x,y),text,font=face,fill=color,stroke_width=1,stroke_fill=(13,10,8,215))

def nine_slice(image,w,h):
    sx=(0,24,image.width-24,image.width)
    sy=(0,8,image.height-8,image.height)
    dx=(0,24,w-24,w)
    dy=(0,8,h-8,h)
    out=Image.new('RGBA',(w,h))
    for iy in range(3):
        for ix in range(3):
            tile=image.crop((sx[ix],sy[iy],sx[ix+1],sy[iy+1]))
            out.alpha_composite(tile.resize((dx[ix+1]-dx[ix],dy[iy+1]-dy[iy]),Image.Resampling.LANCZOS),(dx[ix],dy[iy]))
    return out

def meter(image,x,cy,left,right,value,color):
    w,h=350,35
    bar=nine_slice(track,w,h)
    # Retain the existing fill's horizontal highlight, with shared semantic tint.
    mono=ImageOps.grayscale(fill_source).resize((w-12,h-10),Image.Resampling.LANCZOS)
    light=ImageOps.colorize(mono,tuple(round(c*.30) for c in color),tuple(round(c*.80) for c in color)).convert('RGBA')
    amount=max(0,min(w-12,round((w-12)*value)))
    pigment=Image.new('RGBA',(w,h))
    pigment.alpha_composite(light.crop((0,0,amount,h-10)),(6,5))
    clip=Image.new('L',(w,h))
    ImageDraw.Draw(clip).polygon([(9,5),(w-9,5),(w-5,9),(w-5,h-9),(w-9,h-5),(9,h-5),(5,h-9),(5,9)],fill=255)
    pigment.putalpha(ImageChops.multiply(pigment.getchannel('A'),clip))
    bar.alpha_composite(pigment)
    # Preserve every gold rim highlight above the tinted interior. The track's
    # opaque black center is a backdrop, rather than a second fill layer.
    rim=nine_slice(track,w,h)
    rim.putalpha(ImageChops.multiply(rim.getchannel('A'),ImageOps.grayscale(rim).point(lambda p:min(255,p*4))))
    bar.alpha_composite(rim)
    image.alpha_composite(bar,(x,round(cy-h/2)))
    caption(image,(x+15,cy),left,29)
    caption(image,(x+w-15,cy),right,29,anchor='rm')
    return {'label':left,'right':right,'fraction':value,'sourceBounds':[x,round(cy-h/2),w,h],'fontSourcePixels':29}

proposal=source.copy()
# Reuse the panel's own empty material strip; preserve frame, portrait and gold.
material=source.crop((315,78,335,159)).resize((374,171),Image.Resampling.BICUBIC)
mask=Image.new('L',material.size)
ImageDraw.Draw(mask).rounded_rectangle((0,0,material.width-1,material.height-1),radius=3,fill=255)
material.putalpha(mask)
proposal.alpha_composite(material,(332,29))
caption(proposal,(342,49),'拉斐尔 · Lv4',36,GOLD)
rows=[
 meter(proposal,342,90,'生命','85 / 135',85/135,COLORS['health']),
 meter(proposal,342,132,'专注','80 / 100',.8,COLORS['resource']),
 meter(proposal,342,174,'经验','还需 200',290/490,COLORS['experience']),
]
proposal.convert('RGB').save(HERE/'scene-preview.png')
phone=ImageOps.fit(proposal,(2532,1170),method=Image.Resampling.LANCZOS)
phone.convert('RGB').save(HERE/'phone-preview.png')
detail=proposal.crop(FRAME).resize((PANEL_W*2,PANEL_H*2),Image.Resampling.LANCZOS)
detail.convert('RGB').save(HERE/'hero-detail.png')

board=Image.new('RGBA',(1600,940),(23,22,20,255))
caption(board,(65,58),'经验也使用完整进度条',36,GOLD)
caption(board,(66,111),'三条同一套切角金边；经验填充表示本级进度，条内直接显示还需多少。',22,(194,176,150,255))
board.alpha_composite(detail,(64,166))
caption(board,(1180,213),'生命',26,GOLD)
caption(board,(1180,251),'数值与填充一体',21)
caption(board,(1180,326),'职业资源',26,GOLD)
caption(board,(1180,364),'随职业保留原色',21)
caption(board,(1180,439),'经验',26,GOLD)
caption(board,(1180,477),'当前进度 + 升级差额',21)
caption(board,(65,590),'外框宽高不变 · 头像、金币和任务位置不变 · 不新增点击区域',24,INK)
small=phone.resize((633,293),Image.Resampling.LANCZOS)
board.alpha_composite(small,(65,625))
caption(board,(750,663),'示例 Lv4：290 / 490',24,GOLD)
caption(board,(750,708),'经验条填充约59%，右侧显示“还需 200”。',22)
caption(board,(750,758),'满级显示“已满级”，不显示“还需 0”。',22)
caption(board,(750,808),'完整经验数值保留在人物详情中。',22)
caption(board,(750,878),'同高 UI 设计稿 · 尚未接入游戏',19,(170,151,124,255))
board.convert('RGB').save(HERE/'design-review.png')

# Geometry and text-fit checks on the actual rendered layout.
for row in rows:
    x,y,w,h=row['sourceBounds']
    assert FRAME[0]<=x and x+w<=FRAME[2] and FRAME[1]<=y and y+h<=FRAME[3]
long=font(29).getlength('经验')+font(29).getlength('还需 38,290')
assert long<350-30-20
modified=ImageChops.difference(source,proposal).convert('RGB').getbbox()
assert FRAME[0]<=modified[0] and FRAME[1]<=modified[1] and modified[2]<=FRAME[2] and modified[3]<=FRAME[3]
record={
 'createdOn':'2026-11-15',
 'purpose':'按用户反馈将经验重设计为与生命/职业资源统一的第三条完整进度条；不接入游戏',
 'method':'Deterministic Pillow layout using the original screenshot material, native bar-track/fill skins, and bundled RPG font; no image generation or new runtime asset',
 'source':str(SOURCE.relative_to(ROOT)),
 'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'frame':{'sourceBounds':list(FRAME),'sourceSize':[PANEL_W,PANEL_H],'heightAdded':0,'widthAdded':0,'creatorSize':[328,116],'logicalSizeAt844x390':[328*390/720,116*390/720]},
 'rows':rows,
 'sample':{'level':4,'thisLevelXp':290,'xpToNextLevel':490,'remaining':200,'progress':290/490},
 'maxLevel':'Full experience bar with 已满级; no remaining zero.',
 'detail':'Full current/required XP stays in the existing character detail page; remaining XP is always visible on HUD.',
 'resource':'BOW focus shown using resource.focus; actual resource name and color follow profession.',
 'savedCheck':'Remove the saved check from the proposed frame; pause already contains save state. Persistence unchanged.',
 'touchTargetsAdded':False,
 'checks':{'allMetersInsideOriginalFrame':True,'worstRemaining38290Fits':True,'fontSizeLogical':29/3,'sameNativeFrameSize':True,'onlyModifiedInsideHeroFrame':True,'modifiedBounds':list(modified)},
 'artReview':{'assistantStatus':'pending visual review','userApproved':False},
 'runtimeChanged':False,
 'outputs':['design-review.png','hero-detail.png','phone-preview.png','scene-preview.png']
}
(HERE/'design.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record['checks'],ensure_ascii=False))
