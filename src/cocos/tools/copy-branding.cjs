// Store artwork stays outside Cocos asset bundles; Web builds only need two small icons.
const fs=require('node:fs'),path=require('node:path');
const {loadConfig}=require('./taptap-config.cjs');
const project=path.resolve(__dirname,'..'),output=path.resolve(process.argv[2]||'');
const buildRoot=fs.realpathSync(path.join(project,'build'))+path.sep;
if(!output.startsWith(buildRoot)||!fs.existsSync(output)||!fs.realpathSync(output).startsWith(buildRoot))throw new Error('Branding output must be an existing project Web build directory.');
const branding=loadConfig().branding;
const destination=path.join(output,'branding');fs.mkdirSync(destination,{recursive:true});
for(const [key,name]of [['favicon','favicon.png'],['webIcon','icon-192.png']]){
 const source=path.resolve(project,branding[key]);if(!source.startsWith(project+path.sep))throw new Error('Brand asset must remain inside the Cocos project.');
 fs.copyFileSync(source,path.join(destination,name));
}
console.log('Web game icons copied: '+destination);
