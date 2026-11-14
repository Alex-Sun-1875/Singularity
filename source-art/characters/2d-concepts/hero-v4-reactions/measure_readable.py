"""Read alpha only, copy PNG bytes, and expose standard FlatAction fields."""
from pathlib import Path
import ast,json,hashlib,shutil,statistics
from PIL import Image
HERE=Path(__file__).parent
# Reuse measurement functions without executing the original script's writes.
tree=ast.parse((HERE/'measure_metadata.py').read_text(encoding='utf-8'))
tree.body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef))]
exec(compile(tree,'measurement_functions','exec'),globals())
record_path=HERE/'generation-readable-v2.json'
record=json.loads(record_path.read_text(encoding='utf-8'))
extra_path=HERE/'hit-death-readable-generation.json'
if extra_path.exists():
    extra=json.loads(extra_path.read_text(encoding='utf-8'))
    if not any(v['name']==extra['name'] for v in record['files']):record['files'].append(extra)
sheets={}
for item in record['files']:
    for src,dst in [(item.get('paletteGeneratedPath'),item.get('paletteFailedFile')),(item['finalGeneratedPath'],item['file'])]:
        if src and dst:
            src=Path(src);dst=HERE/dst
            if not dst.exists() or sha(src)!=sha(dst):shutil.copyfile(src,dst)
    path=HERE/item['file'];image=Image.open(path);assert image.mode=='RGBA'
    w,h=image.size;cw,ch=w/4,h/4;alpha=image.getchannel('A');hist=alpha.histogram();frames=[];rects=[];origins=[];bounds=[]
    square_hit=item.get('kind')=='hit-death-square'
    all_comps=components(alpha.point(lambda v:255 if v>=16 else 0),0,h) if square_hit else []
    groups=[sorted([v for v in all_comps if min(3,int((v['bounds'][1]+v['bounds'][3])/2/ch))==row],key=lambda v:v['bounds'][0]) for row in range(4)] if square_hit else []
    if square_hit:assert len(all_comps)==16 and all(len(g)==4 for g in groups),'Reject incomplete independent hit/death bodies'
    for row in range(4):
        for col in range(4):
            cell=tuple(round(v) for v in (col*cw,row*ch,(col+1)*cw,(row+1)*ch))
            if square_hit:
                x0,y0,x1,y1=groups[row][col]['bounds'];l=max(0,x0-2);t=max(0,y0-2);r=min(w,x1+2);b=min(h,y1+2)
            else:
                bb=alpha.crop(cell).point(lambda v:255 if v>=16 else 0).getbbox();assert bb
                x0,y0,x1,y1=bb;l=max(cell[0],cell[0]+x0-2);t=max(cell[1],cell[1]+y0-2);r=min(cell[2],cell[0]+x1+2);b=min(cell[3],cell[1]+y1+2)
            local=alpha.crop((l,t,r,b));core=local.point(lambda v:255 if v>=128 else 0).getbbox();assert core
            ab=local.point(lambda v:255 if v>=16 else 0).getbbox()
            landing=square_hit and col>=2
            contact_depth=max(5,round((core[3]-core[1])*.25)) if landing else 5
            support=[(x0,x1,y) for y in range(max(t,t+core[3]-contact_depth),t+core[3]) for x0,x1 in spans(alpha,y,l,r)]
            assert support
            sx0=min(v[0] for v in support);sx1=max(v[1] for v in support);sy=max(v[2] for v in support)
            origin=[(sx0+sx1)/2-l,sy-t]
            head_end=min(b,t+core[1]+round((core[3]-core[1])*.14))
            hw=max([x1-x0 for y in range(t+core[1],head_end) for x0,x1 in spans(alpha,y,l,r)],default=0)
            rect=[l,t,r-l,b-t];rects.append(rect);origins.append(origin);bounds.append(list(ab))
            foreign=sum(1 for rr,g in enumerate(groups) for cc,other in enumerate(g) if (rr,cc)!=(row,col) for x,y in other['pixels'] if l<=x<r and t<=y<b) if square_hit else 0
            assert foreign==0,'Reject hit/death crop containing another body'
            frames.append({'index':row*4+col,'direction':['down','right','up','left'][row],'phase':col,'rect':rect,'origin':origin,'alphaBounds':list(ab),'coreAlphaBounds128':list(core),'headToSupportPixels':origin[1]-core[1],'headBandWidthPixels128':None if landing else hw,'supportSpanGlobal':[sx0,sx1,sy],'contactType':'lower landing-contact span (hand/hip/boot silhouette), parent native review required' if landing else 'opaque sole support span; two-foot midpoint when both contact','foreignBodyPixelsInsideRect':foreign,'crossesNominalGrid':l<cell[0] or r>cell[2] or t<cell[1] or b>cell[3]})
    grid_x=sorted(set([0,w-1]+[round(c*cw)-1 for c in range(1,4)]+[round(c*cw) for c in range(1,4)]));grid_y=sorted(set([0,h-1]+[round(c*ch)-1 for c in range(1,4)]+[round(c*ch) for c in range(1,4)]))
    gutter=max([alpha.getpixel((x,y)) for x in grid_x for y in range(h)]+[alpha.getpixel((x,y)) for y in grid_y for x in range(w)])
    item['sha256']=sha(path);item['targetSha256']=sha(Path(item['target']));item['referenceSha256']=sha(Path(item['reference']));item['dimensions']=[w,h]
    if item.get('paletteGeneratedPath'):item['paletteFailedSha256']=sha(Path(item['paletteGeneratedPath']))
    item['alphaExtrema']=list(alpha.getextrema());item['alpha0Fraction']=hist[0]/sum(hist);item['gutterMaxAlpha']=gutter
    sheets[item['name']]={'image':'hero-v4/'+item['file'],'size':[w,h],'columns':4,'frameWidth':cw,'frameHeight':ch,'perFrameRects':rects,'perFrameOrigins':origins,'alphaBounds':bounds,'alphaBoundsThreshold':16,'frames':frames,'sha256':item['sha256'],'alphaExtrema':item['alphaExtrema'],'alpha0Fraction':item['alpha0Fraction'],'gutterMaxAlpha':gutter}
height=statistics.median(sheets['hero-v4-dodge-readable']['frames'][i]['headToSupportPixels'] for i in (0,3));upp=1.5562753036437247/height
actions={}
for name,indices,fps,key in [('dodge',[0,1,2,3],14,'hero-v4-dodge-readable'),('spell',[0,1,3],6,'hero-v4-spell-interact-readable'),('interact',[2,3],6,'hero-v4-spell-interact-readable')]:
    s=sheets[key];actions[name]={k:s[k] for k in ('image','columns','frameWidth','frameHeight','perFrameRects','perFrameOrigins','alphaBounds')};actions[name].update({'frames':len(indices),'frameIndices':indices,'fps':fps,'loop':False,'worldUnitsPerPixel':upp})
if 'hero-v4-hit-death-readable' in sheets:
    s=sheets['hero-v4-hit-death-readable'];hit_height=statistics.median(s['frames'][i]['headToSupportPixels'] for i in (0,4,8,12));hit_upp=1.5562753036437247/hit_height
    s['standingRecoilHeightPixels']=hit_height;s['worldUnitsPerPixel']=hit_upp;s['scaleNote']='Actual square1254px source has a different pixel density from1024x1536 action sheets. One UPP is shared by hit and death, derived once from standing recoil body; falling/lying heights are never normalized.'
    for name,indices,fps in [('hit',[0,1],8),('death',[2,3],6)]:
        actions[name]={k:s[k] for k in ('image','columns','frameWidth','frameHeight','perFrameRects','perFrameOrigins','alphaBounds')};actions[name].update({'frames':len(indices),'frameIndices':indices,'fps':fps,'loop':False,'worldUnitsPerPixel':hit_upp})
meta={'version':'hero-v4-reactions-readable-v2','status':'DODGE_SPELL_INTERACT_SOURCE_READY_PENDING_NATIVE_QA','runtimeInstalled':False,'directions':['down','right','up','left'],'targetProjectedBodyHeightMetres':1.5562753036437247,'canonicalDodgeReadyHeightPixels':height,'sharedWorldUnitsPerPixel':upp,'scalePolicy':'One UPP across dodge/spell/interact from neutral ready, never per-phase height normalization.','groundOriginMethod':'Midpoint of opaque contacting boot spans in final4/5 sole rows, both feet when both contact; no sword-tip anchors.','alphaPolicy':'Original built-in extraction output bytes. Alpha>=16 geometry; native unlit low-alpha test remains parent-owned. Failed recolor-alpha candidates preserved as siblings.','actions':actions,'sheets':sheets,'pending':['hit','death'],'limits':['No runtime PNG/meta or game manifest was touched during parent import freeze.','Generated recolor/extraction preserves poses by prompt and visual review but is not a pixel-identity guarantee; parent native phase review remains required.']}
if 'death' in actions:
    meta['status']='ALL_FIVE_REACTION_FIELDS_SOURCE_READY_PENDING_PARENT_ACCEPTANCE_NATIVE_QA';meta['pending']=[];meta['groundOriginMethod']+=' Falling/lying frames use lower-quarter landing contact span, not the death image height or sword tips; parent must verify corpse placement.'
dump(HERE/'metadata-readable.json',meta);dump(record_path,record)
print(json.dumps({'actions':list(actions),'upp':upp,'heightPixels':height,'sheets':{k:{'size':s['size'],'alpha':s['alphaExtrema'],'gutterMaxAlpha':s['gutterMaxAlpha']} for k,s in sheets.items()}}))
