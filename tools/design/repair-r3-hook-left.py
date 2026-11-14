"""Repack the wide repaired LEFT hook poses without shrinking/cutting any pose."""
from pathlib import Path
import hashlib,json,runpy
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'source-art/encounters/cloud-world-v2/actor-production-v1/R3-4'
ownership=runpy.run_path(str(Path(__file__).with_name('composite-enemy-sheet-repair.py')))['ownership']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    source=FOLDER/'sheet-v1.png';edit=FOLDER/'left-views-generated-v2.png';old=np.asarray(Image.open(source).convert('RGBA'));old_owner=ownership(old)
    normalized=Image.open(edit).convert('RGBA').resize((768,768),Image.Resampling.LANCZOS);new=np.asarray(normalized)
    labels,_=ndimage.label(new[:,:,3]>=64);sizes=np.bincount(labels.ravel());ids=np.flatnonzero(sizes>700);ids=ids[ids>0];seeds=np.zeros((768,768),np.int16)
    for identifier in ids:
        yy,xx=np.where(labels==identifier);seeds[labels==identifier]=min(1,int(yy.mean()/384))*2+min(1,int(xx.mean()/384))+1
    assert set(np.unique(seeds))==set(range(5));_,nearest=ndimage.distance_transform_edt(seeds==0,return_indices=True);new_owner=seeds[nearest[0],nearest[1]];new_owner[new[:,:,3]<=3]=0
    cell=512;output=np.zeros((cell*4,cell*4,4),np.uint8);records=[];old_count=0;new_count=0
    def place(pixels,owners,identifier,row,col,cx,cy,kind):
        nonlocal old_count,new_count
        yy,xx=np.where(owners==identifier);left,top,right,bottom=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1);mask=owners[top:bottom,left:right]==identifier
        x=col*cell+round(cell/2+left-cx);y=row*cell+round(cell/2+top-cy);patch=pixels[top:bottom,left:right]
        assert x-col*cell>=16 and y-row*cell>=16 and x+right-left<=(col+1)*cell-16 and y+bottom-top<=(row+1)*cell-16
        target=output[y:y+bottom-top,x:x+right-left];assert not np.any(target[:,:,3][mask]);target[mask]=patch[mask]
        assert np.array_equal(target[mask],patch[mask]);records.append(dict(pose=row,directionColumn=col,kind=kind,sourceRect=[left,top,right,bottom],destination=[x,y],rgbaPixelsExact=int(mask.sum()),perFrameScale=False))
        if kind=='original-peer':old_count+=int(mask.sum())
        else:new_count+=int(mask.sum())
    edges=[0,314,627,941,1254]
    for row in range(4):
        for col in [0,2,3]:place(old,old_owner,row*4+col+1,row,col,(edges[col]+edges[col+1])/2,(edges[row]+edges[row+1])/2,'original-peer')
        er,ec=divmod(row,2);place(new,new_owner,row+1,row,1,ec*384+192,er*384+192,'repaired-left')
    assert old_count==int(np.count_nonzero((old_owner>0)&~np.isin(old_owner,[2,6,10,14])))
    assert new_count==int(np.count_nonzero(new[:,:,3]>3))
    result=FOLDER/'sheet-v2-expanded-composite.png';Image.fromarray(output).save(result)
    report=dict(status='wide-column-protected-repack-prepared',sourceSha256=sha(source),editedSha256=sha(edit),outputSha256=sha(result),sourceSize=[1254,1254],normalizedEditSize=[768,768],outputSize=[2048,2048],allCellsUniformlyExpandedTo=512,reason='Repaired hook primary is367px wide, exceeding native313px cell; preserve it without clipping or per-pose shrinking.',originalPeerCount=12,allOriginalPeerAlphaAbove3RgbaExact=True,allRepairedAlphaAbove3PixelsRetainedExactlyOnce=True,originalPeerCoordinatesRepacked=True,originalNominalCellsByteExactAtOriginalCoordinates=False,onlyAlphaAtMost3Omitted=True,mirrored=False,perFrameRescale=False,records=records,runtimeInstalled=False)
    (FOLDER/'left-expanded-composite-processing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8');print('R3-4: uniform512 cells,12 original subjects exact,4 complete genuine LEFT subjects, no scale/mirror/cut.')

if __name__=='__main__':main()
