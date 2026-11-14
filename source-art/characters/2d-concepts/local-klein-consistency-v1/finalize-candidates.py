"""Constrain generated trials with the original pixels and approved palette."""
from pathlib import Path
import json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
SRGB, LAB = ImageCms.createProfile("sRGB"), ImageCms.createProfile("LAB")
TO_LAB = ImageCms.buildTransformFromOpenProfiles(SRGB, LAB, "RGB", "LAB")
TO_RGB = ImageCms.buildTransformFromOpenProfiles(LAB, SRGB, "LAB", "RGB")


def lab(image):
    values=np.asarray(ImageCms.applyTransform(image.convert("RGB"), TO_LAB)).astype(np.float32)
    # Pillow's NumPy LAB interface exposes signed a/b bytes, unlike getpixel().
    values[:,:,1:]=np.where(values[:,:,1:]>=128,values[:,:,1:]-256,values[:,:,1:])
    return values


def rgb(array):
    values=array.copy()
    values[:,:,0]=np.clip(values[:,:,0],0,255)
    values[:,:,1:]=np.mod(np.clip(values[:,:,1:],-128,127),256)
    return ImageCms.applyTransform(Image.fromarray(values.astype("uint8"), "LAB"), TO_RGB)


def palette_masks(image, region):
    a=np.asarray(image).astype(float); h=np.asarray(image.convert("HSV")).astype(float)
    rows=np.indices(a.shape[:2])[0]
    wine=(((h[:,:,0]<12)|(h[:,:,0]>238))&(h[:,:,1]>48)&(h[:,:,1]<205)&(h[:,:,2]<215)&(a[:,:,0]>a[:,:,2]+6))
    sleeve=(h[:,:,1]<55)&(h[:,:,2]<185)&(rows<390)&(~wine)
    return [(wine & region), (sleeve & region)]


def palette_lock(base, generated, reference, region):
    source_lab, model_lab, ref_lab = lab(base),lab(generated),lab(reference)
    ref_region=np.zeros((768,512),bool);ref_region[200:405]=True
    source_masks=palette_masks(base,region)
    model_masks=palette_masks(generated,region)
    reference_masks=palette_masks(reference,ref_region)
    result=base.copy(); details=[]
    for label,sm,mm,rm in zip(["wine-burgundy","dark-sleeves"],source_masks,model_masks,reference_masks):
        if min(sm.sum(),mm.sum(),rm.sum())<25: continue
        source_median=np.median(source_lab[sm],axis=0)
        model_median=np.median(model_lab[mm],axis=0)
        target_median=np.median(ref_lab[rm],axis=0)
        # Keep the model-proposed colour within the approved standing palette.
        selected=np.clip(model_median,target_median-2,target_median+2)
        delta=selected-source_median
        candidate=rgb(source_lab+delta)
        mask=Image.fromarray((sm*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.8))
        result=Image.composite(candidate,result,mask)
        details.append({"region":label,"source_median_Lab8":source_median.tolist(),"model_median_Lab8":model_median.tolist(),"standing_median_Lab8":target_median.tolist(),"selected_median_Lab8":selected.tolist(),"method":"Model palette projected into standing-reference tolerance, applied to original material detail"})
    return result,details


reports=[]
for case in CASES:
    name=case['name'];folder=Path(case['directory']);out=ROOT/'results'/name
    before=Image.open(folder/'before.png').convert('RGB')
    guide=Image.open(folder/'guide.png').convert('RGB')
    raw=Image.open(out/'raw-model.png').convert('RGB')
    mask=Image.open(folder/'composite-mask.png').convert('L')
    if name=='sword-back':
        oldmask=Image.new('L',before.size,0);ImageDraw.Draw(oldmask).line([(283,192),(200,373)],fill=255,width=5)
        newmask=Image.new('L',before.size,0);ImageDraw.Draw(newmask).line([(283,192),(166.8,445.4)],fill=255,width=13)
        old_samples=(np.asarray(oldmask)>128)&(np.indices((768,512))[0]>220)
        new_samples=(np.asarray(newmask)>128)&(np.indices((768,512))[0]>220)
        delta=np.median(lab(before)[old_samples],axis=0)-np.median(lab(raw)[new_samples],axis=0)
        corrected=rgb(lab(raw)+delta)
        newmask=newmask.filter(ImageFilter.GaussianBlur(.7))
        guard=np.array(newmask);guard[:210]=0;newmask=Image.fromarray(guard)
        final=Image.composite(corrected,guide,newmask)
        # Preserve original grip, pommel, upper mount and all head pixels exactly.
        final.paste(before.crop((0,0,512,210)),(0,0))
        details={'shaft_palette_delta_Lab8':delta.tolist(),'shaft_max_composite_width_px':13,'guide_scabbard_factor':1.4}
    else:
        if name=='clothing-side':
            base=before.copy();region=np.asarray(mask)>100
        else:
            base=guide.copy()
            # Model leg detail may change; original arm silhouettes and shoes remain fixed.
            protect=Image.new('L',before.size,0);d=ImageDraw.Draw(protect)
            if name=='run-front':
                d.polygon([(0,195),(229,195),(237,330),(209,364),(0,364)],fill=255)
                d.polygon([(309,195),(512,195),(512,443),(322,443),(310,387)],fill=255)
            else:
                d.polygon([(0,195),(217,195),(214,448),(0,448)],fill=255)
                d.polygon([(302,195),(512,195),(512,385),(321,385),(301,300)],fill=255)
            d.rectangle((0,650,511,767),fill=255)
            base=Image.composite(before,base,protect)
            legmask=np.array(mask);legmask[:380]=0;legmask[650:]=0
            legmask[np.asarray(protect)>0]=0
            legmask=Image.fromarray(legmask).filter(ImageFilter.GaussianBlur(2))
            base=Image.composite(raw,base,legmask)
            base=Image.composite(before,base,protect)
            region=np.asarray(Image.open(folder/'noise-mask.png'))>100
            rows=np.indices((768,512))[0];region &= (rows>=210)&(rows<420)
        ref=Image.open(folder/'reference.png').convert('RGB')
        final,details=palette_lock(base,raw,ref,region)
        final.paste(before.crop((0,0,512,200)),(0,0))
        if name.startswith('run-'):
            final.paste(before.crop((0,650,512,768)),(0,650))
    final.save(out/'constrained-candidate.png')
    assert np.array_equal(np.asarray(final)[:190],np.asarray(before)[:190])
    if name.startswith('run-'):
        assert np.array_equal(np.asarray(final)[650:],np.asarray(before)[650:])
    reports.append({'case':name,'output':str(out/'constrained-candidate.png'),'head_face_original_pixels_preserved_above_y190':True,'contact_boot_pixels_preserved_from_y650':name.startswith('run-'),'model_output':str(out/'raw-model.png'),'local_constraints':details,'status':'representative-frame prototype, not installed'})
(ROOT/'constraints-report.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')

board=Image.new('RGB',(1056,840),(245,245,245));draw=ImageDraw.Draw(board)
try:font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
except OSError:font=ImageFont.load_default()
labels=['背剑加长约30%','衣色向站姿统一','正面跑长腿比例','背面跑长腿比例']
for i,(case,label) in enumerate(zip(CASES,labels)):
    x=32+i*256;p=Path(case['directory'])
    draw.text((x+8,5),label,font=font,fill=(25,25,25))
    board.paste(Image.open(p/'before.png').resize((240,360),Image.Resampling.LANCZOS),(x+8,40))
    board.paste(Image.open(ROOT/'results'/case['name']/'constrained-candidate.png').resize((240,360),Image.Resampling.LANCZOS),(x+8,455))
draw.text((4,200),'原\n图',font=font,fill=(55,55,55));draw.text((4,580),'小\n样',font=font,fill=(55,55,55))
board.save(ROOT/'comparison-constrained.jpg',quality=90,optimize=True)
print(json.dumps(reports,indent=2))
