const fs=require('node:fs'),path=require('node:path');
function assertSourcePolicy(settings){
 const modules=settings.modules;
 if(modules?.graphics?.pipeline!=='legacy-pipeline')throw Error('Performance policy: select the Cocos 3.8.8 legacy forward pipeline');
 if(!modules.configs?.[modules.globalConfigKey])throw Error('Performance policy: missing active engine module configuration');
 for(const [name,config]of Object.entries(modules.configs)){
  const cache=config.cache;
  if(cache?.['gfx-webgl']?._value!==false||cache?.['gfx-webgl2']?._value!==true||config.includeModules?.includes('gfx-webgl')||!config.includeModules?.includes('gfx-webgl2'))throw Error(`Render policy: WebGL 2 is required and WebGL 1 fallback is disabled in ${name}`);
  if(cache?.['render-pipeline']?._option!=='legacy-pipeline'||cache?.['render-pipeline']?._value!==true||cache?.['legacy-pipeline']?._value!==true||cache?.['custom-pipeline']?._value!==false||!config.includeModules?.includes('legacy-pipeline')||config.includeModules.includes('custom-pipeline'))throw Error(`Performance policy: inconsistent render modules in ${name}`);
 }
}
function assertBuildPolicy(settings){
 if(settings.CocosEngine!=='3.8.8'||settings.rendering?.customPipeline!==false)throw Error('Performance policy: built settings must use Cocos 3.8.8 legacy forward rendering; CRP causes repeated framebuffer checks in the Android baseline');
}
function assertEnginePolicy(source){
 // References in DeviceManager survive feature stripping; only actual exports
 // prove the backend implementation was included in the finished engine.
 const ts=require('typescript'),tree=ts.createSourceFile('cc.js',source,ts.ScriptTarget.Latest,true,ts.ScriptKind.JS),exports=new Set();
 function findRegister(node){
  if(ts.isCallExpression(node)&&ts.isPropertyAccessExpression(node.expression)&&node.expression.expression.getText(tree)==='System'&&node.expression.name.text==='register'){
   let factory=node.arguments[node.arguments.length-1];
   while(ts.isParenthesizedExpression(factory))factory=factory.expression;
   const binding=factory.parameters?.[0]?.name;
   if(binding&&ts.isIdentifier(binding)){
    function visit(child){
     if(ts.isCallExpression(child)&&ts.isIdentifier(child.expression)&&child.expression.text===binding.text){
      const arg=child.arguments[0];
      if(arg&&ts.isStringLiteral(arg)&&child.arguments.length>1)exports.add(arg.text);
      else if(arg&&ts.isObjectLiteralExpression(arg))for(const property of arg.properties)if(property.name&&(ts.isIdentifier(property.name)||ts.isStringLiteral(property.name)))exports.add(property.name.text);
     }
     ts.forEachChild(child,visit);
    }
    visit(factory);
   }
  }
  ts.forEachChild(node,findRegister);
 }
 findRegister(tree);
 if(!exports.has('WebGL2Device'))throw Error('Render policy: generated engine is missing the WebGL 2 backend; Creator minigame defaults can strip it even when project settings enable it');
 if(exports.has('WebGLDevice'))throw Error('Render policy: generated engine includes the disabled WebGL 1 backend');
}
function assertMinigameEntryPolicy(source){
 const starts=[...source.matchAll(/\bfirstScreen\.start\(\s*(['"])[^'"]*\1\s*,\s*(['"])[^'"]*\2\s*,\s*(['"])(true|false)\3\s*\)/g)];
 if(starts.length!==1||starts[0][4]!=='true')throw Error('Render policy: minigame first screen must create a WebGL 2 context for the WebGL 2-only engine');
}
function assertMinigameStartupPolicy(settings,source){
 if(settings.splashScreen?.totalTime!==0)throw Error('Startup policy: the engine splash screen must stay disabled');
 if(!/\bgetContext\(\s*['"]webgl2['"]/.test(source)||/['"](?:logo|slogan)\.png['"]|\buse(?:Default)?Logo\s*=\s*true\b/.test(source))throw Error('Startup policy: use the project first screen without the Cocos logo or slogan');
}
function check(project,build){
 assertSourcePolicy(JSON.parse(fs.readFileSync(path.join(project,'settings/v2/packages/engine.json'),'utf8')));
 if(build){
  const src=path.join(build,'src'),settings=fs.readdirSync(src).filter(name=>/^settings(?:\.[a-z0-9]+)?\.json$/.test(name));
  if(!settings.length)throw Error('Performance policy: no generated render settings found');
  for(const name of settings)assertBuildPolicy(JSON.parse(fs.readFileSync(path.join(src,name),'utf8')));
  const engineDir=path.join(build,'cocos-js'),engines=fs.readdirSync(engineDir).filter(name=>/^cc(?:\.[a-z0-9]+)?\.js$/.test(name));
  if(!engines.length)throw Error('Render policy: no generated engine found');
  for(const name of engines)assertEnginePolicy(fs.readFileSync(path.join(engineDir,name),'utf8'));
  const entry=path.join(build,'game.js');
  if(fs.existsSync(entry)){
   const entrySource=fs.readFileSync(entry,'utf8');
   assertMinigameEntryPolicy(entrySource);
   const firstScreenImport=/\bfirstScreen\s*=\s*require\(\s*(['"])(\.\/first-screen(?:\.[a-z0-9]+)?(?:\.js)?)\1\s*\)/.exec(entrySource);
   if(!firstScreenImport)throw Error('Startup policy: missing project first-screen entry');
   const firstScreenPath=path.join(build,firstScreenImport[2].endsWith('.js')?firstScreenImport[2]:firstScreenImport[2]+'.js');
   const firstScreen=fs.readFileSync(firstScreenPath,'utf8');
   for(const name of settings)assertMinigameStartupPolicy(JSON.parse(fs.readFileSync(path.join(src,name),'utf8')),firstScreen);
  }
 }
}
if(require.main===module){try{const build=process.argv.indexOf('--build');check(path.resolve(__dirname,'..'),build>=0?path.resolve(process.argv[build+1]):undefined);console.log('Render policy passed: Cocos 3.8.8 legacy forward');}catch(error){console.error(error.message);process.exitCode=1;}}
module.exports={assertSourcePolicy,assertBuildPolicy,assertEnginePolicy,assertMinigameEntryPolicy,assertMinigameStartupPolicy,check};
