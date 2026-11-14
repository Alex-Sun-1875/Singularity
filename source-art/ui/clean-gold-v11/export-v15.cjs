const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const palette={metal:'#B99456',light:'#D2B985',ornament:'#C29B5A',glint:'#D9CCA2',low:'#AB853B',mid:'#BE995A',shadow:'#1D170C'};
const defs=`<linearGradient id="gold-metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${palette.low}"/><stop offset=".16" stop-color="${palette.metal}"/><stop offset=".29" stop-color="${palette.light}"/><stop offset=".44" stop-color="${palette.mid}"/><stop offset=".62" stop-color="${palette.metal}"/><stop offset=".79" stop-color="${palette.light}"/><stop offset="1" stop-color="${palette.low}"/></linearGradient>
<linearGradient id="gold-highlight" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${palette.glint}"/><stop offset=".26" stop-color="${palette.light}"/><stop offset=".58" stop-color="${palette.ornament}"/><stop offset=".86" stop-color="${palette.light}"/><stop offset="1" stop-color="${palette.mid}"/></linearGradient>
<linearGradient id="dark-inset" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#211910"/><stop offset=".4" stop-color="#19130E"/><stop offset="1" stop-color="#100D09"/></linearGradient>`;
const number=n=>Number(n.toFixed(3));
function motif(angle,{map=false,secondary=false}={}){
 const tan=map?.79:1,radial=map?.46:1,offset=map?6:0;
 const pt=(t,inset)=>{const a=angle+t*tan/228,d=250.5-(inset*radial+offset);return `${number(256+Math.cos(a)*d)} ${number(256+Math.sin(a)*d)}`;};
 const path=commands=>commands.map(c=>c[0]==='Z'?'Z':c[0]+Array.from({length:(c.length-1)/2},(_,i)=>pt(c[i*2+1],c[i*2+2])).join(' ')).join(' ');
 const line=d=>`<path d="${d}" stroke="${palette.shadow}" stroke-opacity=".84" stroke-width="${map?4.2:5.3}"/><path d="${d}" transform="translate(-.9 -.9)" stroke="${palette.light}" stroke-opacity=".91" stroke-width="${map?1.6:2.1}"/>`;
 const leaf=d=>`<path d="${d}" fill="${palette.ornament}" stroke="${palette.shadow}" stroke-opacity=".86" stroke-width="${map?3.4:4.2}"/><path d="${d}" fill="none" transform="translate(-1 -.9)" stroke="${palette.light}" stroke-opacity=".72" stroke-width="${map?1.3:1.7}"/>`;
 let body='';
 if(!secondary){
  // One continuous S-vine, twin coiled tendrils and outer acanthus leaves.
  body+=line(path([['M',-83,24],['C',-49,12,-23,37,0,29],['C',23,21,49,43,83,24]]));
  for(const side of [-1,1]){
   const c=arr=>arr.map((n,i)=>i%2===1?n*side:n);
   const mirrored=commands=>commands.map(cmd=>[cmd[0],...cmd.slice(1).map((n,i)=>i%2===0?n*side:n)]);
   body+=line(path(mirrored([['M',7,29],['C',21,14,47,10,64,21],['C',84,35,48,45,34,31],['C',23,18,56,16,57,29],['C',57,36,43,35,46,28]])));
   body+=leaf(path(mirrored([['M',58,20],['C',64,9,79,10,86,13],['C',80,23,70,27,58,20],['Z']])));
   body+=leaf(path(mirrored([['M',23,33],['C',35,32,41,42,47,44],['C',31,48,22,44,23,33],['Z']])));
   body+=line(path(mirrored([['M',62,20],['C',70,16,76,15,82,14]])));
  }
  // The central three-petal crest repeats the rectangular panel's curled crowns.
  body+=leaf(path([['M',0,13],['C',-10,22,-8,33,0,41],['C',8,33,10,22,0,13],['Z']]));
  for(const side of [-1,1])body+=leaf(path([['M',0,31],['C',side*18,34,side*20,20,side*12,18],['C',side*9,25,side*6,29,0,31],['Z']]));
 }else{
  body+=line(path([['M',-36,27],['C',-21,15,-8,17,0,27],['C',8,37,21,39,36,27]]));
  for(const side of [-1,1]){
   body+=leaf(path([['M',side*3,27],['C',side*13,14,side*28,13,side*35,17],['C',side*31,29,side*15,34,side*3,27],['Z']]));
   body+=leaf(path([['M',side*8,30],['C',side*16,34,side*20,41,side*21,44],['C',side*8,45,side*3,39,side*8,30],['Z']]));
   body+=line(path([['M',side*8,27],['C',side*19,23,side*25,21,side*31,19]]));
  }
 }
 return `<g stroke-linecap="round" stroke-linejoin="round" fill="none">${body}</g>`;
}
function surround(kind){
 const map=kind==='ring',inner=map?216.5:195;
 const main=map?`<circle cx="256" cy="256" r="236" stroke="url(#gold-metal)" stroke-width="29"/>`:`<circle cx="256" cy="256" r="224.5" stroke="url(#gold-metal)" stroke-width="52"/>`;
 let body=map?'':`<circle cx="256" cy="256" r="250.5" fill="url(#dark-inset)"/>`;
 body+=`<circle cx="256" cy="256" r="250.5" stroke="#070501" stroke-width="5"/>${main}
<circle cx="256" cy="256" r="249.6" stroke="url(#gold-highlight)" stroke-width="2.2"/>
<circle cx="256" cy="256" r="244.9" stroke="${palette.shadow}" stroke-opacity=".85" stroke-width="3.8"/>
<circle cx="256" cy="256" r="242.8" stroke="${palette.light}" stroke-opacity=".76" stroke-width="1.6"/>`;
 if(map){
  for(let i=0;i<8;i++)body+=motif(Math.PI/8+i*Math.PI/4,{map:true});
 }else{
  for(let i=0;i<4;i++)body+=motif(i*Math.PI/2);
  for(let i=0;i<4;i++)body+=motif(Math.PI/4+i*Math.PI/2,{secondary:true});
 }
 body+=`<circle cx="256" cy="256" r="${inner+5.6}" stroke="${palette.shadow}" stroke-width="3.8"/>
<circle cx="256" cy="256" r="${inner+3.4}" stroke="url(#gold-highlight)" stroke-width="2.1"/>
<circle cx="256" cy="256" r="${inner+.9}" stroke="#0A0704" stroke-opacity=".95" stroke-width="2.1"/>`;
 return `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" fill="none"><title>Wide clean-gold ${kind} surround with eight embossed acanthus scroll settings</title><defs>${defs}</defs>${body}</svg>\n`;
}
const sha=data=>crypto.createHash('sha256').update(data).digest('hex'),records=[];
for(const kind of ['skill','ring']){
 const id='unified-gold-'+kind+'-v15',svg=surround(kind),png=new Resvg(svg).render().asPng();
 fs.writeFileSync(path.join(root,id+'.svg'),svg);fs.writeFileSync(path.join(output,id+'.png'),png);
 records.push({id,source:'source-art/ui/clean-gold-v11/'+id+'.svg',sourceSHA256:sha(svg),asset:'src/cocos/assets/resources/ui/quiet-bronze/'+id+'.png',pngSHA256:sha(png),bytes:png.length,size:[512,512],innerApertureRadius:kind==='skill'?195:216.5,outerRadius:250.5,geometry:'Outer silhouette retained; wider band grows inward.',engraving:kind==='skill'?'Four cardinal large twin-scroll crowns with acanthus leaves; four diagonal leaf settings.':'Eight twin-scroll crowns centered at22.5°+45°n, leaving compass axes clear.'});
}
const raster=(kind,x,y,d)=>{const svg=fs.readFileSync(path.join(root,'unified-gold-'+kind+'-v15.svg'),'utf8'),png=new Resvg(svg,{fitTo:{mode:'width',value:d}}).render().asPng();return `<image href="data:image/png;base64,${png.toString('base64')}" x="${x}" y="${y}" width="${d}" height="${d}"/>`;};
const preview=`<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="430" viewBox="0 0 1040 430"><rect width="1040" height="430" fill="#16110D"/><g font-family="sans-serif" font-size="20" fill="${palette.light}"><text x="26" y="35">v15 - wider skill bezels: 58 / 64 / 86 / 160px</text><text x="610" y="35">240px compass</text></g>${raster('skill',30,90,58)}${raster('skill',115,88,64)}${raster('skill',205,77,86)}${raster('skill',330,45,160)}${raster('ring',610,60,240)}${raster('skill',36,225,170)}${raster('ring',295,225,170)}<g font-family="sans-serif" font-size="16" fill="${palette.light}"><text x="26" y="420">Shared gold: wide rim, chased scrolls, closed leaves and restrained relief.</text></g></svg>`;
fs.writeFileSync(path.join(root,'isolated-preview-v15.svg'),preview);fs.writeFileSync(path.join(root,'isolated-preview-v15.png'),new Resvg(preview).render().asPng());
const provenance={version:'unified-gold-v15',date:'2026-11-08',userDirection:'Further widen the skill frames and upper-right minimap surround, with richer matched ornamental patterns.',ownership:'Project-original deterministic SVG refinement of existing v13/v14 gold family. No generation or external download.',palette,construction:'Broad layered metal band; recessed grooves, narrow raised inner/outer lips; embossed acanthus leaves and twin scrolls baked once into the shared SVG texture. Native ornament must not be overlaid for these v15 assets.',geometry:{skill:{outerRadius:250.5,innerApertureRadius:195,visibleRadialBand:55.5,approximateAt58:6.29,approximateAt64:6.94,approximateAt86:9.32},ring:{outerRadius:250.5,innerApertureRadius:216.5,visibleRadialBand:34,approximateAt240:15.94}},sampling:'Parent integration should use non-atlased trilinear mipmapped texture, as v14, to preserve shaded relief at small native control sizes.',exporter:'@resvg/resvg-js@2.6.2 (MPL-2.0), existing project dependency',assets:records,artReview:{isolated:'Generated direct-vector actual-size preview; pending inspection.',runtime:'Pending parent integration and desktop/mobile review.',userAcceptance:'Not recorded.'}};
fs.writeFileSync(path.join(root,'provenance-v15.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify(records.map(({id,bytes,innerApertureRadius})=>({id,bytes,innerApertureRadius}))));
