from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
BASE=Path(__file__).resolve().parent;OUT=BASE/'runtime'
ref=BASE.parent/'2d-concepts/locomotion-repair-v3/shared-body-run.jpg';im=Image.open(ref).convert('RGB');w,h=im.size;cw=w/8;ch=h/4
rect=(round(cw*3),round(ch+25),round(cw*4),round(ch*2));cell=im.crop(rect).resize((278,418))
board=Image.new('RGB',(960,520),'#20272a');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
for x,label in [(0,'2D 跑姿参考'),(320,'上一版 3D'),(640,'本版 3D')]:d.text((x+12,10),label,font=font,fill='#e3d6bd')
board.paste(cell,(21,52));board.paste(Image.open(BASE.parent/'3d-locomotion-v6/runtime/after/W07-run-0.75-90.png'),(320,40));board.paste(Image.open(OUT/'after/W07-run-0.75-90.png'),(640,40));board.save(OUT/'reference-pose-review.jpg',quality=94)
(OUT/'reference-pose-review.sources.json').write_text(json.dumps({'reference':str(ref),'referenceSha256':hashlib.sha256(ref.read_bytes()).hexdigest(),'referenceCrop':rect,'referenceResize':[278,418],'actual3DView':'W07-run-0.75-90.png','actual3DSize':[320,480],'purpose':'Side-view pose comparison, not a body-scale calibration or new generated image'},indent=2)+'\n',encoding='utf-8')
print('REFERENCE_POSE_REVIEW_SAVED')
