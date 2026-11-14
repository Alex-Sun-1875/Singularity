"""Composite the four genuinely left-facing cloud poses; protect other12 cells."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[2]
FOLDER=ROOT/'source-art/encounters/cloud-world-v2/actor-production-v1/R1-4'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--id',default='R1-4');parser.add_argument('--offset-x',type=int);parser.add_argument('--passing-y',type=int);args=parser.parse_args()
    folder=FOLDER.parent/args.id;source=folder/'sheet-v1.png';edit=folder/'left-views-generated-v2.png'
    original=np.asarray(Image.open(source).convert('RGBA'));result=original.copy()
    generated=Image.open(edit).convert('RGBA');assert generated.size==(1254,1254)
    # One uniform resize of the complete2x2 edit, not independent pose fitting.
    normalized=generated.resize((768,768),Image.Resampling.LANCZOS)
    edges=[0,314,627,941,1254];records=[];review=Image.new('RGBA',(384*4,384),(55,55,59,255));draw=ImageDraw.Draw(review)
    for row in range(4):
        frame=normalized.crop((row%2*384,row//2*384,row%2*384+384,row//2*384+384))
        # Complete contact toe needs6px rightward; passing sole needs4px up.
        # No scale change: later helmet registration owns walking pivots.
        dx=args.offset_x if args.offset_x is not None else 6 if args.id=='R1-4'else 0
        dy=(args.passing_y if args.passing_y is not None else -4 if args.id=='R1-4'else 0)if row==2 else 0
        shifted=Image.new('RGBA',(384,384));shifted.paste(frame,(dx,dy))
        height=edges[row+1]-edges[row];replacement=shifted.crop((35,35,348,35+height))
        before=np.asarray(frame)[:,:,3];after=np.asarray(replacement)[:,:,3]
        assert int(np.count_nonzero(before>3))==int(np.count_nonzero(after>3)),'Do not clip a generated toe/head/rope/stake'
        result[edges[row]:edges[row+1],314:627]=np.asarray(replacement)
        records.append(dict(pose=['idle','walk-a','walk-b','stake'][row],sourceDestinationRect=[314,edges[row],627,edges[row+1]],normalizedEditCell=[row%2*384,row//2*384,384,384],normalizedTranslation=[dx,dy],cropOffset=[35,35],allNormalizedAlphaAbove3PixelsRetained=True,perFrameRescale=False))
        review.alpha_composite(shifted,(row*384,0));draw.text((row*384+8,8),records[-1]['pose']+' / actual LEFT',fill='white')
    assert np.array_equal(original[:,:314],result[:,:314])and np.array_equal(original[:,627:],result[:,627:])
    other=0
    for row in range(4):
        for col in [0,2,3]:
            assert np.array_equal(original[edges[row]:edges[row+1],edges[col]:edges[col+1]],result[edges[row]:edges[row+1],edges[col]:edges[col+1]]);other+=1
    output=folder/'sheet-v2-composite.png';Image.fromarray(result).save(output);review.convert('RGB').save(folder/'left-composite-review.jpg',quality=94)
    report=dict(status='composite-prepared-for-independent-static-review',sourceSha256=sha(source),generatedEditSha256=sha(edit),outputSha256=sha(output),sourceFilesUnchanged=True,normalizedWholeEditSize=[768,768],uniformEditScale=768/1254,otherOriginalCellsRgbaByteExact=other,otherOriginalFacesCostumesAndPropsUnchanged=True,noMirroring=True,oldPassingStrayLineRemovedByWholeTargetCellReplacement=True,records=records,generationEvidence='left-repair-generation.json',artReview='Four actual left directions confirmed separately by root; composite/anchor review pending',runtimeInstalled=False)
    (folder/'left-composite-processing.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(args.id+' genuine-left composite: other12 cells byte-exact, all normalized alpha>3 target pixels retained, no mirror/per-frame scale.')

if __name__=='__main__':main()
