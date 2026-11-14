"""Crop the offline source render to the requested side-view leg pose."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;OUT=BASE/'preview';ROOT=BASE.parents[2]
flat=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael';m=json.loads((flat/'manifest.json').read_text(encoding='utf-8'));a=m['actions']['run']
f=3;file=a['frameImages'][f];key=str(Path(file).with_suffix('')).replace('\\','/');x,y,w,h=a['frameRectsByImage'][key][12+a['frameIndices'][f]]
part=Image.open(flat/file).convert('RGBA').crop((x,y,x+w,y+h));origin=a['perFrameOrigins']['left'][f]
reference=Image.new('RGB',(320,480),'#20272a');reference.paste(part,(round(160-origin[0]),round(434-origin[1])),part)
reference=reference.crop((0,220,320,455)).resize((384,282)).convert('L').convert('RGB')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18);frames=[]
for i in range(20):
 im=Image.new('RGB',(1152,340),'#20272a');d=ImageDraw.Draw(im)
 for j,label in enumerate(['2D侧面姿态参考','调整前 · 3D源动作','调整后 · 3D源动作']):d.text((j*384+14,10),label,font=font,fill='#e3d6bd')
 im.paste(reference,(0,48))
 for j,label in [(1,'before'),(2,'after')]:
  crop=Image.open(OUT/f'{label}-side-{i:02d}.png').convert('L').convert('RGB').crop((0,195,384,480));im.paste(crop,(j*384,48))
 frames.append(im)
palette=Image.new('RGB',(1152*4,340))
for j,i in enumerate([0,5,10,15]):palette.paste(frames[i],(j*1152,0))
palette=palette.quantize(colors=128,method=Image.Quantize.MEDIANCUT)
indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE)for f in frames]
durations=[20 if i in [2,5,8,11,14,17,19]else 30 for i in range(20)]
indexed[0].save(OUT/'side-leg-angle.gif',save_all=True,append_images=indexed[1:],duration=durations,loop=0,disposal=1,optimize=True)
frames[7].save(OUT/'side-leg-angle.jpg',quality=94)
board=Image.new('RGB',(1152,680),'#20272a');board.paste(frames[7],(0,0));board.paste(frames[15],(0,340));board.save(OUT/'side-leg-keyposes.jpg',quality=94)
record=json.loads((OUT/'render-source.json').read_text());record.update(referenceAction='Current 2D run / left / frame3',referenceManifestRevision=m['revision'],gifDurationMilliseconds=sum(durations),view='side',scope='Leg geometry/pose only. Grayscale offline Blender source-action render, not a Cocos gameplay screenshot.',userApproved=False)
(OUT/'preview-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('SIDE_POSE_PREVIEW_READY',sum(durations))
