"""Read-only local pixel audit. Writes only to this hand-audit directory."""
from pathlib import Path
import ast
import hashlib
import json

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
STAGES = ('before', 'guide', 'raw-model', 'constrained-candidate')
CASES = ('sword-back', 'clothing-side', 'run-front', 'run-back')
# These are conservative repair envelopes, not a claim that every warm pixel is skin.
# XY endpoints are half-open; margin covers finger tips, wrists and anti-aliasing.
REGIONS = {
    'sword-back': {
        'screen-left': {'box': [142, 364, 204, 453], 'original_box': [142, 364, 192, 443],
                        'search': [140, 360, 200, 448],
                        'risk': 'The new scabbard crosses this envelope. Its warm leather passes a skin gate. A rectangular before paste here can remove the intended longer scabbard or its tip. Preserve the hand/arm occlusion; do not treat the entire envelope as an unconditional restore rectangle.'},
        'screen-right': {'box': [317, 362, 370, 443], 'original_box': [317, 362, 370, 443],
                         'search': [319, 360, 369, 443],
                         'risk': 'No final hand change detected in the original flesh component; keep as an explicit final-stage guard.'},
    },
    'clothing-side': {
        'screen-left': {'box': [181, 304, 256, 402], 'original_box': [184, 312, 256, 402],
                        'search': [190, 312, 252, 390],
                        'risk': 'The existing exclusion ellipse (170,302,215,351) misses the palm and fingers at x200..244,y326..381. Warm leather at the lower edge can pass a skin gate. Full patch restoration restores some cuff/nearby cloth as intended context.'},
        'screen-right': {'box': [349, 239, 415, 320], 'original_box': [349, 239, 415, 320],
                         'search': [350, 239, 413, 320],
                         'risk': 'The other exclusion ellipse (320,226,376,273) does not span the complete hand. Existing final hand is largely unchanged because the garment palette mask is spatially distant.'},
    },
    'run-front': {
        'screen-left': {'box': [190, 266, 276, 351], 'original_box': [190, 278, 276, 351],
                        'search': [195, 265, 274, 348],
                        'risk': 'Original palm extends to x263, beyond the old protection polygon near x229..237. Guide compresses the hand from y290..339 into y278..319; the final combines both positions. Restore the full union after all palette operations, including background and cuff pixels.'},
        'screen-right': {'box': [331, 332, 388, 432], 'original_box': [331, 356, 388, 432],
                         'search': [333, 330, 388, 434],
                         'risk': 'Geometric protection restores this original hand, but palette_lock runs later and changes its RGB. Include the guide/raw hand at y344..387 to erase any shifted contour if blending logic changes.'},
    },
    'run-back': {
        'screen-left': {'box': [129, 323, 188, 415], 'original_box': [129, 346, 188, 415],
                        'search': [131, 275, 202, 416],
                        'risk': 'Original hand y358..403 shifts to y335..373 in the guide. The raw model proposes another hand-like component at x157..190,y285..317, but it is excluded in the current final, so it is diagnostic only and intentionally outside this union erase box.'},
        'screen-right': {'box': [208, 240, 280, 356], 'original_box': [208, 247, 280, 356],
                         'search': [216, 230, 287, 345],
                         'risk': 'Shaded raised hand overlaps warm straps and cuff material: colour alone cannot define a semantic hand contour. Original bright component x228..260,y263..330; guide y255..312. Current final retains guide displacement. This erase box uses before+guide+current only; unrelated raw warm components above it are diagnostic only.'},
    },
}

# Primary flesh components, selected in the local hand windows. Sword standing
# hands and extended fingers use the broad gate; shaded material-connected hands
# use the brighter primary component. These are evidence cores, not full mattes.
CORE_BOXES = {
    'sword-back': {'screen-left': [152,374,181,431], 'screen-right': [329,374,358,431]},
    'clothing-side': {'screen-left': [195,326,244,381], 'screen-right': [359,251,403,308]},
    'run-front': {'screen-left': [202,290,263,339], 'screen-right': [343,368,375,420]},
    'run-back': {'screen-left': [141,358,176,403], 'screen-right': [228,263,260,330]},
}
GUIDE_CORE_BOXES = {
    'sword-back': {'screen-left': [152,374,179,428], 'screen-right': [329,374,358,431]},
    'clothing-side': {'screen-left': [195,326,244,381], 'screen-right': [359,251,403,308]},
    'run-front': {'screen-left': [202,278,263,319], 'screen-right': [343,344,375,388]},
    'run-back': {'screen-left': [141,335,176,373], 'screen-right': [228,255,260,312]},
}


def bounds(mask):
    yy, xx = np.nonzero(mask)
    if not len(xx):
        return None
    return [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]


def rectangular_mask(box):
    mask = np.zeros((768, 512), bool)
    x0, y0, x1, y1 = box
    mask[y0:y1, x0:x1] = True
    return mask


def skin_gate(image, bright=False):
    # Grey is excluded by channel differences/chroma. Yellow/gold is reduced by
    # low hue and G-B/R-G ratio. Leather still overlaps: explicit local windows
    # and component size are essential, and all ambiguous components are reported.
    arr = np.asarray(image).astype(np.float32)
    hsv = np.asarray(image.convert('HSV')).astype(np.float32)
    r, g, b = np.moveaxis(arr, -1, 0)
    yy = np.indices(r.shape)[0]
    if bright:
        gate = ((r>145)&(g>95)&(b>80)&(r>g+12)&(g>b+5)&
                ((r-g)<65)&((g-b)<(r-g)*.75)&(hsv[:,:,0]<19)&
                (hsv[:,:,1]>35)&(hsv[:,:,1]<145))
    else:
        gate = ((r>85)&(g>55)&(b>40)&(r>g+7)&(g>b+5)&
                ((r-g)<65)&((g-b)<(r-g)*1.2)&(hsv[:,:,0]<25)&
                (hsv[:,:,1]>25)&(hsv[:,:,1]<150))
    return gate & (yy>=230) & (yy<470)


def components(mask, image, minimum=12):
    labels, _ = ndi.label(mask, np.ones((3, 3), bool))
    arr = np.asarray(image)
    found = []
    for label_id, slc in enumerate(ndi.find_objects(labels), 1):
        if slc is None:
            continue
        local = labels[slc] == label_id
        count = int(local.sum())
        if count < minimum:
            continue
        found.append({'pixels': count,
                      'box': [slc[1].start,slc[0].start,slc[1].stop,slc[0].stop],
                      'median_rgb': np.median(arr[slc][local],axis=0).tolist()})
    return sorted(found, key=lambda entry: entry['pixels'], reverse=True)


def changed(a, b):
    return np.any(np.asarray(a) != np.asarray(b), axis=2)


def metrics(a, b, roi=None):
    delta = np.abs(np.asarray(a).astype(np.int16)-np.asarray(b).astype(np.int16))
    mask = np.any(delta != 0,axis=2)
    if roi is not None:
        mask &= roi
    return {'changed_pixels': int(mask.sum()), 'changed_box': bounds(mask),
            'changed_over_8_rgb_levels': int((mask & (delta.max(axis=2)>8)).sum()),
            'max_absolute_rgb_delta': int(delta[mask].max()) if mask.any() else 0}


def load_functions():
    source_path = ROOT / 'finalize-candidates.py'
    tree = ast.parse(source_path.read_text(encoding='utf-8'))
    # Execute only function definitions: importing the existing script would
    # overwrite old candidates and reports, so never import it.
    functions = ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)],type_ignores=[])
    srgb, lab = ImageCms.createProfile('sRGB'), ImageCms.createProfile('LAB')
    ns = {'np':np, 'Image':Image, 'ImageCms':ImageCms, 'ImageFilter':ImageFilter,
          'TO_LAB':ImageCms.buildTransformFromOpenProfiles(srgb,lab,'RGB','LAB'),
          'TO_RGB':ImageCms.buildTransformFromOpenProfiles(lab,srgb,'LAB','RGB')}
    exec(compile(functions,str(source_path),'exec'),ns)
    return ns


def reproduce_intermediate(case, images, ns):
    before, guide, raw = (images[key] for key in ('before','guide','raw-model'))
    shape = before.size
    protect = Image.new('L', shape, 0)
    mask = Image.open(ROOT/'guides'/case/'composite-mask.png').convert('L')
    if case == 'sword-back':
        oldmask = Image.new('L', shape, 0)
        ImageDraw.Draw(oldmask).line([(283,192),(200,373)],fill=255,width=5)
        newmask = Image.new('L', shape, 0)
        ImageDraw.Draw(newmask).line([(283,192),(166.8,445.4)],fill=255,width=13)
        rows = np.indices((768,512))[0]
        old_samples = (np.asarray(oldmask)>128)&(rows>220)
        new_samples = (np.asarray(newmask)>128)&(rows>220)
        delta = np.median(ns['lab'](before)[old_samples],axis=0)-np.median(ns['lab'](raw)[new_samples],axis=0)
        corrected = ns['rgb'](ns['lab'](raw)+delta)
        newmask = newmask.filter(ImageFilter.GaussianBlur(.7))
        guard = np.array(newmask);guard[:210]=0;newmask=Image.fromarray(guard)
        final = Image.composite(corrected,guide,newmask)
        final.paste(before.crop((0,0,512,210)),(0,0))
        return guide, final, protect, newmask, []
    if case == 'clothing-side':
        base = before.copy();region=np.asarray(mask)>100
        active = Image.fromarray(np.uint8(region)*255)
    else:
        d=ImageDraw.Draw(protect)
        if case == 'run-front':
            d.polygon([(0,195),(229,195),(237,330),(209,364),(0,364)],fill=255)
            d.polygon([(309,195),(512,195),(512,443),(322,443),(310,387)],fill=255)
        else:
            d.polygon([(0,195),(217,195),(214,448),(0,448)],fill=255)
            d.polygon([(302,195),(512,195),(512,385),(321,385),(301,300)],fill=255)
        d.rectangle((0,650,511,767),fill=255)
        base=Image.composite(before,guide,protect)
        legmask=np.array(mask);legmask[:380]=0;legmask[650:]=0
        legmask[np.asarray(protect)>0]=0
        active=Image.fromarray(legmask).filter(ImageFilter.GaussianBlur(2))
        base=Image.composite(raw,base,active)
        base=Image.composite(before,base,protect)
        region=np.asarray(Image.open(ROOT/'guides'/case/'noise-mask.png'))>100
        rows=np.indices((768,512))[0];region&=(rows>=210)&(rows<420)
    ref=Image.open(ROOT/'guides'/case/'reference.png').convert('RGB')
    final, details=ns['palette_lock'](base,raw,ref,region)
    final.paste(before.crop((0,0,512,200)),(0,0))
    if case.startswith('run-'):
        final.paste(before.crop((0,650,512,768)),(0,650))
    return base, final, protect, active, details


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ns=load_functions()
    report={'status':'local pixel audit only; no visual acceptance, model invocation or source edits',
            'coordinate_system':'512x768 pixel XY, half-open right/bottom endpoints',
            'skin_detection':'8-connected RGB/HSV gates in y230..469, gold/gray reduced; local windows disambiguate hands from warm leather. Gates are evidence, not final compositing masks.',
            'restore_order':'Complete all guide/model compositing and all colour/palette conversions first. Finally copy approved before pixels across the before+guide+current hand union envelope, including fingers, wrist, antialiasing and vacated contour. Uncomposited raw-only displacements are diagnostics, not current erase regions. Assert equality to before in the final protection mask. Sword-left needs an original-alpha occlusion-aware matte, preserving gaps and the intended scabbard.',
            'inputs_sha256':{'finalize-candidates.py':sha256(ROOT/'finalize-candidates.py'),
                             'prepare-cases.py':sha256(ROOT/'prepare-cases.py')},
            'cases':{}}
    sheet=Image.new('RGB',(704,1158),(242,242,242))
    draw=ImageDraw.Draw(sheet)
    try:
        font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',12)
        small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',10)
    except OSError:
        font=small=ImageFont.load_default()
    draw.text((8,4),'Local hand audit | yellow = exact changed pixels; cyan = bright warm components',font=font,fill=(25,25,25))
    for column,stage in enumerate(STAGES):
        draw.text((column*176+8,25),stage,font=font,fill=(30,30,30))
    row=0
    for case in CASES:
        paths={stage: ROOT/('guides' if stage in ('before','guide') else 'results')/case/(stage+'.png') for stage in STAGES}
        images={stage:Image.open(path).convert('RGB') for stage,path in paths.items()}
        before=images['before'];current=images['constrained-candidate']
        base,reproduction,protect,active,palette_details=reproduce_intermediate(case,images,ns)
        assert np.array_equal(np.asarray(reproduction),np.asarray(current)),case+' reproduction differs'
        current_delta=changed(before,current)
        broad={stage:skin_gate(image) for stage,image in images.items()}
        bright={stage:skin_gate(image,bright=True) for stage,image in images.items()}
        case_report={'reproduction_exact':True,
                     'file_sha256':{stage:sha256(path) for stage,path in paths.items()},
                     'all_changes_from_before':{},
                     'band_changes_from_before':{},
                     'full_band_warm_components':{stage:components(mask,images[stage],40) for stage,mask in broad.items()},
                     'palette_details':palette_details,
                     'palette_changes_after_geometric_protection':metrics(base,current,np.asarray(protect)>0) if case!='sword-back' else None,
                     'no_palette_branch':case=='sword-back',
                     'hands':{}}
        band=rectangular_mask([0,230,512,470])
        for stage in STAGES[1:]:
            mask=changed(before,images[stage])
            case_report['all_changes_from_before'][stage]=metrics(before,images[stage])
            case_report['band_changes_from_before'][stage]=metrics(before,images[stage],band)
            Image.fromarray(np.uint8(mask)*255).save(OUT/(case+'-before-vs-'+stage+'-all-changes.png'))
        for hand, config in REGIONS[case].items():
            roi=rectangular_mask(config['box'])
            search=rectangular_mask(config['search'])
            entry=dict(config)
            entry['original_skin_core_box']=CORE_BOXES[case][hand]
            entry['guide_primary_skin_core_box']=GUIDE_CORE_BOXES[case][hand]
            entry['union_erase_box']=config['box']
            entry['union_erase_sources']=['before','guide','constrained-candidate']
            entry['source_protection_box']=config['original_box']
            entry['bright_components']={stage:components(bright[stage]&search,images[stage],40) for stage in STAGES}
            entry['all_roi_changes_from_before']={stage:metrics(before,images[stage],roi) for stage in STAGES[1:]}
            entry['original_warm_skin_pixels']=int((broad['before']&roi).sum())
            entry['original_warm_skin_changed_in_current']=int((broad['before']&roi&current_delta).sum())
            entry['original_warm_skin_unprotected']=int((broad['before']&roi&(~(np.asarray(protect)>0))).sum())
            entry['original_warm_skin_palette_changed']=int((broad['before']&roi&changed(base,current)).sum()) if case!='sword-back' else 0
            entry['original_bright_core_changed']=metrics(before,current,bright['before']&rectangular_mask(CORE_BOXES[case][hand]))
            entry['post_geometry_changes_in_roi']=metrics(base,current,roi)
            if case!='sword-back':
                material_masks=ns['palette_masks'](base,np.ones((768,512),bool))
                entry['original_bright_core_selected_as_garment']={label:int((material_mask&bright['before']&rectangular_mask(CORE_BOXES[case][hand])).sum()) for label,material_mask in zip(('wine','dark-sleeve'),material_masks)}
            entry['active_composite_pixels']=int((roi&(np.asarray(active)>0)).sum())
            entry['palette_changes_in_roi']=metrics(base,current,roi) if case!='sword-back' else None
            # This is only a report/contact sheet, never a candidate image.
            x0,y0,x1,y1=config['box']
            width,height=x1-x0,y1-y0
            side=max(width,height)+8
            cx,cy=(x0+x1)/2,(y0+y1)/2
            crop=(int(cx-side/2),int(cy-side/2),int(cx-side/2)+side,int(cy-side/2)+side)
            for col,stage in enumerate(STAGES):
                array=np.asarray(images[stage]).copy()
                ed=bright[stage]&~ndi.binary_erosion(bright[stage])&roi
                array[ed]=(30,205,220)
                if stage!='before':
                    dif=changed(before,images[stage])&roi
                    # Sparse visible exact-change overlay preserves enough local detail.
                    yy,xx=np.indices(dif.shape)
                    sparse=dif&(((xx+yy)%5)==0)
                    array[sparse]=(255,220,0)
                tile=Image.fromarray(array).crop(crop).resize((126,126),Image.Resampling.NEAREST)
                tx,ty=col*176+8,46+row*138
                sheet.paste(tile,(tx,ty))
                draw.rectangle((tx,ty,tx+125,ty+125),outline=(155,40,50),width=1)
                draw.text((tx,ty+126),case+'/'+hand,font=small,fill=(25,25,25))
                if col==3:
                    draw.text((tx+128,ty+3),f'x{x0}\ny{y0}\nx{x1}\ny{y1}',font=small,fill=(90,30,30))
            case_report['hands'][hand]=entry
            row+=1
        report['cases'][case]=case_report
    (OUT/'hand-regions.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    sheet.save(OUT/'hand-contactsheet.jpg',quality=89,optimize=True)
    compact={case:{'all_changed':data['all_changes_from_before']['constrained-candidate'],
                   'palette_changes_in_protected_pixels':data['palette_changes_after_geometric_protection'],
                   'hands':{hand:{key:entry[key] for key in ('box','original_box','original_warm_skin_pixels','original_warm_skin_changed_in_current','original_warm_skin_palette_changed')} for hand,entry in data['hands'].items()}}
             for case,data in report['cases'].items()}
    print(json.dumps(compact,indent=2))


if __name__=='__main__':
    main()
