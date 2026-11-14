"""Deterministic raster typography, sizing and upload exports; no model inference."""
from pathlib import Path
import hashlib
import json
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'src/cocos/release/branding/taptap-v1'
FONT = Path('C:/Windows/Fonts/NotoSerifSC-VF.ttf')
OUT.mkdir(parents=True, exist_ok=True)


def font(size, weight):
    value = ImageFont.truetype(str(FONT), size)
    value.set_variation_by_axes([weight])
    return value


def text_mask(text, size, weight, tracking):
    face = font(size, weight)
    mask = Image.new('L', (int(sum(face.getlength(c) for c in text) + tracking * (len(text)-1) + 32), size*2))
    draw = ImageDraw.Draw(mask)
    x = 16
    for c in text:
        draw.text((x, size*1.3), c, font=face, fill=255, anchor='ls')
        x += face.getlength(c)+tracking
    return mask.crop(mask.getbbox())


def metal(mask):
    w, h = mask.size
    # Fixed seed and a short warm-metal ramp keep typography reproducible.
    stops = [(0, (255, 241, 194)), (.28, (244, 215, 152)), (.49, (170, 121, 57)),
             (.54, (246, 220, 163)), (1, (179, 129, 64))]
    layer = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(layer)
    for y in range(h):
        t = y/max(1,h-1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                q = (t-a)/(b-a)
                draw.line((0,y,w,y), fill=tuple(round(ca[k]+q*(cb[k]-ca[k])) for k in range(3)))
                break
    grain = Image.frombytes('L', (w,h), random.Random(20261110).randbytes(w*h)).point(lambda x: int(230+x/10))
    layer = ImageChops.multiply(layer, Image.merge('RGB', (grain,grain,grain))).convert('RGBA')
    layer.putalpha(mask)
    return layer


def logo():
    main = text_mask('剑与火', 264, 900, 18)
    sub = text_mask('破晓之战', 82, 650, 24)
    w = main.width+58
    h = main.height+sub.height+130
    output = Image.new('RGBA', (w,h))
    for mask, x, y in [(main,29,16), (sub,(w-sub.width)//2,main.height+66)]:
        shadow = Image.new('RGBA', (mask.width+40,mask.height+40))
        shadow.paste((10,15,17,220),(20,20),mask)
        output.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(5)),(x-20,y-13))
        rim = Image.new('RGBA',mask.size,(47,30,15,255));rim.putalpha(mask.filter(ImageFilter.MaxFilter(3)))
        output.alpha_composite(rim,(x,y+2));output.alpha_composite(metal(mask),(x,y))
        highlight = ImageChops.subtract(mask, ImageChops.offset(mask,0,2))
        edge = Image.new('RGBA',mask.size,(255,244,209,255));edge.putalpha(highlight.point(lambda a: int(a*.65)))
        output.alpha_composite(edge,(x,y))
    # Quiet dividers carry no additional words or promotional claims.
    draw=ImageDraw.Draw(output)
    cy=main.height+66+sub.height//2
    left=(w-sub.width)//2
    draw.line((30,cy,left-28,cy),fill=(193,148,77,210),width=2)
    draw.line((w-left+28,cy,w-30,cy),fill=(193,148,77,210),width=2)
    return output


def place_logo(background, title, width, xy):
    layer=title.resize((width,round(title.height*width/title.width)),Image.Resampling.LANCZOS)
    background=background.convert('RGBA');background.alpha_composite(layer,xy)
    return background.convert('RGB')


icon=Image.open(HERE/'icon-generated.png').convert('RGB')
cover=Image.open(HERE/'cover-generated.png').convert('RGB')
title=logo();title.save(HERE/'title-logo.png',optimize=True)
for size in [1024,512,192,32]:
    icon.resize((size,size),Image.Resampling.LANCZOS).save(OUT/f'icon-{size}.png',optimize=True)
icon.resize((256,256),Image.Resampling.LANCZOS).save(OUT/'favicon.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

wide=ImageOps.fit(cover,(1920,1080),Image.Resampling.LANCZOS)
wide=place_logo(wide,title,830,(118,352))
wide.save(HERE/'cover-landscape-master.png',optimize=True)
wide.save(OUT/'cover-landscape-1920x1080.jpg',quality=95,subsampling=0,optimize=True)

# A separate composition keeps the entire sword visible; it is not a stretched horizontal cover.
square=ImageOps.fit(cover,(1440,1440),Image.Resampling.LANCZOS,centering=(.99,.5))
square=place_logo(square,title,720,(64,1060))
square.save(HERE/'cover-square-master.png',optimize=True)
square.save(OUT/'cover-square-1440x1440.jpg',quality=95,subsampling=0,optimize=True)

files=[]
for path in sorted(OUT.iterdir()):
    if path.suffix not in ('.png','.jpg','.ico'):
        continue
    im=Image.open(path)
    assert im.mode in ('RGB','RGBA')
    if path.suffix=='.jpg':
        assert path.stat().st_size<2000000
    files.append({'file':path.relative_to(ROOT).as_posix(),'width':im.width,'height':im.height,
                  'mode':im.mode,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest={'createdOn':'2026-11-10','title':'剑与火：破晓之战','artVersion':'taptap-v1',
          'generation':'built-in cloud OpenAI image_gen','composition':'local Pillow deterministic type/layout/resize',
          'generationStatus':'succeeded','visualReviewStatus':'pending final export inspection','userApproved':False,
          'font':{'name':'Noto Serif SC','weightMain':900,'weightSubtitle':650,'source':str(FONT),
                  'sha256':hashlib.sha256(FONT.read_bytes()).hexdigest(),'license':'SIL OFL 1.1',
                  'licenseUrl':'https://github.com/notofonts/noto-cjk/blob/main/Serif/LICENSE','fontRedistributed':False},
          'sources':{'icon':'source-art/branding/taptap-v1/icon-generated.png','cover':'source-art/branding/taptap-v1/cover-generated.png','prompts':'source-art/branding/taptap-v1/prompts.json'},
          'notGameplayScreenshots':True,'uploadedToTapTap':False,'files':files}
(HERE/'manifest.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(files,ensure_ascii=False,indent=2))

# Small visual check: store covers plus icon at actual small display sizes.
sheet=Image.new('RGB',(1280,960),(19,29,31))
sheet.paste(wide.resize((1280,720),Image.Resampling.LANCZOS),(0,0))
for x,size in [(40,192),(270,128),(450,64),(550,48),(630,32)]:
    sheet.paste(icon.resize((size,size),Image.Resampling.LANCZOS),(x,740))
sheet.save(HERE/'preview.jpg',quality=93)
