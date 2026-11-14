"""Pack source diffuse + explicit official opacity maps and downsample PBR normals."""
import pathlib,json,hashlib,sys
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parents[2];BASE=ROOT/'assets/resources/environment';CACHE=ROOT/'temp/environment-source'
library=json.loads((BASE/'library.json').read_text());(BASE/'textures').mkdir(exist_ok=True)
for key,mat in library['materials'].items():
 if '--cutouts-only' in sys.argv and not mat.get('opacitySource'):continue
 size=1024 if key.startswith(('tree-','rocks-')) else 512
 for kind in ['color','normal']:
  if '--cutouts-only' in sys.argv and kind!='color':continue
  source=mat.get(kind+'Source')
  if not source:continue
  image=Image.open(CACHE/mat['asset']/source).convert('RGBA' if mat.get('opacitySource') and kind=='color' else 'RGB')
  limit=512 if kind=='normal' else size
  image.thumbnail((limit,limit),Image.Resampling.LANCZOS)
  if kind=='color' and mat.get('opacitySource'):
   alpha=Image.open(CACHE/mat['asset']/mat['opacitySource'])
   # Official PNG opacity maps are unsigned 16-bit data. Pillow's direct L
   # conversion clamps at 255, making dark, transparent RGB padding opaque.
   if alpha.mode in ['I;16','I;16B','I;16L','I']:
    alpha=alpha.convert('F').point(lambda value:value/257+.5).convert('L')
   else:alpha=alpha.convert('L')
   alpha=alpha.resize(image.size,Image.Resampling.LANCZOS);image.putalpha(alpha)
  path=BASE/(mat[kind]+'.png');image.save(path,optimize=True)
 print(key,size,mat.get('cutout'),flush=True)
outputs=[]
for file in sorted(BASE.rglob('*')):
 if file.is_file() and file.suffix in ['.json','.png','.bin'] and file.name!='manifest.json':outputs.append({'path':str(file.relative_to(BASE)).replace('\\','/'),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
manifest={'license':'CC0-1.0','licenseUrl':'https://polyhaven.com/license','sourceManifest':'asset-pipeline/environment/sources.json','textureBudget':'512px props, 1024px tree and rock; albedo alpha explicitly packed from official alpha map','outputs':outputs}
(BASE/'manifest.json').write_text(json.dumps(manifest,indent=2))
