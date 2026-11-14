const {chromium}=require('playwright');const assert=require('node:assert/strict');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const p=await b.newPage({viewport:{width:1280,height:720}});await p.goto('http://localhost:7456/');await p.waitForFunction(()=>globalThis.__chapter?.inspect().ready&&globalThis.__chapter.inspect().actors?.length);
 const result=await p.evaluate(async()=>{const app=globalThis.__chapter.app;app.click('inventory');const nodes=[...app.hud.modal.children],modalOnTop=app.hud.modal.getSiblingIndex()===app.hud.root.children.length-1;app.hud.clearModal();await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));return {detachedAlive:nodes.filter(n=>cc.isValid(n,true)).length,modalOnTop};});
 assert.equal(result.detachedAlive,0,'closing a modal must destroy its UI subtree');assert.equal(result.modalOnTop,true,'modal shade/buttons must render and receive touches above the HUD');console.log('PASS modal layering and destruction',result);
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
