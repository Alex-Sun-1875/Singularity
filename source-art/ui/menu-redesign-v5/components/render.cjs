// Derive reusable, stretchable menu parts from the established gold SVG skin.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../../../..');
const {Resvg}=require(path.join(root,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(root,'src/cocos/assets/resources/ui/quiet-bronze');
const original=fs.readFileSync(path.join(root,'source-art/ui/clean-gold-v11/unified-gold-panel-v13.svg'),'utf8');
const defs=original.match(/<defs>([\s\S]*?)<\/defs>/)[1];
for(const [name,w,h,r] of [['menu-panel-frame-v5',512,512,36],['menu-pill-frame-v5',512,128,60]]){
 const rect=(inset,radius,stroke,width,opacity=1)=>`<rect x="${inset}" y="${inset}" width="${w-inset*2}" height="${h-inset*2}" rx="${radius}" stroke="${stroke}" stroke-width="${width}" opacity="${opacity}"/>`;
 const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" fill="none"><defs>${defs}</defs>${rect(4,r,'#070501',7,.9)}${rect(4,r,'url(#gold-metal)',4.8)}${rect(10,r-6,'#100C05',3)}${rect(13,r-9,'url(#gold-highlight)',1.6,.92)}<path d="M${r+4} 5H${w-r-4}" stroke="url(#gold-highlight)" stroke-width="1.1" opacity=".8"/></svg>`;
 fs.writeFileSync(path.join(__dirname,name+'.svg'),svg);fs.writeFileSync(path.join(output,name+'.png'),new Resvg(svg).render().asPng());
}
const thumb=`<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><defs><radialGradient id="metal" cx=".3" cy=".2" r=".9"><stop stop-color="#E1D1A8"/><stop offset=".3" stop-color="#C6B184"/><stop offset=".6" stop-color="#A18B60"/><stop offset="1" stop-color="#65502E"/></radialGradient><linearGradient id="rim" x2="1" y2="1"><stop stop-color="#D9CCA2"/><stop offset=".5" stop-color="#AB853B"/><stop offset="1" stop-color="#211910"/></linearGradient></defs><circle cx="32" cy="33" r="28" fill="#080705" opacity=".8"/><circle cx="32" cy="31" r="27" fill="url(#metal)" stroke="url(#rim)" stroke-width="2.5"/><circle cx="32" cy="31" r="22.5" fill="none" stroke="#D2B985" stroke-opacity=".45" stroke-width="1"/><path d="M15 20Q31 9 48 20" fill="none" stroke="#E0D0AB" stroke-opacity=".5" stroke-width="1.2"/></svg>`;
fs.writeFileSync(path.join(__dirname,'menu-toggle-thumb-v5.svg'),thumb);fs.writeFileSync(path.join(output,'menu-toggle-thumb-v5.png'),new Resvg(thumb).render().asPng());
