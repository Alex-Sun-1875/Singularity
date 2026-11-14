const {chromium}=require('../../../src/cocos/node_modules/playwright');
const fs=require('node:fs'),path=require('node:path');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--enable-unsafe-swiftshader']});try{
 const page=await b.newPage({viewport:{width:1440,height:900}});const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 await page.goto((process.env.WEAPONS_REVIEW_URL??'http://127.0.0.1:7469/')+'?view=2d&player=3d&test=max');await page.waitForFunction(()=>globalThis.System);await page.evaluate(async()=>{globalThis.cc=await System.import('cc');globalThis.app=()=>cc.director.getScene()?.getChildByName('ChapterGame')?.getComponent('ChapterGame');});await page.waitForFunction(()=>app()?.actors&&!app().loading||app()?.failure,undefined,{timeout:120000});
 const r=await page.evaluate(()=>({failure:app().failure,actors:app().actors.inspect().slice(0,1)}));r.errors=errors;console.log(JSON.stringify(r));await page.screenshot({path:path.join(__dirname,'runtime-load.jpg'),type:'jpeg',quality:94});fs.writeFileSync(path.join(__dirname,'load-report.json'),JSON.stringify(r,null,2));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
