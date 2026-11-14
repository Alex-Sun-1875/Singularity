"""Arrange real runtime captures at one fixed camera scale and ground anchor."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'runtime-audit.json').read_text())
fontpath=Path('C:/Windows/Fonts/msyh.ttc')
font=ImageFont.truetype(str(fontpath),20) if fontpath.exists() else ImageFont.load_default()
small=ImageFont.truetype(str(fontpath),15) if fontpath.exists() else ImageFont.load_default()
states=[('standing','收剑待机'),('held','持剑待机'),('attack-p0','挥剑准备'),('attack-p3','挥剑收招')]
directions=['right','down','up','left']
board=Image.new('RGB',(1120,1720),'#252a2b');draw=ImageDraw.Draw(board)
for row,d in enumerate(directions):
    for col,(state,title) in enumerate(states):
        record=next(c for c in data['captures'] if c['label']==state and c['direction']==d)
        im=Image.open(HERE/record['name']).convert('RGB')
        ax=record['anchor'][0]-record['clip']['x'];ay=record['anchor'][1]-record['clip']['y']
        # Identical dimensions and pixel density, never fit individual bounds.
        crop=im.crop((round(ax-70),round(ay-175),round(ax+70),round(ay+25)))
        crop=crop.resize((280,400),Image.Resampling.LANCZOS)
        board.paste(crop,(col*280,row*430+25))
        draw.text((col*280+12,row*430+2),title,font=font,fill='#f0dbae')
        draw.text((col*280+12,row*430+402),d,font=small,fill='#f0dbae')
board.save(HERE/'game-four-directions-aligned.jpg',quality=92)
board.crop((0,0,1120,430)).save(HERE/'game-model-alignment.jpg',quality=94)
print('Arranged real runtime captures without per-frame scaling.')
