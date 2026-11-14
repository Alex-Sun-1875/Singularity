"""Measure accessory-only reaction siblings. PIL reads alpha; PNGs are copied unchanged."""
from pathlib import Path
from collections import deque
from PIL import Image
import ast, copy, hashlib, json, shutil
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REF = ROOT/'source-art/characters/2d-concepts/hero-v4-reactions'
SOURCE = HERE/'sources/bow-reactions'
RUNTIME = ROOT/'src/cocos/assets/resources/flat2d/characters/raphael/hero-v4'
baseline_path = REF/'metadata-readable.json'
baseline_bytes = baseline_path.read_bytes()
baseline = json.loads(baseline_bytes)
tree = ast.parse((REF/'measure_metadata.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'<existing-measurement-functions>','exec'))

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def body_translation(old_path,new_path,old_rect,index,square):
    # Small binary-alpha registration uses only legs/boots, away from the added upper-back quiver.
    # Bottom-five sole contact alone is unstable when AA changes which boot reaches the last row.
    old=np.asarray(Image.open(old_path).getchannel('A'))>=128
    new=np.asarray(Image.open(new_path).getchannel('A'))>=128
    x,y,w,h=old_rect;col=index%4
    if square and col==3:
        l,t,r,b=round(x+w*.55),y,x+w,y+h  # prone: lower legs occupy right half
    else:
        l,t,r,b=x,round(y+h*.55),x+w,y+h
    l,t,r,b=max(8,l),max(8,t),min(old.shape[1]-8,r),min(old.shape[0]-8,b)
    original=old[t:b,l:r];best=None
    for dy in range(-6,7):
        for dx in range(-6,7):
            candidate=new[t+dy:b+dy,l+dx:r+dx]
            union=np.count_nonzero(original|candidate)
            score=np.count_nonzero(original&candidate)/union
            key=(score,-abs(dx)-abs(dy))
            if best is None or key>best[0]:best=(key,dx,dy)
    return [best[1],best[2]],round(best[0][0],5)

def measure(path, square):
    im=Image.open(path); assert im.mode=='RGBA'
    w,h=im.size;cw,ch=w/4,h/4;a=im.getchannel('A')
    groups=[]
    if square:
        comps=components(a.point(lambda v:255 if v>=16 else 0),0,h)
        groups=[sorted([c for c in comps if min(3,int((c['bounds'][1]+c['bounds'][3])/2/ch))==row],key=lambda c:c['bounds'][0]) for row in range(4)]
        assert len(comps)==16 and all(len(g)==4 for g in groups), 'Four independent bodies per row required'
    rects=[];bounds=[];contacts=[];frames=[]
    for row in range(4):
        for col in range(4):
            cell=[round(col*cw),round(row*ch),round((col+1)*cw),round((row+1)*ch)]
            if square:
                x0,y0,x1,y1=groups[row][col]['bounds']
                l,t,r,b=max(0,x0-2),max(0,y0-2),min(w,x1+2),min(h,y1+2)
            else:
                bb=a.crop(tuple(cell)).point(lambda v:255 if v>=16 else 0).getbbox();assert bb
                l,t,r,b=max(cell[0],cell[0]+bb[0]-2),max(cell[1],cell[1]+bb[1]-2),min(cell[2],cell[0]+bb[2]+2),min(cell[3],cell[1]+bb[3]+2)
            local=a.crop((l,t,r,b));core=local.point(lambda v:255 if v>=128 else 0).getbbox();assert core
            ab=local.point(lambda v:255 if v>=16 else 0).getbbox();assert ab
            depth=max(5,round((core[3]-core[1])*.25))if square and col>=2 else 5
            support=[(x0,x1,y) for y in range(max(t,t+core[3]-depth),t+core[3])for x0,x1 in spans(a,y,l,r)]
            assert support
            sx0,sx1,sy=min(v[0]for v in support),max(v[1]for v in support),max(v[2]for v in support)
            foreign=sum(1 for rr,g in enumerate(groups)for cc,c in enumerate(g)if(rr,cc)!=(row,col)for x,y in c['pixels']if l<=x<r and t<=y<b)if square else 0
            assert foreign==0
            rect=[l,t,r-l,b-t];rects.append(rect);bounds.append(list(ab));contacts.append([(sx0+sx1)/2,sy])
            frames.append({'index':row*4+col,'rect':rect,'supportSpan':[sx0,sx1,sy],'foreignBodyPixelsInsideRect':foreign,'contactMethod':'lower-quarter landing contact'if square and col>=2 else'opaque bottom-five sole rows'})
    hist=a.histogram()
    empty=[a.getpixel(p)for p in[(0,0),(w-1,0),(0,h-1),(w-1,h-1),(w//4,20),(w//2,20),(3*w//4,20)]]
    return {'size':[w,h],'rects':rects,'alphaBounds':bounds,'contacts':contacts,'frames':frames,'alphaExtrema':list(a.getextrema()),'alphaZeroFraction':hist[0]/sum(hist),'alphaUnder6Fraction':sum(hist[:6])/sum(hist),'blankSamples':empty}

meta={'version':'hero-v4-bow-reactions-v1','status':'SOURCE_RUNTIME_FROZEN_PENDING_PARENT_BUILD_NATIVE_REVIEW','directions':baseline['directions'],'actions':{},'records':{},'sourcePolicy':'Native imagegen PNG bytes preserved; alpha measurement and JSON only. Existing shared reactions retained.','scalePolicy':'Exact original per-sheet body UPP retained. No quiver/arrow-tip height normalization.','temporalPolicy':'All fps/frameIndices/frames/loop copied exactly from approved shared reaction metadata.'}
for kind,states in [('dodge',['dodge']),('spell-interact',['spell','interact']),('hit-death',['hit','death'])]:
    filename=f'hero-v4-bow-{kind}-readable.png';path=SOURCE/filename;target=REF/f'hero-v4-{kind}-readable.png'
    before=measure(target,kind=='hit-death');after=measure(path,kind=='hit-death');assert after['size']==before['size']
    state=states[0];original=baseline['actions'][state]
    origins=[];points=[];drifts=[];registrations=[]
    for idx,(rect,contact,old_contact)in enumerate(zip(after['rects'],after['contacts'],before['contacts'])):
        old_rect=original['perFrameRects'][idx];old_origin=original['perFrameOrigins'][idx]
        delta,score=body_translation(target,path,old_rect,idx,kind=='hit-death')
        point=[old_rect[0]+old_origin[0]+delta[0],old_rect[1]+old_origin[1]+delta[1]]
        origin=[point[0]-rect[0],point[1]-rect[1]]
        assert 0<=origin[0]<=rect[2]and 0<=origin[1]<=rect[3]
        origins.append(origin);points.append(point);drifts.append(delta)
        registrations.append({'index':idx,'bodyOnlyTranslationXY':delta,'lowerBodyMaskIoU':score,'bottomFiveContactDeltaDiagnosticOnly':[contact[0]-old_contact[0],contact[1]-old_contact[1]]})
    sha256=digest(path);shutil.copyfile(path,RUNTIME/filename);assert digest(RUNTIME/filename)==sha256
    for state in states:
        action=copy.deepcopy(baseline['actions'][state]);action.update({'image':'hero-v4/'+filename,'perFrameRects':after['rects'],'perFrameOrigins':origins,'alphaBounds':after['alphaBounds'],'sourcePNG':path.relative_to(ROOT).as_posix(),'sourcePNGSHA256':sha256})
        assert action['worldUnitsPerPixel']==baseline['actions'][state]['worldUnitsPerPixel']
        for key in ['fps','frames','frameIndices','loop','frameWidth','frameHeight','columns']:
            assert action[key]==baseline['actions'][state][key]
        meta['actions'][state+'_W07']=action
    meta['records'][filename]={'sourcePNG':path.relative_to(ROOT).as_posix(),'sourceSHA256':sha256,'sourceRuntimeSHAEqual':True,'editTargetPNG':target.relative_to(ROOT).as_posix(),'editTargetSHA256':digest(target),'accessoryReferences':[{'sourcePNG':f'source-art/characters/2d-concepts/hero-v4/{name}','sourceSHA256':digest(ROOT/'source-art/characters/2d-concepts/hero-v4'/name)}for name in['W07-walk-readable.png','W07-run-a-readable.png']],'worldUnitsPerPixelPreserved':original['worldUnitsPerPixel'],'absoluteGroundPoints':points,'pairedBodyTranslationXY':drifts,'bodyRegistration':registrations,'registrationMethod':'Original origin plus small lower-body alpha translation. Standing/falling: lower55%-100% height. Prone: right55%-100% width legs. Quiver and arrow tips excluded; no pixel resampling. Bottom-five contact stored as diagnostic only.',**{k:v for k,v in after.items()if k not in['rects','contacts','alphaBounds']}}
assert baseline_path.read_bytes()==baseline_bytes,'Shared metadata must remain unchanged'
meta['sharedMetadataPNGSourceSHA256']=hashlib.sha256(baseline_bytes).hexdigest()
assert set(meta['actions'])=={'dodge_W07','spell_W07','interact_W07','hit_W07','death_W07'}
output=HERE/'metadata-bow-reactions.json';output.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'actions':list(meta['actions']),'metadataSHA256':digest(output),'images':{k:{'size':v['size'],'sha256':v['sourceSHA256'],'UPP':v['worldUnitsPerPixelPreserved'],'maxBodyTranslationXY':[max(abs(d[j])for d in v['pairedBodyTranslationXY'])for j in[0,1]],'minBodyMaskIoU':min(x['lowerBodyMaskIoU']for x in v['bodyRegistration']),'blankSamples':v['blankSamples']}for k,v in meta['records'].items()}},ensure_ascii=False))
