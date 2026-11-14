"""Read-only Pillow geometry measurements; copies PNG bytes but never saves pixels."""
from pathlib import Path
from collections import deque
import hashlib,json,shutil,statistics

HERE=Path(__file__).parent
ROOT=HERE.parents[3]
THRESHOLD=16
TARGET=1.5562753036437247
record=json.loads((HERE/'generation-record.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
from PIL import Image

def spans(alpha,y,left,right,threshold=128):
    out=[];start=None
    for x in range(left,right):
        opaque=alpha.getpixel((x,y))>=threshold
        if opaque and start is None:start=x
        if start is not None and (not opaque or x==right-1):
            end=x if not opaque else x+1
            if end-start>=2:out.append((start,end))
            start=None
    return out

def components(alpha,top,bottom):
    w=alpha.width;h=bottom-top;pix=alpha.load();seen=bytearray(w*h);found=[]
    for y in range(h):
        for x in range(w):
            idx=y*w+x
            if seen[idx] or pix[x,y+top]<128:continue
            queue=deque([(x,y)]);seen[idx]=1;points=[]
            while queue:
                xx,yy=queue.popleft();points.append((xx,yy+top))
                for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 0<=nx<w and 0<=ny<h and not seen[ny*w+nx] and pix[nx,ny+top]>=128:
                        seen[ny*w+nx]=1;queue.append((nx,ny))
            if len(points)>2000:
                xs,ys=zip(*points);found.append({'bounds':[min(xs),min(ys),max(xs)+1,max(ys)+1],'pixels':points,'area':len(points)})
    return sorted(found,key=lambda c:c['bounds'][0])

sheets={}
for item in record['files']:
    src=Path(item['generatedPath']);dest=HERE/item['file']
    if not dest.exists() or sha(dest)!=sha(src):shutil.copyfile(src,dest)
    item['sha256']=sha(dest);ref_paths=[p['path'] if isinstance(p,dict) else p for p in item['references']];item['references']=[{'path':p,'sha256':sha(Path(p))} for p in ref_paths]
    image=Image.open(dest);assert image.size==(1024,1536) and image.mode=='RGBA'
    alpha=image.getchannel('A');hist=alpha.histogram();frames=[];rects=[];origins=[];bounds=[]
    rejected=item['name']=='hero-v4-hit-death'
    for row in range(4):
        comps=components(alpha,row*384,(row+1)*384) if rejected else []
        if rejected and len(comps)!=4:raise ValueError('Need four independent bodies in row '+str(row))
        for col in range(4):
            cell=[col*256,row*384,(col+1)*256,(row+1)*384]
            if rejected:
                x0,y0,x1,y1=comps[col]['bounds'];box=[max(0,x0-3),max(row*384,y0-3),min(1024,x1+3),min((row+1)*384,y1+3)]
            else:
                bb=alpha.crop(tuple(cell)).point(lambda v:255 if v>=THRESHOLD else 0).getbbox()
                if not bb:raise ValueError('Empty cell')
                x0,y0,x1,y1=bb;box=[max(cell[0],cell[0]+x0-2),max(cell[1],cell[1]+y0-2),min(cell[2],cell[0]+x1+2),min(cell[3],cell[1]+y1+2)]
            l,t,r,b=box;local=alpha.crop(tuple(box));core=local.point(lambda v:255 if v>=128 else 0).getbbox()
            foreground=local.point(lambda v:255 if v>=THRESHOLD else 0).getbbox()
            if not core or not foreground:raise ValueError('Empty figure')
            contact_rows=range(max(t,t+core[3]-5),t+core[3]);support=[(x0,x1,y) for y in contact_rows for x0,x1 in spans(alpha,y,l,r)]
            sx0=min(s[0] for s in support);sx1=max(s[1] for s in support);sy=max(s[2] for s in support)
            origin=[(sx0+sx1)/2-l,sy-t]
            head_end=min(b,t+core[1]+round((core[3]-core[1])*.14))
            head_width=max([x1-x0 for y in range(t+core[1],head_end) for x0,x1 in spans(alpha,y,l,r)],default=0)
            foreign=0
            if rejected:
                foreign=sum(1 for j,c in enumerate(comps) if j!=col for x,y in c['pixels'] if l<=x<r and t<=y<b)
            rect=[l,t,r-l,b-t];rects.append(rect);origins.append(origin);bounds.append(list(foreground))
            frames.append({'index':row*4+col,'direction':['down','right','up','left'][row],'phase':col,'rect':rect,'origin':origin,'alphaBounds':list(foreground),'coreAlphaBounds128':list(core),'bodyHeadTopToSupportPixels':origin[1]-core[1],'headBandWidthPixels128':head_width,'groundSupportSpanGlobal':[sx0,sx1,sy],'foreignBodyCorePixelsInsideRect':foreign,'crossesNominalCell':l<cell[0] or r>cell[2],'contactMethod':'Last four/five opaque sole rows; dual-foot span midpoint when both boots contact. Falling/lying contact is only an unapproved candidate requiring visual review.' if rejected else 'Last four/five opaque sole rows; midpoint across both visible contacting boots or the single support boot. Empty hands avoid weapon-tip anchors.'})
    sheet={'image':'hero-v4/'+item['file'],'sourceFile':str(dest.relative_to(ROOT)).replace('\\','/'),'sha256':item['sha256'],'size':[1024,1536],'columns':4,'frameWidth':256,'frameHeight':384,'directions':['down','right','up','left'],'perFrameRects':rects,'perFrameOrigins':origins,'alphaBounds':bounds,'alphaBoundsThreshold':THRESHOLD,'alphaComparison':'>=16','alphaExtrema':list(alpha.getextrema()),'alpha0Fraction':hist[0]/sum(hist),'lowAlpha1To7Fraction':sum(hist[1:8])/sum(hist),'frames':frames,'integrationStatus':item['status']}
    sheets[item['name']]=sheet
    item['dimensions']=[1024,1536];item['alphaExtrema']=sheet['alphaExtrema'];item['alpha0Fraction']=sheet['alpha0Fraction']

base=sheets['hero-v4-dodge'];height=statistics.median(base['frames'][i]['bodyHeadTopToSupportPixels'] for i in (0,3));upp=TARGET/height
for sheet in sheets.values():sheet['worldUnitsPerPixel']=upp
def action(sheet_name,indices,fps):
    s=sheets[sheet_name]
    return {k:s[k] for k in ('image','frameWidth','frameHeight','columns','perFrameRects','perFrameOrigins','alphaBounds','worldUnitsPerPixel')}|{'frames':len(indices),'frameIndices':indices,'fps':fps,'loop':False}
meta={'version':'hero-v4-reactions-candidate-v1','runtimeInstalled':False,'status':'SOURCE_ONLY_PAUSED_AFTER_USER_READABILITY_FEEDBACK','directions':['down','right','up','left'],'canonicalHeadToGroundPixels':height,'targetProjectedBodyHeightMetres':TARGET,'sharedWorldUnitsPerPixel':upp,'scalePolicy':'One UPP shared across all three sheets; no per-frame height normalization and no raster stretch. Target is the old1.556m projected baseline, not the withdrawn1.8m preview.','backgroundAlphaLimit':'Original alpha includes1..7 low-alpha backdrop values; PNG bytes are unchanged. Root plans native builtin-unlit USE_ALPHA_TEST with alphaThreshold about.025 while keeping transparent blend. Geometry bounds use>=16 to distinguish foreground.','sheets':sheets,'candidateActions':{'dodge':action('hero-v4-dodge',[0,1,2,3],14),'spell':action('hero-v4-spell-interact',[0,1,3],6),'interact':action('hero-v4-spell-interact',[2,3],6)},'rejectedLayoutActions':{'hit':action('hero-v4-hit-death',[0,1],8),'death':action('hero-v4-hit-death',[2,3],6)},'limits':['No runtime PNG/manifest/code was installed. All three images remain source candidates pending revised clothing/background readability.','Hit-death first output has falling/lying bodies crossing nominal columns. Independent main-component rects are diagnostic only, not approved crops; foreign-body pixel counts identify bleed. No retry was generated after parent paused generation.','Body/head band alpha metrics describe silhouette scale, not a recovered skeleton or proof of final anatomy acceptance.','Death ground origins need explicit contact review after layout correction; no sword-tip heuristic was used.']}
dump(HERE/'metadata.json',meta);dump(HERE/'generation-record.json',record)
print(json.dumps({'files':len(sheets),'frames':sum(len(s['frames']) for s in sheets.values()),'sharedUPP':upp,'heightPixels':height,'hitForeignPixels':sum(f['foreignBodyCorePixelsInsideRect'] for f in sheets['hero-v4-hit-death']['frames']),'sourceOnly':True}))
