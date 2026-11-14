import sys
from PIL import Image
import numpy as np
from scipy import ndimage as nd
p=sys.argv[1];a=np.asarray(Image.open(p).convert('RGBA')).copy();valid=a[:,:,:3].max(2)>30
index=nd.distance_transform_edt(~valid,return_distances=False,return_indices=True);a[:,:,:3]=a[index[0],index[1],:3];Image.fromarray(a).save(p)
