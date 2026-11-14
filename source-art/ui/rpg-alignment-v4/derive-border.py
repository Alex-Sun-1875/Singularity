"""Keep the approved metal lip; remove interior alpha and old image fragments."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
import json, hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
folder=ROOT/'src/cocos/assets/resources/ui/quiet-bronze'
source=folder/'double-gold-frame-v6.png';output=folder/'double-gold-frame-rpg-v4.png'
im=Image.open(source).convert('RGBA');mask=Image.new('L',im.size,255)
ImageDraw.Draw(mask).rounded_rectangle((14,14,im.width-15,im.height-15),radius=12,fill=0)
im.putalpha(ImageChops.multiply(im.getchannel('A'),mask));im.save(output)
(HERE/'border-provenance.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)).replace('\\','/'),'output':str(output.relative_to(ROOT)).replace('\\','/'),'method':'Pillow alpha-only cleanup; original RGB/metal/corners retained; interior fragments removed. Native clip uses the same 14px inset and 12px inner radius.','newGeneration':False,'sha256':hashlib.sha256(output.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
