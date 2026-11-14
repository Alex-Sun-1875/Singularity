// Deterministic soft UI layers. No change to the accepted v16 frame artwork.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=__dirname,project=path.resolve(root,'../../..'),output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const sha=d=>crypto.createHash('sha256').update(d).digest('hex');
const write=(file,data)=>{fs.writeFileSync(file+'.v17tmp',data);fs.renameSync(file+'.v17tmp',file);};
const definitions=[
 {id:'skill-soft-shadow-v17',scale:1.6,description:'Neutral dark ambient/contact shadow; baked lower weighting. Place centered behind the skill face.',svg:`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><title>Skill medallion diffuse neutral contact shadow</title><defs><radialGradient id="shadow"><stop offset="0" stop-color="#070605" stop-opacity=".48"/><stop offset=".54" stop-color="#070605" stop-opacity=".48"/><stop offset=".64" stop-color="#070605" stop-opacity=".43"/><stop offset=".7" stop-color="#070605" stop-opacity=".32"/><stop offset=".78" stop-color="#070605" stop-opacity=".17"/><stop offset=".86" stop-color="#070605" stop-opacity=".07"/><stop offset=".94" stop-color="#070605" stop-opacity=".017"/><stop offset="1" stop-color="#070605" stop-opacity="0"/></radialGradient></defs><ellipse cx="256" cy="268" rx="238" ry="228" fill="url(#shadow)"/></svg>`},
 {id:'skill-soft-halo-v17',scale:1.36,description:'Restrained desaturated champagne-gray soft rim halo. Centered; 0.15 alpha peak near the face edge, with no solid line or face artwork.',svg:`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><title>Soft restrained champagne-gray skill perimeter haze</title><defs><radialGradient id="haze"><stop offset="0" stop-color="#B6B09D" stop-opacity="0"/><stop offset=".66" stop-color="#B6B09D" stop-opacity="0"/><stop offset=".72" stop-color="#B6B09D" stop-opacity=".035"/><stop offset=".77" stop-color="#C7BDA1" stop-opacity=".15"/><stop offset=".815" stop-color="#B6B09D" stop-opacity=".115"/><stop offset=".87" stop-color="#AAA998" stop-opacity=".052"/><stop offset=".935" stop-color="#AAA998" stop-opacity=".014"/><stop offset="1" stop-color="#AAA998" stop-opacity="0"/></radialGradient><filter id="soften" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.6"/></filter></defs><circle cx="256" cy="256" r="238" fill="url(#haze)" filter="url(#soften)"/></svg>`}
];
const records=[];
for(const d of definitions){const svg=d.svg+'\n',png=new Resvg(svg).render().asPng();write(path.join(root,d.id+'.svg'),svg);write(path.join(output,d.id+'.png'),png);records.push({id:d.id,source:'source-art/ui/clean-gold-v11/'+d.id+'.svg',sourceSHA256:sha(svg),asset:'src/cocos/assets/resources/ui/quiet-bronze/'+d.id+'.png',pngSHA256:sha(png),size:[512,512],bytes:png.length,displayDiameterRatio:d.scale,description:d.description});}
const previewCode=String.raw`
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import sys,json
root=Path(sys.argv[1]);project=Path(sys.argv[2]);assets=project/'src/cocos/assets/resources/ui/quiet-bronze';results=project/'src/cocos/test-results'
shadow=Image.open(assets/'skill-soft-shadow-v17.png').convert('RGBA');halo=Image.open(assets/'skill-soft-halo-v17.png').convert('RGBA');frame=Image.open(assets/'unified-gold-skill-v16.png').convert('RGBA')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
# Empty project-rendered world crops are used as material backgrounds only.
green=Image.open(results/'hud-skill-v16-outdoor.png').convert('RGBA').crop((1040,540,1440,900))
wood=Image.open(results/'hud-skill-v16-hidpi.png').convert('RGBA').crop((1080,480,1480,840))
out=Image.new('RGBA',(1080,1000),(22,17,13,255));draw=ImageDraw.Draw(out);draw.text((20,14),'v17 软阴影 + 克制柔光 · 58 / 86 技能框',font=font,fill=(210,185,133))
def composite(base,layer,cx,cy,d):
 layer=layer.resize((round(d),round(d)),Image.Resampling.LANCZOS);base.alpha_composite(layer,(round(cx-layer.width/2),round(cy-layer.height/2)))
for x,bg,label in [(20,green,'绿色地面'),(560,wood,'木地板')]:
 tile=bg.resize((500,300),Image.Resampling.LANCZOS);out.alpha_composite(tile,(x,50));draw.text((x+10,60),label,font=small,fill=(239,230,207))
 # Two actual logical diameters and one 2x enlarged 86-px sample.
 for cx,d in [(x+70,58),(x+190,86),(x+365,148)]:
  composite(out,shadow,cx,205,d*1.6);composite(out,halo,cx,205,d*1.36);composite(out,frame,cx,205,d)
# Concept preview: add effects outside the accepted actual faces, then protect
# those face pixels and keyboard/rank marks. Runtime review remains separate.
original=Image.open(results/'hud-skill-v16-outdoor.png').convert('RGBA').crop((1820,810,2556,1428))
fx=original.copy();mask=Image.new('L',original.size,0);md=ImageDraw.Draw(mask)
buttons=[(1209.12,637.12,85.76),(1100.32,637.12,58),(1113.376,552.256,58),(1209.12,521.792,58),(1022.24,541.376,58),(1026.08,637.12,52),(944.16,637.12,58)]
for x,y,d in buttons:
 cx=(x-910)*2;cy=(y-405)*2;dp=d*2
 composite(fx,shadow,cx,cy,dp*1.6);composite(fx,halo,cx,cy,dp*1.36)
 radius=dp*.495;md.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),fill=255)
 # Preserve known key/rank text around the top diagonal corners.
 for sign in [-1,1]:
  tx=cx+sign*dp*.31;ty=cy-dp*.32;md.rectangle((tx-18,ty-17,tx+18,ty+17),fill=255)
fx=Image.composite(original,fx,mask)
draw.text((20,374),'当前实景 · 调整前',font=font,fill=(210,185,133));draw.text((560,374),'阴影/柔光概念合成 · 运行时待验收',font=font,fill=(210,185,133))
out.alpha_composite(original.resize((500,420),Image.Resampling.LANCZOS),(20,412));out.alpha_composite(fx.resize((500,420),Image.Resampling.LANCZOS),(560,412))
# Visualize the two alpha-only layers on a simple neutral background.
for x,tex,label in [(20,shadow,'独立暗影 texture · 512透明'),(560,halo,'独立柔光 texture · 512透明')]:
 draw.text((x,855),label,font=small,fill=(210,185,133));comp=Image.new('RGBA',(160,110),(93,91,78,255));composite(comp,tex,80,55,130);out.alpha_composite(comp,(x+5,882))
out.convert('RGB').save(root/'isolated-preview-v17.png')
measure={}
for name,tex in [('shadow',shadow),('halo',halo)]:
 a=tex.getchannel('A');edges=[a.crop((0,0,512,1)),a.crop((0,511,512,512)),a.crop((0,0,1,512)),a.crop((511,0,512,512))]
 measure[name]={'maxAlpha':a.getextrema()[1],'edgeMaxAlpha':max(e.getextrema()[1] for e in edges),'alphaAtTopFaceEdge':a.getpixel((256,96 if name=='shadow' else 68)),'alphaAtBottomFaceEdge':a.getpixel((256,416 if name=='shadow' else 444))}
(root/'alpha-check-v17.json').write_text(json.dumps(measure,indent=2)+'\n',encoding='utf-8')
print(json.dumps(measure))
`;
const measure=JSON.parse(cp.execFileSync('python',['-c',previewCode,root,project],{encoding:'utf8'}).trim());
const provenance={version:'skill-soft-depth-v17',date:'2026-11-08',userDirection:'Add soft shadows or blurred halo layers around skill buttons, with Honor of Kings as visual inspiration.',ownership:'Project-original deterministic SVG radial gradients and Gaussian blur using existing Resvg and Pillow tooling. No new generation, downloads or dependencies.',reference:{acceptedFrame:'unified-gold-skill-v16',previewWorld:'Project runtime screenshots hud-skill-v16-outdoor.png and hud-skill-v16-hidpi.png',previewStatus:'Concept layering comparison only; actual game integration and artistic acceptance remain separate.',officialURL:'https://www.honorofkings.com/de/img/2.jpg',officialNecessaryCrop:'src/cocos/test-results/hok-official-skill-reference-v17.png',visualInterpretation:'Diffuse dark terrain separation with restrained perimeter haze; official artwork is reference-only and is not included in the new textures.'},construction:'Two reusable transparent sprite layers behind each accepted v16 face: broad dark ambient/contact shadow plus subtle neutral-champagne perimeter haze. Soft alpha fades avoid hard circles or panels.',assets:records,sampling:'Use linear/trilinear mipmaps and non-atlased SpriteFrame for clean low-alpha scaling.',layerOrder:['shadow','halo','accepted v16 face','icon and labels'],alphaValidation:measure,artReview:{isolated:'Parent reviewed isolated-preview-v17.png and approved the first-pass strength for runtime integration without brightening. Geometry and alpha frozen.',runtime:'Not integrated by this asset task.',userAcceptance:'Not recorded.'}};
write(path.join(root,'provenance-v17.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify({assets:records.map(({id,bytes,displayDiameterRatio})=>({id,bytes,displayDiameterRatio})),alphaValidation:measure}));
