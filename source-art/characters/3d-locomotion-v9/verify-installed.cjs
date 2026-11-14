const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await browser.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&player=3d&test=max&revision=locomotion-v9');await page.waitForFunction(()=>globalThis.System);await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 const result=await page.evaluate(()=>{const a=app(),p=a.actors.player.active.get('player');return {failure:a.failure,revision:p.metadata.locomotionRevision,source:p.metadata.source,stride:p.stride,clips:Object.keys(p.clips),movementSpeed:a.session.movementSpeed};});
 assert.equal(result.failure,'');assert.equal(result.revision,'locomotion-v9');assert.equal(result.clips.length,14);assert.equal(result.movementSpeed,5.2);assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(__dirname,'runtime/installed-review.json'),JSON.stringify({...result,errors},null,2));console.log('CANONICAL_INSTALLED',JSON.stringify(result));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
