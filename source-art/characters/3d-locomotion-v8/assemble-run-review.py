"""Lay out current 2D frames and native-engine 3D captures without generation."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];OUT=BASE/'runtime'
SOURCE=ROOT/'src/cocos/assets/resources/flat2d/characters/raphael'
m=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'));a=m['actions']['run']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def reference(i):
 f=int(i/30*a['fps'])%a['frames'];image=a['frameImages'][f];idx=a['frameIndices'][f]
 rect=a['frameRectsByImage'][str(Path(image).with_suffix('')).replace('\\','/')][4+idx]
 x,y,w,h=rect;part=Image.open(SOURCE/image).convert('RGBA').crop((x,y,x+w,y+h))
 origin=a['perFrameOrigins']['right'][f];im=Image.new('RGB',(384,480),'#20272a')
 im.paste(part,(round(192-origin[0]),round(434-origin[1])),part)
 return im
frames=[]
for i in range(60):
 im=Image.new('RGB',(1152,520),'#20272a');d=ImageDraw.Draw(im)
 for j,label in enumerate(['现有 2D 完整跑姿','新版 3D · 侧面','新版 3D · 背面']):d.text((j*384+12,10),label,font=font,fill='#e3d6bd')
 im.paste(reference(i),(0,40))
 for col,angle in [(1,90),(2,180)]:im.paste(Image.open(OUT/'after-ground'/f'run-{angle}-{i:03d}.png').convert('RGB'),(col*384,40))
 frames.append(im)
palette=Image.new('RGB',(1152*6,520))
for i in range(6):palette.paste(frames[i*10],(1152*i,0))
palette=palette.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
indexed=[im.quantize(palette=palette,dither=Image.Dither.NONE)for im in frames]
indexed[0].save(OUT/'coordinated-run.gif',save_all=True,append_images=indexed[1:],duration=[30,30,40]*20,loop=0,optimize=True,disposal=1)
frames[5].save(OUT/'coordinated-run.jpg',quality=94)
board=Image.new('RGB',(2560,1040),'#20272a');d=ImageDraw.Draw(board)
for row,(folder,label)in enumerate([(BASE.parent/'3d-locomotion-v7/runtime','上一版'),(OUT,'本版')]):
 for j,f in enumerate([0,.125,.25,.375,.5,.625,.75,.875]):
  d.text((j*320+12,row*520+10),f'{label} / {f:g}',font=font,fill='#e3d6bd')
  board.paste(Image.open(folder/'after'/f'W07-run-{f}-90.png').convert('RGB').resize((320,400) if row else (320,480)),(j*320,row*520+(80 if row else 40)))
board.save(OUT/'full-stride-keyframes.jpg',quality=93)
report={'referenceManifestRevision':m['revision'],'referenceManifestSHA256':hashlib.sha256((SOURCE/'manifest.json').read_bytes()).hexdigest(),'referenceAction':'run / right, all 8 runtime frames','engine':'Actual Cocos native actor, fixed test ground with actor and camera translating at game speed 5.2m/s','durationMilliseconds':2000,'fps':30,'generatedImages':False,'userApproved':False}
(OUT/'coordinated-run-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('COORDINATED_RUN_PREVIEW_READY')
