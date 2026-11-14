"""Take only specified repaired subjects from a full cloud sheet; preserve peers."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image
from scipy import ndimage

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def ownership(pixels):
    h,w=pixels.shape[:2];labels,_=ndimage.label(pixels[:,:,3]>=64);sizes=np.bincount(labels.ravel());ids=np.flatnonzero(sizes>=max(250,w*h/16*.008));ids=ids[ids>0]
    seeds=np.zeros((h,w),np.int16)
    for identifier in ids:
        yy,xx=np.where(labels==identifier);row=min(3,int(yy.mean()/h*4));col=min(3,int(xx.mean()/w*4));seeds[labels==identifier]=row*4+col+1
    assert set(np.unique(seeds))==set(range(17)),'Inspect connected/crossing subjects before compositing'
    _,nearest=ndimage.distance_transform_edt(seeds==0,return_indices=True);owners=seeds[nearest[0],nearest[1]];owners[pixels[:,:,3]<=3]=0
    return owners

def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder',type=Path);args=parser.parse_args();folder=args.folder
    spec=json.loads((folder/'repair-compose-spec.json').read_text('utf-8'));base=folder/spec['source'];edit=folder/spec['edit'];original=np.asarray(Image.open(base).convert('RGBA'));generated=Image.open(edit).convert('RGBA')
    source_size=generated.size
    if generated.size!=(original.shape[1],original.shape[0]):generated=generated.resize((original.shape[1],original.shape[0]),Image.Resampling.LANCZOS)
    repaired=np.asarray(generated);old_owner=ownership(original);new_owner=ownership(repaired);ids=[row*4+col+1 for row,col in spec['targets']]
    old_selected=np.isin(old_owner,ids);new_selected=np.isin(new_owner,ids);other=(old_owner>0)&~old_selected
    assert not np.any(new_selected&other),'Repaired tip overlaps an original peer; review alignment before compositing'
    result=original.copy();result[old_selected]=[0,0,0,0];result[new_selected]=repaired[new_selected]
    assert np.array_equal(result[other],original[other])
    assert np.array_equal(result[new_selected],repaired[new_selected])
    output=folder/spec['output'];Image.fromarray(result).save(output)
    h,w=original.shape[:2];grid=np.zeros((h,w),bool)
    for row,col in spec['targets']:grid[round(row*h/4):round((row+1)*h/4),round(col*w/4):round((col+1)*w/4)]=True
    beyond=int(np.count_nonzero(np.any(result!=original,2)&~grid))
    report=dict(status='protected-subject-composite-prepared',sourceSha256=sha(base),editedSha256=sha(edit),outputSha256=sha(output),editedOriginalSize=list(source_size),uniformWholeEditResampleTo=[w,h],targets=spec['targets'],otherOriginalSubjectCount=16-len(ids),allOtherOriginalAlphaAbove3SubjectRgbaExact=True,allSelectedRepairedAlphaAbove3PixelsRetained=True,otherNominalCellsByteExact=beyond==0,changedGutterPixelsBeyondNominalTargetCells=beyond,gutterReason='Whole-subject ownership preserves complete bow/weapon tips that cross the nominal row boundary; original other subjects remain exact',perFrameRescale=False,sourceFilesUnchanged=True,runtimeInstalled=False)
    (folder/'repair-composite-processing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print(json.dumps(report))

if __name__=='__main__':main()
