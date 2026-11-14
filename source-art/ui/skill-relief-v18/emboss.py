"""Emboss existing vector masks with Pillow/NumPy; no model inference."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageChops, ImageDraw
import numpy as np
import json, hashlib

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[2]
OUTPUT=PROJECT/'src/cocos/assets/resources/ui/combat-relief'
PALETTES={
 'attack':((235,220,181),(95,72,39)), 'bow':((213,222,175),(72,85,47)),
 'staff':((224,216,192),(94,78,57)), 'dash':((232,220,181),(92,74,42)),
 'skill':((236,209,148),(109,75,31)), 'spell0':((255,191,104),(132,56,20)),
 'spell1':((175,226,246),(34,80,111)), 'checks':((233,218,180),(93,70,39)),
}

def color_layer(size,color,alpha):
 image=Image.new('RGBA',size,(*color,255));image.putalpha(alpha);return image

def offset(mask,x,y):
 result=Image.new('L',mask.size);result.paste(mask,(x,y));return result

def emboss(mask,palette):
 # Successive erosions approximate a bevel height field without extra libraries.
 height=sum(np.asarray(mask.filter(ImageFilter.MinFilter(s)),dtype=np.float32)/255 for s in [1,3,5,7,9,11])/6
 height=np.asarray(Image.fromarray((height*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.55)),dtype=np.float32)/255
 gy,gx=np.gradient(height);norm=np.stack([-gx*6,-gy*6,np.ones_like(height)],axis=-1)
 norm/=np.linalg.norm(norm,axis=-1,keepdims=True)
 light=np.array([-.48,-.61,.63]);light/=np.linalg.norm(light)
 lighting=np.clip(np.sum(norm*light,axis=-1),0,1)
 y,x=np.indices(height.shape);polish=.026*np.sin((x+y*.22)*.31)+.04*(1-y/256)
 amount=np.clip((lighting-.12)/.88+polish,0,1)[...,None]
 high,low=[np.array(c,dtype=np.float32) for c in palette]
 rgb=low+(high-low)*amount
 # A narrow specular ridge and dark lower wall make even small glyphs feel cast.
 specular=np.clip((lighting-.91)/.09,0,1)[...,None]*.48
 rgb=rgb*(1-specular)+np.array([255,246,214])*specular
 top=Image.fromarray(np.dstack([np.clip(rgb,0,255).astype('uint8'),np.asarray(mask)]))
 expanded=mask.filter(ImageFilter.MaxFilter(5))
 result=Image.new('RGBA',mask.size)
 result.alpha_composite(color_layer(mask.size,(0,0,0),offset(expanded,2,6).filter(ImageFilter.GaussianBlur(2))))
 result.alpha_composite(color_layer(mask.size,(47,29,14),offset(expanded,1,4)))
 result.alpha_composite(color_layer(mask.size,(28,22,15),expanded))
 result.alpha_composite(top)
 return result

if __name__ == '__main__':
 records=json.loads((ROOT/'sources.json').read_text(encoding='utf8'))
 for item in records['assets']:
  name=item['id'];mask=Image.open(ROOT/'masks'/f'{name}.png').convert('RGBA').getchannel('A')
  result=emboss(mask,PALETTES[name])
  target=OUTPUT/f'{name}.png';result.save(target,optimize=True)
  item.update(asset=target.relative_to(PROJECT).as_posix(),size=list(result.size),bytes=target.stat().st_size,pngSHA256=hashlib.sha256(target.read_bytes()).hexdigest())

 credits=(ROOT/'../game-icons/CREDITS.txt').read_text(encoding='utf8')+'\nCombat relief adaptations: beveled metal, palette and cast shadow by this project. Original SVG authors and CC-BY-3.0 attribution retained. Lightning silhouette and frame are project-original.\n'
 (OUTPUT/'CREDITS.txt').write_text(credits,encoding='utf8')
 # Actual display-size samples, with one larger detail row for inspecting the bevel.
 frame=Image.open(PROJECT/'src/cocos/assets/resources/ui/quiet-bronze/unified-gold-skill-v18.png').convert('RGBA')
 sheet=Image.new('RGBA',(960,370),(30,27,22,255));draw=ImageDraw.Draw(sheet)
 for i,item in enumerate(records['assets']):
  icon=Image.open(OUTPUT/f"{item['id']}.png").convert('RGBA');cx=60+i*118
  for cy,diameter in [(70,54),(235,132)]:
   sheet.alpha_composite(frame.resize((diameter,diameter),Image.Resampling.LANCZOS),(cx-diameter//2,cy-diameter//2))
   d=round(diameter*.56);sheet.alpha_composite(icon.resize((d,d),Image.Resampling.LANCZOS),(cx-d//2,cy-d//2))
  draw.text((cx-28,108),item['id'],fill=(225,205,162))
 sheet.convert('RGB').save(ROOT/'isolated-preview.jpg',quality=94)
 (ROOT/'provenance.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(f'Exported {len(records["assets"])} beveled combat glyphs and a cast-gold frame.')
