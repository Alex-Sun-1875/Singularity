"""Nearest valid hair color in unused UV space prevents dark mip seams."""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy import ndimage as nd
p=Path(__file__).resolve().parent/'textures/hair-nero-color.png'
a=np.array(Image.open(p).convert('RGBA'));valid=a[:,:,:3].max(2)>30
index=nd.distance_transform_edt(~valid,return_distances=False,return_indices=True)
a[:,:,:3]=a[index[0],index[1],:3];a[:,:,3]=255;Image.fromarray(a).save(p)
print('Extended native bake padding',int((~valid).sum()),flush=True)
