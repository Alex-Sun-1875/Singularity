"""Compose only revised UI state regions into the real screenshots."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import numpy as np
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
UI=ROOT/'src/cocos/assets/resources/ui'
SKIN=UI/'quiet-bronze'
FONT=SKIN/'rpg-serif-v2.ttf'
SOURCES=[
 Path('C:/Users/Alexa/AppData/Local/Temp/codex-clipboard-c63bfe4f-2dd8-4e20-aaad-185ef1c712ee.png'),
 Path('C:/Users/Alexa/AppData/Local/Temp/codex-clipboard-c6a0ae8b-5e2a-4644-803a-54c961dc88de.png')]
CROP=(1140,595,2702,1317)
generated=Image.open(OUT/'material-study-generated.png').convert('RGB')

def f(size):return ImageFont.truetype(str(FONT),size)

def clear_annotations(im):
    values=np.array(im.convert('RGB')).astype(np.float32)
    r,g,b=values[:,:,0],values[:,:,1],values[:,:,2]
    mask=(r>210)&(g<125)&(b<130)&(r>1.75*g)
    mask=np.array(Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.MaxFilter(3)))>0
    original=mask.copy()
    valid=~mask
    values[mask]=0
    for _ in range(18):
        sums=np.zeros_like(values);counts=np.zeros(valid.shape,dtype=np.float32)
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            known=np.roll(valid,(dy,dx),(0,1))
            sums+=np.roll(values,(dy,dx),(0,1))*known[:,:,None]
            counts+=known
        fill=(~valid)&(counts>0)
        values[fill]=sums[fill]/counts[fill,None]
        valid[fill]=True
        if valid.all():break
    result=Image.fromarray(np.clip(values,0,255).astype('uint8'))
    softened=result.filter(ImageFilter.GaussianBlur(.8))
    result.paste(softened,(0,0),Image.fromarray((original*255).astype('uint8')))
    return result

def muted_smoke(im):
    a=np.array(im.convert('RGBA')).astype(float)
    r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    lum=.299*r+.587*g+.114*b
    protect=(r>g*1.15)&(g>b*1.25)&(lum>55)
    strength=(~protect)*.92
    grey=np.stack([lum*1.03,lum*.98,lum*.90],axis=-1)
    a[:,:,:3]=a[:,:,:3]*(1-strength[:,:,None])+grey*strength[:,:,None]
    return Image.fromarray(np.clip(a,0,255).astype('uint8'))

def round_mask(w,h,inset=0,radius=12):
    m=Image.new('L',(w*4,h*4));d=ImageDraw.Draw(m)
    d.rounded_rectangle((inset*4,inset*4,(w-1-inset)*4,(h-1-inset)*4),radius=radius*4,fill=255)
    return m.resize((w,h),Image.Resampling.LANCZOS)

def material_inlay(base,selected=False,palette=None):
    """Retain the reference bronze edge; put patinated material inside it."""
    base=base.convert('RGBA')
    if not selected:return base
    w,h=base.size
    # A text-free field from the generated selected-row material sample.
    metal=generated.crop((604,710,733,749)).resize((w,h),Image.Resampling.LANCZOS)
    grain=np.array(ImageEnhance.Color(metal).enhance(0)).astype(float)[:,:,0]
    body=(palette or {}).get('body',(28,40,32))
    edge=(palette or {}).get('rim',(112,143,130))
    highlight=(palette or {}).get('highlight',(156,173,151))
    toned=np.stack([channel+grain*.55 for channel in body],axis=-1)
    metal=Image.fromarray(np.clip(toned,0,255).astype('uint8')).convert('RGBA')
    mask=round_mask(w,h,4,9).point(lambda alpha:round(alpha*.78))
    base.paste(metal,(0,0),mask)
    rim=Image.new('RGBA',base.size)
    d=ImageDraw.Draw(rim)
    d.rounded_rectangle((3,3,w-4,h-4),radius=9,outline=(*edge,175),width=1)
    # A restrained reflected highlight along the upper bevel, not a luminous ring.
    d.line((13,3,w-14,3),fill=(*highlight,95),width=1)
    base.alpha_composite(rim)
    return base

def tile(w,h,selected=False,palette=None):
    image=Image.new('RGBA',(w,h),'#100D0A')
    source=muted_smoke(Image.open(SKIN/'prep-item-sword-v2.png'))
    # Keep the original painted proportions instead of stretching the blade.
    factor=min((w-8)/source.width,(h-9)/source.height)
    source=source.resize((round(source.width*factor),round(source.height*factor)),Image.Resampling.LANCZOS)
    texture=Image.open(SKIN/'prep-surface-v2.png').convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
    image.alpha_composite(texture)
    image=material_inlay(image,selected,palette)
    image.alpha_composite(source,((w-source.width)//2,(h-source.height)//2-1))
    border=Image.open(SKIN/'prep-socket-v5.png').convert('RGBA').resize((w,h),Image.Resampling.LANCZOS)
    border=ImageEnhance.Brightness(border).enhance(.68)
    # Keep the original skin alpha and soft contour; its central field is transparent.
    image.alpha_composite(border)
    if selected:
        # Aged green inner bevel is deliberately quieter than the original gold.
        d=ImageDraw.Draw(image)
        edge=(palette or {}).get('rim',(108,139,127))
        d.rounded_rectangle((4,4,w-5,h-5),radius=8,outline=(*edge,205),width=1)
    image.putalpha(round_mask(w,h,0,12))
    return image

originals=[Image.open(path).crop(CROP).convert('RGB') for path in SOURCES]
clean=[clear_annotations(im) for im in originals]
equipment=clean[0].convert('RGBA')

# Common item: revise only the selected tile, quiet worn socket and purple smoke.
chosen=tile(120,134,True)
badge=clean[0].crop((648,339,748,365)).convert('RGBA')
badge=ImageEnhance.Color(badge).enhance(.72)
chosen.alpha_composite(badge,(10,107))
equipment.alpha_composite(chosen,(638,232))
equipment.alpha_composite(tile(91,91,False),(84,487))
region=equipment.crop((1066,65,1545,230))
equipment.paste(muted_smoke(region),(1066,65))
equipment.convert('RGB').save(OUT/'equipment-context-revised.png',optimize=True)

# The list keeps its existing row centres and five visible rows.
skills=clean[1].convert('RGBA')
texture=Image.open(SKIN/'prep-surface-v2.png').convert('RGBA')
erase=texture.resize((584,430),Image.Resampling.LANCZOS)
skills.alpha_composite(erase,(377,99))
normal=Image.open(SKIN/'prep-skill-row-v5.png').convert('RGBA').resize((574,74),Image.Resampling.LANCZOS)
names=['断空斩','破军突袭','铁誓壁垒','旋风斩','破晓裁决']
roles=['单体','群攻','辅助','群攻','终极 · 群攻']
levels=['1级','1级','1级','Lv.10','Lv.11']
for index,(name,role,level) in enumerate(zip(names,roles,levels)):
    row=material_inlay(normal,index==0)
    icon=Image.open(UI/f'combat-relief/rpg-war-{index+1:02d}.png').convert('RGBA')
    inset=round(icon.width*.047)
    icon=icon.crop((inset,inset,icon.width-inset,icon.height-inset)).resize((56,56),Image.Resampling.LANCZOS)
    if index>2:icon=ImageEnhance.Color(icon).enhance(.72)
    row.alpha_composite(icon,(20,9))
    frame=Image.open(SKIN/'rpg-skill-icon-frame-v6.png').convert('RGBA').resize((59,59),Image.Resampling.LANCZOS)
    row.alpha_composite(frame,(18,7))
    d=ImageDraw.Draw(row)
    color='#FFF0C9' if index<3 else '#BBA17A'
    d.text((100,25),name,font=f(31),fill=color,anchor='lm',stroke_width=0)
    role_font=ImageFont.truetype('C:/Windows/Fonts/simsun.ttc',21) if role=='辅助' else f(21)
    d.text((100,57),role,font=role_font,fill='#B4A083',anchor='lm')
    d.text((552,37),level,font=f(25),fill='#D1BE98' if index<3 else '#AD9774',anchor='rm')
    skills.alpha_composite(row,(381,107+84*index))
skills.convert('RGB').save(OUT/'skills-context-revised.png',optimize=True)

# Review is tied to actual screenshots, with equal crop scales in both columns.
board=Image.new('RGB',(1600,1070),'#100D0A')
d=ImageDraw.Draw(board)
d.text((58,32),'选中状态 · 修订',font=f(37),fill='#E5D5B4')
d.text((58,88),'当前画面',font=f(23),fill='#AC9776')
d.text((826,88),'修订方向',font=f(23),fill='#B9C9B9')
d.line((58,127,1542,127),fill='#493622',width=1)
eqbox=(489,218,908,392)
eq_before=originals[0].crop(eqbox).resize((714,297),Image.Resampling.LANCZOS)
eq_after=equipment.crop(eqbox).convert('RGB').resize((714,297),Image.Resampling.LANCZOS)
d.text((58,154),'装备',font=f(24),fill='#C6B28C')
board.paste(eq_before,(58,200));board.paste(eq_after,(826,200))
d.text((58,549),'技能列表',font=f(24),fill='#C6B28C')
d.line((58,595,1542,595),fill='#493622',width=1)
skillbox=(361,96,975,356)
sk_before=originals[1].crop(skillbox).resize((714,302),Image.Resampling.LANCZOS)
sk_after=skills.crop(skillbox).convert('RGB').resize((714,302),Image.Resampling.LANCZOS)
board.paste(sk_before,(58,621));board.paste(sk_after,(826,621))
d.text((58,979),'细铜边与原材质保留；选中只增加青灰内衬和柔和压边。',font=f(22),fill='#B9AA8D')
d.text((1542,1030),'候选设计 · 尚未接入游戏',font=f(18),fill='#9D8C73',anchor='rm')
board.save(OUT/'selection-before-after.png',optimize=True)

combined=Image.new('RGB',(1562,1460),'#100D0A')
combined.paste(equipment.convert('RGB'),(0,0));combined.paste(skills.convert('RGB'),(0,738))
combined.save(OUT/'revised-context-panels.png',optimize=True)

# Record the rejection without promoting either candidate to an accepted skin.
for folder,status in [('equipment-selection-v1','rejected_by_user'),('skill-selection-v1','invalidated_with_rejected_direction')]:
    spec_path=OUT.parent/folder/'design-spec.json'
    spec=json.loads(spec_path.read_text(encoding='utf-8'))
    spec['status']=status
    spec['review']={'date':'2026-11-17','reason':'用户否定象牙白角标方向的审美；派生稿不再作为后续基线。','supersededBy':'source-art/ui/selection-redesign-v2/'}
    spec_path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
review_path=OUT/'review.json'
review=json.loads(review_path.read_text(encoding='utf-8'))
review['status']='candidate_pending_user_review'
review['composition']['status']='visually_reviewed_candidate_pending_user'
review['composition']['files']=['selection-before-after.png','equipment-context-revised.png','skills-context-revised.png']
review['composition']['annotationCleanup']='Pillow/NumPy local neighbor fill removes red markup only.'
review['composition']['font']='Existing bundled rpg-serif-v2.ttf, with original compact list centres and no new runtime rules.'
review['composition']['fontFallback']='The bundled subset lacks 辅; that role label uses the existing Windows SimSun font in this static composition only.'
review_path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'comparison':str(OUT/'selection-before-after.png'),'context':str(OUT/'revised-context-panels.png')},ensure_ascii=False))
