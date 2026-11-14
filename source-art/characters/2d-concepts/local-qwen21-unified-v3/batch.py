"""Adapt every referenced player phase, then install a verified complete set.

Uses prior semantic-frame packing and existing image libraries, not new model
inference per phase. No full original atlas or manifest backups are created.
"""
from pathlib import Path
import argparse
import collections
import copy
import json
import os
import sys
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image,ImageDraw
import appearance as art
import prepare

HERE=prepare.HERE
REVISION='qwen21-unified-v3'
packing=art.load('existing_semantic_atlas_packer',HERE.parent/'local-qwen21-consistency-v2/game-install/install.py')

def jsonwrite(path,obj):
    path.write_bytes((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def prepare_batch(acting_only=False,selected_images=None):
    inv=json.loads((HERE/'inventory.json').read_text());manifest=json.loads(prepare.MANIFEST.read_text())
    if prepare.digest(prepare.MANIFEST)!=inv['manifestSHA256']:raise RuntimeError('Manifest changed after reference preparation')
    locations={(r['image'],r['index']):r['hair'] for r in json.loads((HERE/'head-locations.json').read_text())['frames']}
    grouped=collections.defaultdict(list)
    for r in inv['frames']:grouped[r['image']].append(r)
    masters={d:Image.open(HERE/'approved'/f'standing-{d}.png').convert('RGBA') for d in prepare.DIRECTIONS}
    attacks={d:Image.open(HERE/'approved'/f'attack-{d}.png').convert('RGBA') for d in prepare.DIRECTIONS}
    candidate=HERE/'candidate-runtime';candidate.mkdir(exist_ok=True)
    geometry={};reports=[];image_reports=[]
    previous=json.loads((HERE/'batch-report.json').read_text()) if acting_only or selected_images else None
    previous_phases=collections.defaultdict(list)
    if previous:
        for row in previous['phases']:previous_phases[row['image']].append(row)
    previous_images={r['image']:r for r in previous['images']} if previous else {}
    # A small representative contact sheet, same scale for every original pose.
    review=Image.new('RGB',(1080,((len(grouped)+5)//6)*204),'#262628');draw=ImageDraw.Draw(review)
    for ordinal,(name,records) in enumerate(grouped.items()):
        selected=(name in selected_images) if selected_images else (not acting_only or any(any(any(k in v['action'] for k in ('hit','death','dodge')) for v in r['refs']) for r in records))
        if not selected:
            page=Image.open(candidate/name).convert('RGBA');image_reports.append(previous_images[name])
            for row in previous_phases[name]:
                reports.append(row);x,y,w,h=row['rect'];b=packing.bounds(page.crop((x,y,x+w,y+h)))
                geometry[(name,row['index'])]=dict(rect=row['rect'],origin=row['origin'],bounds=b)
            representative=next((rr for rr in records if rr['direction']=='right'),records[0])
            g=geometry[(name,representative['index'])];r=copy.copy(representative);r.update(rect=g['rect'],origin=g['origin'])
            thumb=prepare.canvas(r,{name:page}).resize((120,180),Image.Resampling.LANCZOS)
            x=(ordinal%6)*180;y=(ordinal//6)*204+22;review.paste(thumb,(x+30,y),thumb);draw.text((x+3,y-18),name.split('/')[-1][:24],fill='white')
            continue
        source=Image.open(prepare.ACTOR/name).convert('RGBA');patches=[]
        padded_source=Image.new('RGBA',(source.width+64,source.height+64));padded_source.paste(source,(32,32))
        example_action=manifest['actions'][records[0]['action']]
        columns=example_action.get('columns',manifest['columns'])
        rows=max(r['index']//columns for r in records)+1
        for r in records:
            before=prepare.canvas(r,{name:source});key=(name,r['index']);info=locations[key]
            refs=r['refs'];d=r['direction']
            acting=any(any(k in v['action'] for k in ('hit','death','dodge')) for v in refs)
            hc=info['center'];extra_view=acting and (hc[0]<120 or hc[0]>392 or hc[1]<100 or hc[1]>650)
            if any(v['action']=='explore_idle_W01' for v in refs):
                after=masters[d].copy();head={'applied':False,'method':'accepted standing identity and actual local-Qwen clothing repair'};color={'approved_master':True}
            elif any(v['action']=='attack_sword_W01' and v['phase']==1 for v in refs):
                after=attacks[d].copy();head={'applied':True,'method':'standing-derived head plus actual masked local-Qwen neck repair'}
                after,color=art.grade(after,masters[d],info)
            else:
                if extra_view:
                    after,color=art.grade(before,masters[d],info)
                    head={'applied':False,'method':'head handled in shifted editing viewport'}
                else:
                    after,head=art.retarget_head(before,r,info)
                    after,color=art.grade(after,masters[d],info,r.get('head_protection_mask'))
            working_record=copy.copy(r)
            working_record['rect']=[r['rect'][0]+32,r['rect'][1]+32,*r['rect'][2:]]
            working_record['absolute_anchor']=[v+32 for v in r['absolute_anchor']]
            patch,(px,py),pack=packing.native_patch(before,after,working_record,padded_source)
            if extra_view:
                # Wide lying poses put their head outside the ordinary 512px
                # body window. Edit the head in a translated window, retaining
                # the original world anchor and the already graded full body.
                colored_source=padded_source.copy();colored_source.paste(patch,(px,py))
                shift=[256-hc[0],200-hc[1]]
                head_record=copy.copy(r);head_record['editing_viewport_shift']=shift
                shifted_info=copy.deepcopy(info)
                shifted_info['center']=[hc[0]+shift[0],hc[1]+shift[1]]
                shifted_info['box']=[info['box'][i]+shift[i%2] for i in range(4)]
                head_before=prepare.canvas(head_record,{name:source})
                head_after,head=art.retarget_head(head_before,head_record,shifted_info)
                working_head=copy.copy(working_record)
                working_head['absolute_anchor']=[working_record['absolute_anchor'][i]-shift[i]/r['scale'] for i in range(2)]
                patch,(px,py),pack=packing.native_patch(head_before,head_after,working_head,colored_source)
                head['editingViewportShift']=shift
            px-=32;py-=32
            if 'nativeWorkingRect' in pack:
                pack['nativeWorkingRect'][0]-=32;pack['nativeWorkingRect'][1]-=32
            b=packing.bounds(patch)
            crop=[max(0,b[0]-2),max(0,b[1]-2),min(patch.width,b[2]+2),min(patch.height,b[3]+2)]
            rect=[px+crop[0],py+crop[1],crop[2]-crop[0],crop[3]-crop[1]]
            anchor=r['absolute_anchor'];origin=[anchor[0]-rect[0],anchor[1]-rect[1]]
            bounds=[b[0]-crop[0],b[1]-crop[1],b[2]-crop[0],b[3]-crop[1]]
            geometry[key]=dict(rect=rect,origin=origin,bounds=bounds)
            patches.append((r,patch,px,py))
            reports.append(dict(image=name,index=r['index'],direction=d,actions=[v['action'] for v in refs],head=head,color=color,
                packing=pack,rect=rect,origin=origin,absoluteAnchorRetained=anchor))
            representative=next((rr['index'] for rr in records if rr['direction']=='right'),records[0]['index'])
            if r['index']==representative:
                thumb=after.resize((120,180),Image.Resampling.LANCZOS)
                x=(ordinal%6)*180;y=(ordinal//6)*204+22
                review.paste(thumb,(x+30,y),thumb)
                draw.text((x+3,y-18),name.split('/')[-1][:24],fill='white')
        # Some old sheets leave only 0-2 native pixels between a crown and the
        # preceding row's boots. Add atlas gutters only if needed. This moves
        # packed coordinates, never body/weapon pixels or world-space anchors.
        outer_left=max(0,-min(px for _,_,px,_ in patches));outer_top=max(0,-min(py for _,_,_,py in patches))
        outer_right=max(0,max(px+p.width for _,p,px,_ in patches)-source.width)
        outer_bottom=max(0,max(py+p.height for _,p,_,py in patches)-source.height)
        for gutter in (0,16,32,64):
            page=Image.new('RGBA',(source.width+outer_left+outer_right+(columns-1)*gutter,source.height+outer_top+outer_bottom+(rows-1)*gutter))
            own_labels=np.zeros((page.height,page.width),np.uint16);placed=[];safe=True;pending_geometry={}
            for number,(r,patch,px,py) in enumerate(patches,1):
                dx=outer_left+(r['index']%columns)*gutter;dy=outer_top+(r['index']//columns)*gutter
                tx,ty=px+dx,py+dy;alpha=np.asarray(patch)[...,3]
                region=own_labels[ty:ty+patch.height,tx:tx+patch.width]
                if np.any((alpha>=16)&(region!=0)):safe=False;break
                region[alpha>=16]=number
                page.paste(patch,(tx,ty),Image.fromarray(np.uint8(alpha>0)*255))
                placed.append((r,patch,tx,ty,dx,dy))
            if not safe:continue
            for number,(r,patch,px,py,dx,dy) in enumerate(placed,1):
                b=packing.bounds(patch)
                for padding in (2,1,0):
                    crop=[max(0,b[0]-padding),max(0,b[1]-padding),min(patch.width,b[2]+padding),min(patch.height,b[3]+padding)]
                    x,y=px+crop[0],py+crop[1];w,h=crop[2]-crop[0],crop[3]-crop[1]
                    labels=own_labels[y:y+h,x:x+w]
                    if not np.any((labels!=0)&(labels!=number)):break
                else:safe=False;break
                anchor=r['absolute_anchor'];origin=[anchor[0]+dx-x,anchor[1]+dy-y]
                pending_geometry[(name,r['index'])]=dict(rect=[x,y,w,h],origin=origin,bounds=[b[0]-crop[0],b[1]-crop[1],b[2]-crop[0],b[3]-crop[1]])
                reports[-len(records)+number-1].update(rect=[x,y,w,h],origin=origin,cropPadding=padding,atlasTranslation=[dx,dy])
            if safe:geometry.update(pending_geometry);break
        else:raise RuntimeError('Could not separate complete phase crops: '+name)
        dest=candidate/name;dest.parent.mkdir(parents=True,exist_ok=True);page.save(dest)
        image_reports.append(dict(image=name,beforeSHA256=prepare.digest(prepare.ACTOR/name),afterSHA256=prepare.digest(dest),size=list(page.size),originalSize=list(source.size),atlasGutterAdded=gutter,outerAtlasPadding=[outer_left,outer_top,outer_right,outer_bottom]))
        print(f'Prepared {ordinal+1}/{len(grouped)} atlases; {len(reports)} physical frames',flush=True)
    review.save(HERE/'all-assets-review-small.jpg',quality=88)
    updated=copy.deepcopy(manifest)
    mutable={'perFrameRects','frameRectsByImage','perFrameOrigins','alphaBounds','perPhaseAlphaBounds','originMethod',
        'sourcePNGs','sourcePNGSHA256s','sourceDesign','sourceDesignSHA256','identityReference','identityReferenceSHA256',
        'identityReferenceScope','rawOutputPNGs','rawOutputPNGSHA256s','localQwenProcessing','appearanceAuthority'}
    hashes={r['image']:r['afterSHA256'] for r in image_reports}
    for key,a in updated['actions'].items():
        old=manifest['actions'][key];names=list(dict.fromkeys(a.get('frameImages',[a['image']])))
        for name in names:
            rects=a.get('frameRectsByImage',{}).get(name.removesuffix('.png'),a['perFrameRects'])
            for i in range(len(rects)):
                g=geometry.get((name,i))
                if g is not None:rects[i]=g['rect']
        a['perFrameRects']=[geometry.get((a['image'],i),{'rect':r})['rect'] for i,r in enumerate(old['perFrameRects'])]
        origins=copy.deepcopy(old['perFrameOrigins']);alpha=copy.deepcopy(old.get('alphaBounds',[]));phase_alpha=copy.deepcopy(old.get('perPhaseAlphaBounds',{}))
        for r in inv['frames']:
            for v in r['refs']:
                if v['action']!=key:continue
                g=geometry[(r['image'],r['index'])]
                if isinstance(origins,list):origins[r['index']]=g['origin']
                else:origins[v['direction']][v['phase']]=g['origin']
                if r['image']==a['image'] and r['index']<len(alpha):alpha[r['index']]=g['bounds']
                if v['direction'] in phase_alpha:phase_alpha[v['direction']][v['phase']]=g['bounds']
        a['perFrameOrigins']=origins;a['alphaBounds']=alpha
        if phase_alpha:a['perPhaseAlphaBounds']=phase_alpha
        a['sourcePNGs']=[str(candidate/n) for n in names];a['sourcePNGSHA256s']=[hashes[n] for n in names]
        a.pop('rawOutputPNGs',None);a.pop('rawOutputPNGSHA256s',None)
        a['originMethod']='Complete phase-owned semantic crops; original absolute support/flight anchors and world scale retained; no grid-cell assumptions.'
        a['appearanceAuthority']={'identity':'user image 2 / current standing four-direction head and body scale',
            'clothing':'user image 1 / original W01 sword attack dark clothing',
            'method':'two actual local-Qwen four-direction masked repairs plus bounded per-pose original-pixel identity/colour adaptation'}
        a['identityReferenceScope']='Standing head is canonical. Acting tilt/expression is retained for hit, roll and death. Same material palette across all equipped weapons and states.'
        a['localQwenProcessing']={'revision':REVISION,'report':str(HERE/'batch-report.json')}
        for field,value in old.items():
            if field not in mutable and a.get(field)!=value:raise RuntimeError(f'Unexpected action change: {key}/{field}')
    authority=HERE/'references/standing-identity-authority.png'
    if not authority.exists():
        board=Image.new('RGBA',(512,768))
        for i,d in enumerate(prepare.DIRECTIONS):board.paste(Image.open(HERE/'references'/f'identity-{d}.png').resize((256,384)),((i%2)*256,(i//2)*384))
        board.save(authority)
    authority_path=authority.relative_to(prepare.ROOT).as_posix();authority_sha=prepare.digest(authority)
    updated['identityReference']=authority_path;updated['identityReferenceSHA256']=authority_sha
    updated['identityReferenceScope']='User image 2/current standing four-direction appearance is authoritative; user image 1/current W01 attack is clothing authority.'
    for action in updated['actions'].values():action['identityReference']=authority_path;action['identityReferenceSHA256']=authority_sha
    updated['revision']='concept-image-2d-'+REVISION
    updated['localQwenInstall']={'revision':REVISION,'actions':len(updated['actions']),'frames':len(reports),'atlases':len(image_reports),
        'newModelInferences':2,'method':'four-direction standing cloth and attack neck samples; remaining phases use deterministic adaptations',
        'extraOriginalBackups':False,'report':str(HERE/'batch-report.json')}
    jsonwrite(candidate/'manifest.json',updated)
    fallback=[{'image':r['image'],'index':r['index'],'head':r['head']} for r in reports if r['head'].get('method')=='source pose retained: neck connectivity guard']
    summary=dict(status='prepared',revision=REVISION,actions=len(updated['actions']),frames=len(reports),atlases=len(image_reports),
        headRetargeted=sum(r['head'].get('applied',False) for r in reports),headConnectionFallbacks=fallback,
        extraOriginalBackups=False,invariants={'timingDirectionAndWorldScaleUnchanged':True,'absoluteSupportAndFlightAnchorsRetained':True,
        'noForeignProcessedPhaseAlpha16InCrops':True,'metaUnmodified':True},images=image_reports,phases=reports)
    jsonwrite(HERE/'batch-report.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('images','phases','headConnectionFallbacks')}|{'headConnectionFallbacks':len(fallback)}),flush=True)

def install():
    inv=json.loads((HERE/'inventory.json').read_text());report=json.loads((HERE/'batch-report.json').read_text());candidate=HERE/'candidate-runtime'
    if prepare.digest(prepare.MANIFEST)!=inv['manifestSHA256']:raise RuntimeError('Runtime manifest changed; inspect before installing')
    for row in inv['images']:
        if prepare.digest(prepare.ACTOR/row['image'])!=row['sha256']:raise RuntimeError('Runtime input changed: '+row['image'])
        if prepare.digest(str(prepare.ACTOR/row['image'])+'.meta')!=row['metaSHA256']:raise RuntimeError('Asset meta changed')
    for row in report['images']:
        if prepare.digest(candidate/row['image'])!=row['afterSHA256']:raise RuntimeError('Candidate changed')
    # Stage only new bytes. The user requested direct replacement, no originals.
    paths=[(prepare.ACTOR/r['image'],candidate/r['image']) for r in report['images']]+[(prepare.MANIFEST,candidate/'manifest.json')]
    for dest,src in paths:dest.with_name(dest.name+'.qwen-stage').write_bytes(src.read_bytes())
    for dest,src in paths:
        os.replace(dest.with_name(dest.name+'.qwen-stage'),dest)
        if prepare.digest(dest)!=prepare.digest(src):raise RuntimeError('Installed byte verification failed')
    for row in inv['images']:
        if prepare.digest(str(prepare.ACTOR/row['image'])+'.meta')!=row['metaSHA256']:raise RuntimeError('Meta changed during installation')
    report['status']='installed';report['manifestAfterSHA256']=prepare.digest(prepare.MANIFEST)
    jsonwrite(HERE/'batch-report.json',report)
    print(json.dumps({'status':'installed','actions':report['actions'],'frames':report['frames'],'atlases':report['atlases'],'extraOriginalBackups':False}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--install',action='store_true');parser.add_argument('--acting-only',action='store_true');parser.add_argument('--images',nargs='+');args=parser.parse_args()
    install() if args.install else prepare_batch(args.acting_only,args.images)
