// Project-original refined skill bezel. Native UiChrome owns the floral engraving.
// Reuses the installed Resvg exporter and the v13 subdued gold palette.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const palette={metal:'#B99456',light:'#D2B985',ornament:'#C29B5A',glint:'#D9CCA2',low:'#AB853B',mid:'#BE995A',shadow:'#1D170C'};
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" fill="none">
 <title>Refined clean-gold skill bezel; thicker metal, recessed channels and fine raised lips</title>
 <defs>
  <linearGradient id="gold-metal" x1="0" y1="0" x2="1" y2="1">
   <stop stop-color="${palette.low}"/><stop offset=".16" stop-color="${palette.metal}"/>
   <stop offset=".29" stop-color="${palette.light}"/><stop offset=".44" stop-color="${palette.mid}"/>
   <stop offset=".62" stop-color="${palette.metal}"/><stop offset=".79" stop-color="${palette.light}"/>
   <stop offset="1" stop-color="${palette.low}"/>
  </linearGradient>
  <linearGradient id="gold-highlight" x1="0" y1="0" x2="1" y2="1">
   <stop stop-color="${palette.glint}"/><stop offset=".26" stop-color="${palette.light}"/>
   <stop offset=".58" stop-color="${palette.ornament}"/><stop offset=".86" stop-color="${palette.light}"/>
   <stop offset="1" stop-color="${palette.mid}"/>
  </linearGradient>
  <linearGradient id="dark-inset" x1="0" y1="0" x2="0" y2="1">
   <stop stop-color="#211910"/><stop offset=".4" stop-color="#19130E"/><stop offset="1" stop-color="#100D09"/>
  </linearGradient>
 </defs>
 <circle cx="256" cy="256" r="250.5" fill="url(#dark-inset)"/>
 <!-- Same outer silhouette as v13; the additional metal grows inward. -->
 <circle cx="256" cy="256" r="250.5" stroke="#070501" stroke-opacity=".94" stroke-width="5"/>
 <circle cx="256" cy="256" r="237" stroke="url(#gold-metal)" stroke-width="27"/>
 <circle cx="256" cy="256" r="249.6" stroke="url(#gold-highlight)" stroke-width="1.55"/>
 <!-- Two shallow chased channels keep the wider band from reading as flat paint. -->
 <circle cx="256" cy="256" r="246.3" stroke="${palette.shadow}" stroke-opacity=".74" stroke-width="1.35"/>
 <circle cx="256" cy="256" r="244.9" stroke="${palette.light}" stroke-opacity=".68" stroke-width=".8"/>
 <circle cx="256" cy="256" r="227" stroke="${palette.shadow}" stroke-opacity=".66" stroke-width="1.35"/>
 <circle cx="256" cy="256" r="225.4" stroke="url(#gold-highlight)" stroke-opacity=".73" stroke-width="1.25"/>
 <!-- Recessed inner seam and narrow return lip create the inset face. -->
 <circle cx="256" cy="256" r="222.8" stroke="#100C05" stroke-width="2.3"/>
 <circle cx="256" cy="256" r="219.8" stroke="${palette.ornament}" stroke-width="1.6"/>
 <circle cx="256" cy="256" r="217.7" stroke="#0A0704" stroke-opacity=".9" stroke-width="1.25"/>
 <path d="M82.95 80.66A246.35 246.35 0 0 1 422.5 74.46" stroke="${palette.glint}" stroke-opacity=".42" stroke-width="1.1"/>
</svg>`;
const id='unified-gold-skill-v14',svgPath=path.join(root,id+'.svg'),pngPath=path.join(output,id+'.png');
fs.writeFileSync(svgPath,svg+'\n');
const png=new Resvg(svg).render().asPng();fs.writeFileSync(pngPath,png);
const dataURL=buffer=>'data:image/png;base64,'+buffer.toString('base64');
const old=fs.readFileSync(path.join(root,'unified-gold-skill-v13.svg'),'utf8');
// Rasterize each vector at its actual display size rather than resampling a
// 512 px embedded bitmap; Resvg's nested-image scaling is not the game filter.
const img=(source,x,y,d)=>{const buffer=new Resvg(source,{fitTo:{mode:'width',value:d}}).render().asPng();return `<image href="${dataURL(buffer)}" x="${x}" y="${y}" width="${d}" height="${d}"/>`;};
const preview=`<svg xmlns="http://www.w3.org/2000/svg" width="600" height="270" viewBox="0 0 600 270">
 <rect width="600" height="270" fill="#16110D"/>
 <g font-family="sans-serif" font-size="15" fill="${palette.light}"><text x="22" y="27">v13</text><text x="318" y="27">v14 — wider layered metal</text><text x="22" y="244">120 px / 64 px</text><text x="318" y="244">120 px / 64 px</text></g>
 ${img(old,22,62,120)}${img(old,190,90,64)}${img(svg,318,62,120)}${img(svg,486,90,64)}
</svg>`;
fs.writeFileSync(path.join(root,'isolated-preview-v14.svg'),preview);
fs.writeFileSync(path.join(root,'isolated-preview-v14.png'),new Resvg(preview).render().asPng());
const provenance={version:'unified-gold-skill-v14',date:'2026-11-08',userDirection:'Thicken the small circular skill frames and refine their construction and decoration while retaining the current gold brightness.',ownership:'Project-original deterministic SVG refinement of unified-gold-skill-v13. No generation or external downloads.',palette,geometry:{outerRadius:250.5,previousMetalBand:16.5,metalBand:27,totalVisibleBezel:33.425,diameterUnchanged:true,approximateBezelAt58:3.786,approximateBezelAt64:4.178,approximateBezelAt86:5.615},construction:'Outer raised lip, two narrow chased channels, recessed inner seam and return lip. The wider metal face leaves space for four native twin-leaf scroll groups. Floral scrolls remain native UiChrome paths, not baked into this bitmap.',exporter:'@resvg/resvg-js@2.6.2 (MPL-2.0), existing project dependency',assets:[{id,source:'source-art/ui/clean-gold-v11/'+id+'.svg',sourceSHA256:sha(svg+'\n'),derivedFrom:'source-art/ui/clean-gold-v11/unified-gold-skill-v13.svg',asset:'src/cocos/assets/resources/ui/quiet-bronze/'+id+'.png',pngSHA256:sha(png),size:[512,512],bytes:png.length}],artReview:{isolated:'Generated 120 px and 64 px comparison against v13; pending parent review.',runtime:'Pending integration by parent.',userAcceptance:'Not recorded.'}};
fs.writeFileSync(path.join(root,'provenance-v14.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify({id,bytes:png.length,size:[512,512],preview:'isolated-preview-v14.png'}));
