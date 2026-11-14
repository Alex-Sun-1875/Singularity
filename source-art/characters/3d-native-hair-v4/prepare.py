from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];BASE.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/T_Hair_1_BaseColor.png'
rgb=np.asarray(Image.open(SOURCE).convert('RGB'),dtype=float);lum=rgb@np.array([.2126,.7152,.0722]);silver=((lum[:,:,None]-np.median(lum))*1.25+np.array([171,179,187])).clip(0,255).astype('uint8')
Image.fromarray(silver).save(BASE/'native-silver-source.png')
ref=Image.open(ROOT/'source-art/characters/2d-concepts/identity-reference-v1/head-identity-master.png').convert('RGB')
# Only the two relevant hairstyles, without sending the full character sheet.
ref=ref.crop((30,0,1230,450));ref.thumbnail((900,360));ref.save(BASE/'hair-2d-reference.jpg',quality=94)
print('Prepared original native silver map and limited 2D hair reference')
