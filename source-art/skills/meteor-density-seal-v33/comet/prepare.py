"""Increase the approved comet sheath's optical density without new art.

Only the wrapped head and adjacent flame are changed. All original first-half
tail pixels, frame layout, nose pivot and runtime motion parameters are kept.
"""
from pathlib import Path
import hashlib
import json
import uuid
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PRODUCTION=ROOT/'src/cocos/assets/resources/vfx/production'
SOURCE=PRODUCTION/'fire-meteor-reference-tail-v32.png'
NAME='fire-meteor-reference-tail-v33'
CELL=(512,192)


def smooth(x):
    x=np.clip(x,0,1);return x*x*(3-2*x)


def blur(channel,radius):
    return np.asarray(Image.fromarray(np.uint8(np.clip(channel,0,1)*255)).filter(ImageFilter.GaussianBlur(radius)),dtype=float)/255


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    atlas=Image.open(SOURCE).convert('RGBA');out_atlas=Image.new('RGBA',atlas.size)
    yy,xx=np.mgrid[:CELL[1],:CELL[0]]
    gate=smooth((xx-270)/65)*(1-smooth((xx-494)/12))
    frames=[];old_frames=[];stats=[]
    for frame in range(16):
        box=((frame%4)*512,(frame//4)*192,(frame%4+1)*512,(frame//4+1)*192)
        original=np.asarray(atlas.crop(box),dtype=np.uint8)
        rgba=original.astype(float)/255;rgb=rgba[...,:3];alpha=rgba[...,3]
        # Grey-scale closing joins nearby original hot strands across the
        # exposed core. It keeps graded flame coverage, rather than filling a
        # binary hull into a flat opaque ball. Restrict it to the head gate.
        closed=Image.fromarray(original[...,3]).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.MinFilter(31))
        closed_alpha=np.asarray(closed,dtype=float)/255
        gap=np.maximum(0,closed_alpha-alpha)
        fill_mask=blur(np.clip(gap/np.maximum(1-alpha,.01),0,1),1.6)
        # Nearby original orange-gold strands supply all infill colour. No
        # flat white core, generated fire, extra emitter or opaque ball is used.
        denominator=np.maximum(blur(alpha,8),.005)
        neighbour=np.stack([blur(rgb[...,channel]*alpha,8)/denominator for channel in range(3)],axis=-1)
        neighbour[...,0]=np.maximum(neighbour[...,0],.92)
        neighbour[...,1]=np.clip(neighbour[...,1],.40,.82)
        neighbour[...,2]=np.clip(neighbour[...,2],.045,.32)
        dense=1-np.power(1-alpha,1+1.10*gate)
        fill_alpha=.82*fill_mask*gate*(.94+.06*np.clip(denominator*2,0,1))
        combined=dense+fill_alpha*(1-dense)
        colour=(rgb*dense[...,None]+neighbour*fill_alpha[...,None]*(1-dense[...,None]))/np.maximum(combined[...,None],1e-6)
        result=np.dstack([np.clip(colour,0,1),np.minimum(combined,.96)])
        result=np.uint8(np.rint(np.clip(result,0,1)*255))
        result[gate==0]=original[gate==0]
        assert np.array_equal(result[:,:256],original[:,:256]),'tail centroid pixels changed'
        image=Image.fromarray(result,'RGBA');frames.append(image);old_frames.append(Image.fromarray(original,'RGBA'));out_atlas.paste(image,box[:2])
        core=(xx>=365)&(xx<=480)&(yy>=45)&(yy<=132)
        stats.append({'frame':frame,'joinedHeadGapPixels':int(((gap>.10)&(gate>.5)).sum()),'oldHeadMeanAlpha':float(alpha[core].mean()),'newHeadMeanAlpha':float((result[...,3]/255)[core].mean())})
    output=PRODUCTION/(NAME+'.png');out_atlas.save(output,optimize=True)
    meta=json.loads(SOURCE.with_suffix('.png.meta').read_text(encoding='utf8'))
    identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'singularity:vfx/production/'+NAME+'.png'))
    meta['uuid']=identity;sub=meta['subMetas']['6c48a'];sub['uuid']=identity+'@6c48a';sub['displayName']=NAME;sub['userData']['imageUuidOrDatabaseUri']=identity;meta['userData']['redirect']=identity+'@6c48a'
    output.with_suffix('.png.meta').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    board=Image.new('RGB',(1024,470),'#252d2a');draw=ImageDraw.Draw(board)
    for index,(title,images) in enumerate([('v32 original sheath',old_frames),('v33 denser continuous sheath',frames)]):
        draw.text((index*512+12,12),title,fill='#ecd0a5')
        for row,colour in enumerate(['#252d2a','#514b43']):
            panel=Image.new('RGBA',CELL,colour);panel.alpha_composite(images[3]);board.paste(panel.convert('RGB'),(index*512,40+row*202))
    draw.text((12,448),'Texture comparison only. Tail first-half RGBA, nose pivot, frame count and motion remain unchanged.',fill='#e3c9a4')
    board.save(HERE/'material-comparison.png',optimize=True)
    movie=[]
    for frame in frames:
        panel=Image.new('RGBA',CELL,'#252d2a');panel.alpha_composite(frame);movie.append(panel.convert('RGB'))
    movie[0].save(HERE/'material-loop.webp',save_all=True,append_images=movie[1:],duration=62,loop=0,quality=94)
    provenance={'method':'deterministic optical-density adjustment and grey-scale closing of nearby original hot strands over the core; no generation','source':SOURCE.relative_to(ROOT).as_posix(),'sourceSha256':sha(SOURCE),'originalSourceRecord':'source-art/skills/fire-reference-alignment-v32/meteor-body/provenance.json','output':output.relative_to(ROOT).as_posix(),'sha256':sha(output),'bytes':output.stat().st_size,'cell':CELL,'grid':[4,4],'frames':16,'noseUV':[.9519727106545961,.27757515088207985],'keptRuntime':{'flightVector':[-4.42,-8,3.06],'intrinsicTailAngleCorrectionDegrees':-9.391739408467398,'landingHeight':'.045 above height(target)','contactHoldSeconds':.045,'animation':'same original 16-frame positive transport and native playback clock','drawCalls':'same single comet card; no added shell pass'},'tailPreservation':'left 256 RGBA pixels of every 512px frame are byte-identical; measured tail-centroid angle is unchanged','opticalDensity':{'headExponentMax':2.10,'greyClosingPixels':31,'gapFillWeight':.82,'alphaCap':.96,'externalContour':'bounded original head flame; no radial enlargement or new round silhouette'},'measurements':stats,'review':{'materialSample':'pending visual inspection','nativeCocos':'pending','userArtAcceptance':'pending'}}
    (HERE/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'output':str(output),'sha256':sha(output),'bytes':output.stat().st_size,'frame0':stats[0]},ensure_ascii=False))


if __name__=='__main__':main()
