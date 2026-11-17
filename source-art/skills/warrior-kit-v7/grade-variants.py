from pathlib import Path
import sys,json
from PIL import Image
BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(BASE))
from grade import grade,STOPS
PALETTES={
 'A':{'name':'银白钢刃','detail':'银灰刀面 / 深灰蓝暗边','colours':[(9,15,26),(34,45,58),(113,123,134),(177,190,202),(231,241,247),(255,255,255)],'edge':(4,14,32),'halo':(148,171,191)},
 'B':{'name':'赤金钢刃','detail':'赤金主刃 / 暗红刀背','colours':[(27,7,12),(72,13,24),(148,31,43),(226,74,52),(255,187,104),(255,243,212)],'edge':(48,6,14),'halo':(205,66,42)},
 'C':{'name':'暖金钢刃','detail':'金色刀面 / 深棕暗边','colours':[(25,17,12),(60,38,19),(114,78,31),(192,145,67),(248,224,160),(255,253,230)],'edge':(35,20,8),'halo':(185,139,61)},
 'D':{'name':'银紫钢刃','detail':'银紫主刃 / 深紫暗边','colours':[(18,10,38),(38,22,76),(87,54,136),(155,104,216),(222,192,252),(253,244,255)],'edge':(20,8,43),'halo':(133,91,202)},
}
for key,palette in PALETTES.items():
 target=BASE/'variants'/key;target.mkdir(parents=True,exist_ok=True)
 for name,grid in [('blade',(4,3)),('guard',(2,2))]:
  im=Image.open(BASE/(name+'-warm.png')).convert('RGBA');cols,rows=grid
  out=Image.new('RGBA',(cols*512,rows*512))
  for row in range(rows):
   for col in range(cols):
    tile=im.crop((round(im.width*col/cols),round(im.height*row/rows),round(im.width*(col+1)/cols),round(im.height*(row+1)/rows))).resize((512,512),Image.Resampling.LANCZOS)
    out.paste(grade(tile,palette['colours'],palette['edge'],palette['halo']),(col*512,row*512))
  out.save(target/(name+'.png'))
(BASE/'palette-candidates.json').write_text(json.dumps({'status':'Four candidates requested after cyan treatment was rejected','stops':STOPS,'palettes':PALETTES},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Four blade and guard palette pairs generated')
