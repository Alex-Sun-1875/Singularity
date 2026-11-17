"""Recolour existing rolling-fire shapes; deterministic, no model or redesign.

The atlas previews are material swatches, never represented as game footage.
Only this directory and the two named PNG/metas are written.
"""
from pathlib import Path
import hashlib, json, uuid, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RES = ROOT / 'src/cocos/assets/resources/vfx/production'
HERE.mkdir(parents=True, exist_ok=True)
ASSETS = HERE / 'assets'
ASSETS.mkdir(exist_ok=True)
SOURCE = RES / 'fire-pyro-v7.png'
PREVIEW_ONLY = '--preview-only' in sys.argv

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

def sample(a, x, y):
    valid = (x >= 0) & (x <= a.shape[1]-1) & (y >= 0) & (y <= a.shape[0]-1)
    x = np.clip(x, 0, a.shape[1]-1.001)
    y = np.clip(y, 0, a.shape[0]-1.001)
    ix, iy = x.astype(int), y.astype(int)
    tx, ty = (x-ix)[..., None], (y-iy)[..., None]
    p = a[iy, ix]*(1-tx)*(1-ty)+a[iy, ix+1]*tx*(1-ty)+a[iy+1, ix]*(1-tx)*ty+a[iy+1, ix+1]*tx*ty
    return p*valid[..., None]

def rgba(p):
    alpha = p[..., 3:4]
    rgb = p[..., :3]/np.maximum(alpha, 1e-6)
    return Image.fromarray(np.uint8(np.clip(np.concatenate([rgb, alpha], axis=2), 0, 1)*255))

raw = np.asarray(Image.open(SOURCE).convert('RGBA'), dtype=float)/255
source_frames = [raw[i//4*256:(i//4+1)*256, i%4*384:(i%4+1)*384].copy() for i in range(16)]
frames = []
for a in source_frames:
    # Keep the existing curled silhouette and fine colour detail. Remove the
    # opaque dark-red sheets; shift the selected warm filaments into v27's
    # measured orange-gold range, without a grey-white core.
    ratio = a[..., 1]/np.maximum(a[..., 0], .001)
    heat = smooth((ratio-.20)/.60)
    chroma = np.empty_like(a[..., :3])
    chroma[..., 0] = 1
    chroma[..., 1] = .425+.355*np.sqrt(heat)
    chroma[..., 2] = .045+.295*heat**.65
    alpha = np.minimum(.78, a[..., 3]**1.12*(.20+.65*heat**.65)*(.6+.4*a[..., 0]))
    frames.append(np.concatenate([chroma*alpha[..., None], alpha[..., None]], axis=2))

def phase_frame(phase):
    n = 6+5*phase
    i = int(n)
    return frames[i]*(1-(n-i))+frames[min(11, i+1)]*(n-i)

# One coherent blast lifecycle. Fixed registration keeps its foot and centre
# stable through ignition, expansion, collapse and low residual fire.
blast_frames = []
by, bx = np.mgrid[:160, :256]
for p in frames:
    q = sample(p, (bx-127.5)/(2/3)+191.5, (by-150)/.60+242)
    border = smooth(np.minimum.reduce([bx, 255-bx, by, 159-by])/3)
    q *= border[..., None]
    blast_frames.append(rgba(q))

# A horizontally periodic low rolling field. Two very broad existing waves
# overlap in space, with independent smooth lifecycle windows. Each source
# always advances 6->11; a zero-weight wrap restarts it invisibly. Maximum-like
# translucent fusion preserves filament detail instead of piling alpha up.
field_frames = []
fy, fx = np.mgrid[:128, :256]
for index in range(16):
    layers = []
    for layer in range(2):
        phase = (index/16+layer*.5) % 1
        weight = np.sin(np.pi*phase)**2
        wave = phase_frame(phase)
        centre = layer*128+phase*34
        dx = (fx-centre+128) % 256-128
        q = sample(wave, dx/(2/3)+191.5, (fy-120)/.40+242)
        q *= (.24+.76*weight)
        layers.append(q)
    # The endpoint of the quiet phase is already low fire, so suppressing its
    # canopy avoids any visible sudden restart while the other wave carries it.
    # Window the transport contribution fully at wrap, keep a faint low bed.
    for layer in range(2):
        phase = (index/16+layer*.5) % 1
        layers[layer] *= smooth(min(phase, 1-phase)/.14)
    a = np.stack([q[..., 3] for q in layers], axis=0)
    dominant = a.argmax(axis=0)
    maximum = a.max(axis=0)
    out_alpha = np.minimum(.74, maximum+.10*(a.sum(axis=0)-maximum))
    # A soft dominant-layer blend retains the linework without a hard seam.
    weights = np.maximum(a, 1e-7)**5
    denom = weights.sum(axis=0)
    colours = np.stack([q[..., :3]/np.maximum(q[..., 3:4], 1e-6) for q in layers], axis=0)
    colour = (colours*weights[..., None]).sum(axis=0)/denom[..., None]
    out = np.concatenate([colour*out_alpha[..., None], out_alpha[..., None]], axis=2)
    out *= smooth(np.minimum(fy, 127-fy)/3)[..., None]
    # Pixel edges are shared explicitly; neighbouring repeats are continuous.
    edge = (out[:, 0]+out[:, -1])*.5
    out[:, 0] = edge
    out[:, -1] = edge
    field_frames.append(rgba(out))

specs = [('fire-field-roll-v28', field_frames, (256, 128)),
         ('fire-blast-roll-v28', blast_frames, (256, 160))]
outputs = []
for name, seq, cell in specs:
    atlas = Image.new('RGBA', (cell[0]*4, cell[1]*4))
    for i, frame in enumerate(seq):
        atlas.paste(frame, (i%4*cell[0], i//4*cell[1]))
    atlas.save(ASSETS/(name+'.png'), optimize=True)
    if not PREVIEW_ONLY:
        atlas.save(RES/(name+'.png'), optimize=True)
        meta_path = RES/(name+'.png.meta')
        if not meta_path.exists():
            source_meta = (RES/'fire-pyro-v7.png.meta').read_text(encoding='utf8')
            old = json.loads(source_meta)['uuid']
            meta_path.write_text(source_meta.replace(old, str(uuid.uuid4())).replace('fire-pyro-v7', name), encoding='utf8')
    outputs.append(dict(name=name, cell=cell, grid=[4,4], frameCount=16,
        footUV=[.5,.9375], straightAlpha=True, pngBytes=(ASSETS/(name+'.png')).stat().st_size,
        rgbaMemoryBytes=atlas.width*atlas.height*4,
        sha256=hashlib.sha256((ASSETS/(name+'.png')).read_bytes()).hexdigest()))

font = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
small = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
sheet = Image.new('RGB', (1024, 910), '#28312c')
draw = ImageDraw.Draw(sheet)
draw.text((15,12), '沿用原横卷形状，只统一橙金、通透和顺向流动 / 素材合成，非实景', font=font, fill='#eac187')
def composite(frame, gain=1):
    q = np.asarray(frame, dtype=float)/255
    a = q[...,3,None]*gain
    return Image.fromarray(np.uint8(np.clip(q[...,:3]*a*1.10+np.array([40,49,44])/255*(1-a*.90),0,1)*255))
for j, i in enumerate([0, 3, 6, 9]):
    im = field_frames[i]
    bar = Image.new('RGB', (1000,128), '#28312c')
    for repeat in range(4): bar.paste(composite(im), (repeat*256,0))
    sheet.paste(bar, (12,64+j*148))
    draw.text((16,44+j*148), f'连续低矮火面 {i:02} / 横向4次重复检视', font=small, fill='#eac187')
for j, i in enumerate([2, 6, 10, 13]):
    sheet.paste(composite(blast_frames[i]), (j*256,730))
    draw.text((j*256+10,704), f'一体爆燃 / {i:02}', font=small, fill='#eac187')
sheet.save(HERE/'shape-and-colour-preview.jpg', quality=95, subsampling=0)

# Small animated local material previews, including the actual loop boundary.
movie = []
for tick in range(32):
    im = composite(field_frames[tick%16])
    canvas = Image.new('RGB',(768,220),'#28312c')
    canvas.paste(im,(0,72));canvas.paste(im,(256,72));canvas.paste(im,(512,72))
    ImageDraw.Draw(canvas).text((12,10),'连续横卷 / 仅素材循环小样，非游戏实录',font=font,fill='#eac187')
    movie.append(canvas)
movie[0].save(HERE/'field-material-loop.webp', save_all=True, append_images=movie[1:], duration=83, loop=0, quality=90)

record = dict(method='Deterministic Pillow/NumPy recolour and registration of existing authored v7 rolling fire. No generated imagery or local model.',
    userCorrection='Unify orange-gold translucency and forward motion, not identical clumped upright silhouettes.',
    source=str(SOURCE.relative_to(ROOT)), sourceSha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    sourceShape='v7 full fire lifecycle; existing 6..11 rolling waves are spatially repeated for the periodic field; the blast retains authored 0..15 progression.',
    paletteReference='fire-ground-jets-v27.png; measured orange-gold G/R .426.. .761 and B/R .036.. .339, no white or grey core.',
    fieldLoop='16 phases, two broad existing waves each advance 6->11; smooth zero-weight phase resets; no ping-pong. Repeat U within the frame before atlas mapping. Opposite U edge pixels are identical.',
    shaderContract='Straight RGBA; interpolate frames in premultiplied space, then same accepted RGB*1.10 / alpha*.90 source-over as v27.',
    outputs=outputs, productionUpdated=not PREVIEW_ONLY,
    verification='Local texture swatch and loop checked only; native Cocos and user acceptance pending; TapTap/device pending.')
(HERE/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
