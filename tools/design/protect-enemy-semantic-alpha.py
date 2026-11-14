"""Use U1-3 cloud background semantics, preserving original actor RGBA pixels."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'source-art/encounters/cloud-world-v2/actor-production-v1/U1-3'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source=FOLDER/'sheet-v1.png';matte_path=FOLDER/'background-removed-v2.png';original=np.asarray(Image.open(source).convert('RGBA'));h,w=original.shape[:2]
    matte_image=Image.open(matte_path).convert('RGBA');matte_size=matte_image.size
    if matte_size!=(w,h):matte_image=matte_image.resize((w,h),Image.Resampling.LANCZOS)
    matte=np.asarray(matte_image)[:,:,3];solid=original[:,:,3]>=128;other=matte>=128
    best=(-1,0,0)
    for dy in range(-4,5):
        for dx in range(-4,5):
            ty=slice(max(0,dy),min(h,h+dy));tx=slice(max(0,dx),min(w,w+dx));sy=slice(max(0,-dy),min(h,h-dy));sx=slice(max(0,-dx),min(w,w-dx));a=solid[ty,tx];b=other[sy,sx];score=np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))
            if score>best[0]:best=(float(score),dx,dy)
    score,dx,dy=best;aligned=ndimage.shift(matte,[dy,dx],order=0,mode='constant',cval=0)
    protected=ndimage.binary_dilation(solid,structure=np.ones((3,3)),iterations=3)
    remove=(aligned<=3)&~protected&(original[:,:,3]>0);result=original.copy();result[remove,3]=0
    assert np.array_equal(result[protected],original[protected])and np.array_equal(result[~remove],original[~remove])
    assert np.array_equal(result[:,:,:3],original[:,:,:3])
    output=FOLDER/'sheet-v3-protected-alpha.png';Image.fromarray(result).save(output)
    removed=FOLDER/'alpha-removed-mask.png';protected_path=FOLDER/'alpha-protected-mask.png';Image.fromarray(np.uint8(remove)*255).save(removed);Image.fromarray(np.uint8(protected)*255).save(protected_path)
    report=dict(status='semantic-background-alpha-derived-original-body-protected',authority='Root U1-3 alpha output alignment and body-protected derivative authorization',sourceSha256=sha(source),cloudMatteSha256=sha(matte_path),outputSha256=sha(output),sourceFilesUnchanged=True,cloudMatteOriginalSize=list(matte_size),uniformMatteSize=[w,h],wholeSheetIntegerTranslation=[dx,dy],solidSilhouetteIoU=score,cloudMatteBackgroundAlphaMax=3,rawProtectedSolidAlpha=128,rawProtectedDilationPixels=3,protectedRgbaByteExact=True,allRetainedOriginalRgbaByteExact=True,allOriginalRgbByteExact=True,removedPixels=int(remove.sum()),removedAlphaAbove3Pixels=int(np.count_nonzero(remove&(original[:,:,3]>3))),removedMaxOriginalAlpha=int(original[:,:,3][remove].max()),removedMask=removed.name,removedMaskSha256=sha(removed),protectedMask=protected_path.name,protectedMaskSha256=sha(protected_path),protectedRgbaSha256=hashlib.sha256(original[protected].tobytes()).hexdigest(),rgbThresholdUsed=False,cloudRepaintedRgbUsed=False,runtimeInstalled=False)
    (FOLDER/'alpha-protection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(report))

if __name__=='__main__':main()
