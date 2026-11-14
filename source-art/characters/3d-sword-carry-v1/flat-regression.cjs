// Reuse the real default renderer and game session; no new test dependencies.
const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await b.newPage({viewport:{width:1440,height:900}}),errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:7469/?view=2d&test=max&revision=carry-regression');await page.waitForFunction(()=>globalThis.System);
 await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});
 await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 const result=await page.evaluate(()=>{const a=app();if(a.failure)throw Error(a.failure);a.enabled=false;a.menu='';a.session.state.inventory.W01=1;if(!a.session.equip('W01'))throw Error('equip W01');const sample=(attack=false,dash=false)=>{a.process(a.session.advance(1/30,{x:0,z:0,aim:0,attack,dash}));a.actors.update(a.session,1/30,false);return a.actors.inspect().find(x=>x.id==='player').weaponCarry;};for(let i=0;i<150;i++)sample();const idle=sample(),attack=sample(true);for(let i=0;i<100;i++)sample();const returned=sample(),dash=sample(false,true);return {idle,attack,returned,dash};});
 assert.deepEqual(result,{idle:'stowed',attack:'ready',returned:'stowed',dash:'stowed'});assert.deepEqual(errors,[]);
 fs.writeFileSync(path.join(__dirname,'runtime/flat-regression.json'),JSON.stringify({result,errors},null,2));console.log(JSON.stringify(result));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
