"""Exact-image review boards: original v5 sheets plus actual runtime FBX views.

Only layout/scale is applied to placed images. Original concepts are never
written. Each board records the unchanged original SHA256 and current FBX hash.
"""
from pathlib import Path
import json,hashlib,textwrap,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'source-art/characters/cocos/previews/runtime'
FONT=Path('C:/Windows/Fonts');REG=FONT/'segoeui.ttf';BOLD=FONT/'segoeuib.ttf'
def font(size,bold=False):return ImageFont.truetype(str(BOLD if bold else REG),size)
def paragraph(draw,text,xy,width,size=29,color='#38413b',bold=False):
    f=font(size,bold);x,y=xy;words=text.split();line=''
    for word in words:
        trial=line+' '+word if line else word
        if draw.textlength(trial,font=f)>width:
            draw.text((x,y),line,font=f,fill=color);y+=size*1.48;line=word
        else:line=trial
    if line:draw.text((x,y),line,font=f,fill=color);y+=size*1.48
    return int(y)
def paste_fit(canvas,path,box,upscale=False):
    im=Image.open(path).convert('RGB')
    if upscale:
        factor=min(box[2]/im.width,box[3]/im.height);im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
    else:im.thumbnail((box[2],box[3]),Image.Resampling.LANCZOS)
    canvas.paste(im,(box[0]+(box[2]-im.width)//2,box[1]));return im.size
if '--mpfb' in sys.argv:
    before=OUT.parent/'mpfb-before';destination=OUT.parent/'mpfb-comparison';destination.mkdir(parents=True,exist_ok=True)
    records={}
    for identity in ['raphael','mira']:
        page=Image.new('RGB',(1500,1190),'#eeece5');draw=ImageDraw.Draw(page)
        draw.text((50,28),identity.title()+' / MPFB appearance pass',font=font(42,True),fill='#202b25')
        draw.text((50,92),'BEFORE — exported FBX',font=font(25,True),fill='#4f594f')
        draw.text((790,92),'AFTER — exported FBX',font=font(25,True),fill='#4f594f')
        first=before/f'{identity}-closeup.png';last=OUT/f'{identity}-closeup.png'
        paste_fit(page,first,(50,140,660,880),True);paste_fit(page,last,(790,140,660,880),True)
        paragraph(draw,'Same verifier camera and lighting. Actual runtime LoD assets; images are scaled only. Fitted CC0 hair cards, strand maps, subtle MPFB face targets and skin detail. Volume-lock style and costumes remain authored approximations.',(50,1040),1400,25)
        report=json.loads((ROOT/'src/cocos/assets/resources/actors'/identity/'inspection.json').read_text())
        record={'before':str(first.relative_to(ROOT)),'beforeSha256':hashlib.sha256(first.read_bytes()).hexdigest(),'after':str(last.relative_to(ROOT)),'afterSha256':hashlib.sha256(last.read_bytes()).hexdigest(),'afterFbxSha256':report['fbxSha256'],'imageContentEdited':False,'beforeEvidence':'Archived pre-pass runtime verifier render'}
        path=destination/f'{identity}-before-after.png';page.save(path,optimize=True);record['comparison']=str(path.relative_to(ROOT));records[identity]=record
    cast=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
    front=Image.open(OUT/'raphael-front.png').convert('RGB');w,h=front.size
    sheet=Image.new('RGB',(w*5,h*2),'#303030')
    for i,identity in enumerate(cast):sheet.paste(Image.open(OUT/f'{identity}-front.png').convert('RGB'),(i%5*w,i//5*h))
    sheet.save(OUT/'cast-front-contact-sheet.png',optimize=True)
    comparison=Image.new('RGB',(w*5,h*4+120),'#eeece5');drawing=ImageDraw.Draw(comparison)
    drawing.text((30,12),'BEFORE / actual runtime FBX',font=font(30,True),fill='#202b25')
    comparison.paste(Image.open(before/'cast-front-contact-sheet.png').convert('RGB'),(0,60))
    drawing.text((30,h*2+72),'AFTER / MPFB appearance pass / actual runtime FBX',font=font(30,True),fill='#202b25')
    comparison.paste(sheet,(0,h*2+120));comparison.save(destination/'cast-before-after.png',optimize=True)
    (destination/'comparison-record.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2));sys.exit(0)
records={}
for identity,reference,description,matches,gaps in [
 ('raphael','hero-v5-balanced.png','Original hero reference sheet, retained without edits.','Brown curls; dark teal short shoulder drape; one steel pauldron; brown leather over rolled off-white sleeves; star brooch and belt tools.','Facial likeness and expression are approximations. Hair locks remain sculptural rather than natural strands. Cloth drape, collar construction, leather engraving, skin and boot detail differ from v5.'),
 ('mira','explorers-v5-recast.png','Project Mira corresponds to the leftmost blonde character (Aida label) in this original sheet.','Closed blonde bob with broad waves; long burgundy split vest; off-white rolled sleeves; fitted belt and twin dagger equipment (hidden for the neutral comparison).','Hair parting, wave volume and strand detail differ from v5. Face likeness remains approximate. Vest construction, fabric folds, leather ornament and boots are simplified. The brass shoulder fastenings are a game-model adaptation.'),
]:
    ref=ROOT/'assets/concepts/revision-v5'/reference;ref_hash=hashlib.sha256(ref.read_bytes()).hexdigest()
    folder=ROOT/'src/cocos/assets/resources/actors'/identity;manifest=json.loads((folder/'manifest.json').read_text());inspection=json.loads((folder/'inspection.json').read_text())
    page=Image.new('RGB',(3200,2100),'#f2f0e9');draw=ImageDraw.Draw(page)
    draw.text((80,55),identity.title()+' — v5 design / exported Cocos FBX',font=font(58,True),fill='#202b25')
    paragraph(draw,'Original concept content is unchanged. Images are scaled only for this comparison layout; no generative edits or retouching.',(80,140),3040,29)
    draw.line((80,205,3120,205),fill='#b8bbae',width=2)
    draw.text((80,230),'V5 REFERENCE',font=font(31,True),fill='#5d675c')
    draw.text((1640,230),'RUNTIME LOD — FRONT / BACK / SIDE',font=font(31,True),fill='#5d675c')
    paste_fit(page,ref,(80,290,1460,1000));paste_fit(page,OUT/f'{identity}-turnaround.png',(1640,290,1480,760))
    y=paragraph(draw,description,(80,1310),1460,28)
    y+=20;draw.text((80,y),'Retained design cues',font=font(34,True),fill='#263b2d');y+=52
    y=paragraph(draw,matches,(80,y),1450,30)
    y+=22;draw.text((80,y),'Remaining visual differences',font=font(34,True),fill='#644b35');y+=52
    paragraph(draw,gaps,(80,y),1450,30)
    draw.text((1640,1000),'SAME FBX — FACE / GARMENT DETAIL',font=font(29,True),fill='#5d675c')
    paste_fit(page,OUT/f'{identity}-closeup.png',(1640,1050,630,840))
    y=1070;draw.text((2330,y),'Verified export',font=font(34,True),fill='#263b2d');y+=66
    facts=[f"53 named bones / 10 actual actions",f"{manifest['triangles']:,} runtime triangles",f"{manifest['lod']['skinMaxSize']} px game skin map",'Editable high-detail source retained','Clips and skin weights reimported in Blender','Original concept files unchanged','Visual parity with v5 is not claimed.']
    for fact in facts:y=paragraph(draw,fact,(2330,y),760,30)+24
    draw.line((80,1970,3120,1970),fill='#b8bbae',width=2)
    paragraph(draw,'Actual FBX SHA256: '+inspection['fbxSha256']+' | Reference SHA256: '+ref_hash,(80,2000),3040,23)
    path=OUT/f'{identity}-v5-runtime-comparison.png';page.save(path,optimize=True)
    assert hashlib.sha256(ref.read_bytes()).hexdigest()==ref_hash
    records[identity]={'comparison':str(path.relative_to(ROOT)),'reference':str(ref.relative_to(ROOT)),'referenceSha256':ref_hash,'fbxSha256':inspection['fbxSha256'],'referenceContentUnchanged':True}
(OUT/'comparison-record.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
