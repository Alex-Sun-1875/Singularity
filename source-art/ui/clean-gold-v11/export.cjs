// Original circular variants of the project's SupplyBelt panel-frame SVG.
// Rasterization uses the already installed resvg dependency; no downloads.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
fs.mkdirSync(output,{recursive:true});
const defs=`<defs>
 <linearGradient id="gold-metal" x1="75" y1="35" x2="435" y2="480" gradientUnits="userSpaceOnUse">
  <stop stop-color="#C99D45"/><stop offset=".16" stop-color="#DAAE65"/>
  <stop offset=".29" stop-color="#F7DA9D"/><stop offset=".44" stop-color="#E0B46A"/>
  <stop offset=".62" stop-color="#DAAE65"/><stop offset=".79" stop-color="#F7DA9D"/>
  <stop offset="1" stop-color="#C99D45"/>
 </linearGradient>
 <linearGradient id="gold-highlight" x1="50" y1="15" x2="430" y2="485" gradientUnits="userSpaceOnUse">
  <stop stop-color="#FFF0BF"/><stop offset=".26" stop-color="#F7DA9D"/>
  <stop offset=".58" stop-color="#E4B66A"/><stop offset=".86" stop-color="#F7DA9D"/>
  <stop offset="1" stop-color="#E0B46A"/>
 </linearGradient>
 <linearGradient id="dark-inset" x1="0" y1="0" x2="0" y2="512" gradientUnits="userSpaceOnUse">
  <stop stop-color="#211910"/><stop offset=".4" stop-color="#19130E"/>
  <stop offset="1" stop-color="#100D09"/>
 </linearGradient>
</defs>`;
// The full visible surround is about18 source pixels radially at512, close to
// SupplyBelt's fine double metal lip. Brown shades are limited to the undercut.
const border=`
 <circle cx="256" cy="256" r="250.5" stroke="#070501" stroke-opacity=".94" stroke-width="5"/>
 <circle cx="256" cy="256" r="244.5" stroke="url(#gold-metal)" stroke-width="12"/>
 <circle cx="256" cy="256" r="249.6" stroke="url(#gold-highlight)" stroke-width="1.55"/>
 <circle cx="256" cy="256" r="238.8" stroke="#100C05" stroke-width="2.2"/>
 <circle cx="256" cy="256" r="236.3" stroke="#E4B66A" stroke-width="1.45"/>
 <circle cx="256" cy="256" r="234.9" stroke="#0A0704" stroke-opacity=".9" stroke-width="1.25"/>
 <path d="M82.95 80.66A246.35 246.35 0 0 1 422.5 74.46" stroke="#FFF0BF" stroke-opacity=".58" stroke-width="1.2"/>
`;
const shell=(title,content,extra='')=>`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" fill="none"><title>${title}</title>${defs}${extra}${content}</svg>\n`;
const wedge=['256,256'];
for(let angle=220;angle<=320;angle+=1){const a=angle*Math.PI/180;wedge.push(`${256+700*Math.cos(a)},${256-700*Math.sin(a)}`);}
const assets=[
 {id:'clean-gold-ring-v11',title:'SupplyBelt-family polished gold circular surround; transparent aperture',svg:shell('SupplyBelt-family polished gold circular surround',border)},
 {id:'clean-gold-medallion-v11',title:'SupplyBelt-family polished gold medallion with dark recessed center',svg:shell('SupplyBelt-family polished gold medallion',`<circle cx="256" cy="256" r="237" fill="url(#dark-inset)"/>${border}`)},
 {id:'clean-gold-rail-v11',title:'SupplyBelt-family lower polished gold tool arc220 to320degrees',svg:shell('SupplyBelt-family lower gold tool arc',`<g clip-path="url(#tool-arc)">${border}</g>`,`<defs><clipPath id="tool-arc"><polygon points="${wedge.join(' ')}"/></clipPath></defs>`)},
];
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const records=[];
for(const asset of assets){
 const source=path.join(root,asset.id+'.svg');fs.writeFileSync(source,asset.svg);
 const png=new Resvg(asset.svg,{fitTo:{mode:'width',value:512}}).render().asPng();
 const target=path.join(output,asset.id+'.png');fs.writeFileSync(target,png);
 records.push({id:asset.id,source:path.relative(project,source).replaceAll('\\','/'),sourceSHA256:sha(asset.svg),asset:path.relative(project,target).replaceAll('\\','/'),pngSHA256:sha(png),size:[512,512],bytes:png.length});
}
const panelSource='source-art/materials/chapter-one-v3/ui-kit/panel-frame.svg';
const provenance={
 version:'clean-gold-v11',date:'2026-11-08',
 userDirection:'Match the SupplyBelt outer surround; bright gold, thin double border and curled ornaments, without aged brass/cast-metal weathering.',
 originalDesignSource:panelSource,originalDesignSHA256:sha(fs.readFileSync(path.join(project,panelSource))),
 ownership:'Original variants of the existing project-owned SVG family; no external game pixels, no external asset download, and no new generation.',
 palette:{gold:'#DAAE65',light:'#F7DA9D',ornament:'#E4B66A',brightGold:'#E0B46A',mainGradientLow:'#C99D45'},
 geometry:'Clean smooth thin double circular lip, approximately18 source pixels radial width at512. Dark values appear only in the narrow recess separator. Transparent central opening on ring/rail; original smooth dark inset on medallion. Runtime UiChrome.circleOrnament supplies the shared curled details.',
 exporter:'@resvg/resvg-js@2.6.2 (MPL-2.0), existing project dependency',
 assets:records,
 artReview:{source:'SVG geometry/palette reviewed against SupplyBelt family.',runtime:'Pending integrated screenshot review.',userAcceptance:'Not recorded.'}
};
fs.writeFileSync(path.join(root,'provenance.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify(records.map(({id,bytes})=>({id,bytes})),null,2));
