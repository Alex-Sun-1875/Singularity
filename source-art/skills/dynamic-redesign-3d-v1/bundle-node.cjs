#!/usr/bin/env node
'use strict';

// Independent design bundle only. Uses the project's installed Three and esbuild without installation.
const fs=require('node:fs');
const path=require('node:path');
const modules=path.resolve(__dirname,'../../../src/cocos/node_modules');
const esbuild=require(path.join(modules,'esbuild'));
const check=process.argv.includes('--check');
async function main(){
  for(const name of ['effects3d.source.js','model-loader.js','fx-geometry.js']){
    if(!fs.existsSync(path.join(__dirname,name)))throw new Error('3D design source is not ready: '+name);
  }
  const result=await esbuild.build({
    absWorkingDir:__dirname,
    entryPoints:['effects3d.source.js'],
    outfile:'effects.js',
    nodePaths:[modules],
    bundle:true,
    platform:'browser',
    format:'esm',
    target:['es2020'],
    mainFields:['browser','module','main'],
    treeShaking:true,
    minify:false,
    sourcemap:false,
    legalComments:'eof',
    charset:'utf8',
    write:!check,
    logLevel:'warning',
  });
  const version=JSON.parse(fs.readFileSync(path.join(modules,'three/package.json'),'utf8')).version;
  const bytes=check?result.outputFiles[0].contents.byteLength:fs.statSync(path.join(__dirname,'effects.js')).size;
  console.log(`${check?'Checked':'Bundled'} standalone 3D preview: Three ${version}, ${bytes} bytes${check?'':', effects.js'}`);
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
