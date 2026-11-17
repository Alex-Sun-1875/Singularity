"""Rectify the generated silver flow into the existing crescent's UV coordinates."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageFilter
BASE=Path(__file__).resolve().parent
source=Image.open(BASE/'texture-original.png').convert('RGBA')
alpha=source.getchannel('A');assert alpha.getextrema()[0]==0 and alpha.getextrema()[1]>220,'Expected real generated transparency'
box=alpha.point(lambda x:255 if x>12 else 0).getbbox();assert box
crop=source.crop(box);rgba=np.asarray(crop).astype(float)
luma=rgba[:,:,:3]@np.array([.2126,.7152,.0722]);weight=luma*(rgba[:,:,3]/255)**1.5
blur=np.asarray(Image.fromarray(np.uint8(np.clip(weight,0,255))).filter(ImageFilter.GaussianBlur(4)))
height,width=rgba.shape[:2]
def smooth_path(values,sigma=22):
 radius=round(sigma*3);axis=np.arange(-radius,radius+1);kernel=np.exp(-axis*axis/(2*sigma*sigma));kernel/=kernel.sum()
 return np.convolve(np.pad(values,(radius,radius),mode='edge'),kernel,mode='valid')
peaks=smooth_path(np.argmax(blur,axis=0).astype(float))
tops=[];bottoms=[]
for sx in range(width):
 ys=np.flatnonzero(rgba[:,sx,3]>12);tops.append(float(ys[0]) if len(ys) else 0);bottoms.append(float(ys[-1]) if len(ys) else height-1)
tops=smooth_path(np.asarray(tops));bottoms=smooth_path(np.asarray(bottoms))
out=np.zeros((512,1024,4),dtype=np.uint8)
for x in range(1024):
 sx=min(width-1,max(0,round((.06+.80*x/1023)*(width-1))))
 ys=np.flatnonzero(rgba[:,sx,3]>12)
 if not len(ys):continue
 peak=float(peaks[sx]);top=max(float(tops[sx]),peak-(bottoms[sx]-tops[sx])*.075);bottom=float(bottoms[sx])
 at=np.linspace(top,bottom,512);lo=np.floor(at).astype(int);hi=np.minimum(lo+1,height-1);mix=(at-lo)[:,None]
 sample=rgba[lo,sx]*(1-mix)+rgba[hi,sx]*mix
 grey=np.clip(sample[:,:3]@np.array([.2126,.7152,.0722])*1.035,0,255)
 out[:,x,:3]=np.round(grey[:,None]).astype(np.uint8)
 out[:,x,3]=np.round((sample[:,3]/255)**.8*255).astype(np.uint8)
Image.fromarray(out).save(BASE/'blade.png')
data={'generator':'Built-in cloud OpenAI image_gen','generationPrompt':'texture-prompt.txt','original':'texture-original.png','originalSize':source.size,'originalAlphaRange':alpha.getextrema(),
 'originalSha256':hashlib.sha256((BASE/'texture-original.png').read_bytes()).hexdigest(),
 'processing':'Deterministic column-wise UV rectification using a Gaussian-smoothed bright-strand path and bounds to avoid column discontinuities; neutral greyscale mapping, alpha exponent 0.8 with zero preserved; no background replacement or new generated pixels.',
 'crop':box,'output':'blade.png','outputSize':[1024,512],'outputSha256':hashlib.sha256((BASE/'blade.png').read_bytes()).hexdigest(),
 'generationStatus':'Generated and saved','artAcceptance':'Pending user review','productionIntegration':False}
(BASE/'texture-processing.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'originalSize':source.size,'outputSize':[1024,512],'alphaRange':alpha.getextrema()}))
