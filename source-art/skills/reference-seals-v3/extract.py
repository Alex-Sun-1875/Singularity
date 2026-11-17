"""Extract the user's actual reference linework and remove its presentation perspective."""
from pathlib import Path
import json
import hashlib
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'reference.png'
SIZE = 1024
EXTENT = 460
FAMILIES = {
    'WAR': {'name':'战士 · 银金刃阵', 'box':(36,176,705,514), 'cardinals':[(373,188),(686,309),(374,496),(56,309)], 'base':(240,200,139), 'hot':(255,236,188)},
    'BOW': {'name':'弓系 · 青绿风阵', 'box':(745,176,1410,514), 'cardinals':[(1081,189),(1394,308),(1081,493),(763,309)], 'base':(107,218,171), 'hot':(183,251,218)},
    'FIR': {'name':'火系 · 橙红陨星阵', 'box':(36,596,705,943), 'cardinals':[(374,610),(685,729),(375,929),(56,730)], 'base':(255,128,43), 'hot':(255,207,123)},
    'THU': {'name':'雷系 · 蓝紫雷纹阵', 'box':(745,596,1410,943), 'cardinals':[(1083,612),(1390,729),(1083,930),(763,730)], 'base':(139,151,255), 'hot':(210,212,255)},
}


def mapping(src, dst):
    rows, values = [], []
    for (x,y),(u,v) in zip(dst,src):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        values.extend([u,v])
    return np.linalg.solve(np.asarray(rows),np.asarray(values))


def extract():
    image = Image.open(SOURCE).convert('RGB')
    full = np.asarray(image,dtype=np.float32)
    for key,style in FAMILIES.items():
        x0,y0,x1,y1 = style['box']
        crop = image.crop(style['box'])
        rgb = full[y0:y1,x0:x1]
        r,g,b = rgb.transpose(2,0,1)
        if key=='WAR':
            score = np.minimum(g-79, (r+g)*.5-95)
            scale = 118
        elif key=='BOW':
            score = g-(r+b)*.5-15
            scale = 57
        elif key=='FIR':
            score = np.minimum(r-115,g-69)
            scale = 117
        else:
            score = b-(r+g)*.5-17
            scale = 65
        alpha = np.clip((score-3)/scale,0,1)**.78
        brightness = np.clip((rgb.max(axis=2)-150)/100,0,1)
        base,hot = np.asarray(style['base']),np.asarray(style['hot'])
        colour = base[None,None,:]*(1-brightness[:,:,None])+hot[None,None,:]*brightness[:,:,None]
        rgba = np.dstack((colour,alpha*255)).astype(np.uint8)
        cropped = Image.fromarray(rgba)
        cropped.save(HERE/'assets'/f'{key}-plane.png')
        src = [(x-x0,y-y0) for x,y in style['cardinals']]
        dest = [(512,512-EXTENT),(512+EXTENT,512),(512,512+EXTENT),(512-EXTENT,512)]
        transform = mapping(src,dest)
        texture = cropped.transform((SIZE,SIZE),Image.Transform.PERSPECTIVE,transform,Image.Resampling.BICUBIC)
        yy,xx=np.indices((SIZE,SIZE))
        radial=np.sqrt((xx-512)**2+(yy-512)**2)/EXTENT
        perimeter=np.clip((1.065-radial)/.025,0,1)
        texture.putalpha(Image.fromarray(np.uint8(np.asarray(texture.getchannel('A'),dtype=np.float32)*perimeter)))
        # Warp straight RGBA in premultiplied space through Pillow, preserving fine points.
        texture.save(HERE/'assets'/f'{key}.png')
        glow = texture.filter(ImageFilter.GaussianBlur(4.2))
        glow.save(HERE/'assets'/f'{key}-glow.png')
        crop.save(HERE/'assets'/f'{key}-source.png')
        ground = np.asarray(crop,dtype=np.float32).copy()
        unknown = np.asarray(Image.fromarray((alpha>.025).astype(np.uint8)*255).filter(ImageFilter.MaxFilter(5)))>0
        known = ~unknown
        for _ in range(24):
            total = np.zeros_like(ground)
            count = np.zeros_like(alpha)
            for dy,dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                shifted = np.roll(known,(dy,dx),(0,1))
                total += np.roll(ground,(dy,dx),(0,1))*shifted[:,:,None]
                count += shifted
            fill = ~known & (count>0)
            ground[fill] = total[fill]/count[fill,None]
            known[fill] = True
            if known.all():break
        Image.fromarray(np.clip(ground,0,255).astype(np.uint8)).save(HERE/'assets'/f'{key}-ground.png')
    data = {'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'method':'Class-channel extraction, inverse perspective and alpha separation. Original drawing retained.',
            'reference':'../four-class-vfx-redesign-v1/02-first-style-class-colors-v5.png',
            'families':FAMILIES, 'textureSize':SIZE, 'circleUVRadius':EXTENT/SIZE,
            'acceptance':'Pending user review', 'productIntegration':False}
    (HERE/'extraction.json').write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')


def check():
    sheet = Image.new('RGB',(1280,760),'#211d19')
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
    for k,(key,style) in enumerate(FAMILIES.items()):
        x = (k%2)*640
        y = (k//2)*380
        d.text((x+16,y+8),style['name'],font=font,fill=style['hot'])
        original = Image.open(HERE/'assets'/f'{key}-source.png')
        original.thumbnail((600,160))
        sheet.paste(original,(x+20,y+38))
        tex = Image.open(HERE/'assets'/f'{key}.png').resize((270,270),Image.Resampling.LANCZOS)
        sheet.paste(tex,(x+180,y+110),tex)
    sheet.save(HERE/'media/extraction-check.jpg',quality=94)


if __name__=='__main__':
    extract()
    check()
