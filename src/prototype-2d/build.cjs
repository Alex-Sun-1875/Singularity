const path=require('node:path');
const esbuild=require('../cocos/node_modules/esbuild');
esbuild.buildSync({entryPoints:[path.join(__dirname,'main.ts')],outfile:path.join(__dirname,'game.bundle.js'),bundle:true,format:'iife',platform:'browser',target:['es2020'],minify:false,sourcemap:true});
console.log('Built isolated 2D prototype. Existing Cocos game and saves are unchanged.');
