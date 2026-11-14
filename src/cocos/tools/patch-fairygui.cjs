// Cocos 3.8's trimmed builds expose this class under its explicit component name.
const fs=require('node:fs');
const path=require('node:path');
const base=path.join(__dirname,'../node_modules/fairygui-cc');
const pkg=JSON.parse(fs.readFileSync(path.join(base,'package.json'),'utf8'));
if(pkg.version!=='1.2.2')throw Error('Review the FairyGUI Cocos compatibility patch before upgrading '+pkg.version);
for(const file of ['fairygui.mjs','fairygui.min.mjs']){
 const target=path.join(base,'dist',file);
 const source=fs.readFileSync(target,'utf8');
 let patched=source.replace(/\bMask(?=\s*,[^\n]*?from\s*['"]cc['"])/,'MaskComponent as Mask');
 if(source===patched&&!source.includes('MaskComponent as Mask'))throw Error('Unexpected FairyGUI engine import in '+file);
 // Preserve wheel-down's negative Y instead of Math.max(0, negativeY).
 const wheel=/Math\.max\(\s*([\w$]+)\.getScrollX\(\),\s*\1\.getScrollY\(\)\s*\)/;
 patched=patched.replace(wheel,'($1.getScrollY() || $1.getScrollX())');
 if(!/([\w$]+)\.getScrollY\(\)\s*\|\|\s*\1\.getScrollX\(\)/.test(patched))throw Error('Unexpected FairyGUI wheel handler in '+file);
 if(source!==patched)fs.writeFileSync(target,patched);
}
console.log('FairyGUI 1.2.2: applied Cocos 3.8 Mask alias and signed wheel delta.');
