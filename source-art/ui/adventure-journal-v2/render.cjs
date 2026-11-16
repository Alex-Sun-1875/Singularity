const path=require('node:path'),fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const {chromium}=require('../../../src/cocos/node_modules/playwright');

async function main(){
 const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--allow-file-access-from-files']});
 const report={scope:'Static design mockup rendering only; not the running Cocos game or TapTap acceptance.',viewports:[]};
 try{
  for(const viewport of [{width:844,height:390},{width:932,height:430}]){
   const context=await browser.newContext({viewport,deviceScaleFactor:3,isMobile:true,hasTouch:true});
   const page=await context.newPage();const errors=[];page.on('pageerror',error=>errors.push(String(error)));
   for(const view of ['tasks','map']){
    await page.goto(pathToFileURL(path.join(__dirname,'index.html')).href+'?view='+view);
    await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(160);
    const name=view+'-'+viewport.width*3+'x'+viewport.height*3+'.png';
    await page.screenshot({path:path.join(__dirname,name)});
    const layout=await page.evaluate(()=>{
     const visible=element=>{const b=element.getBoundingClientRect(),s=getComputedStyle(element);return b.width>0&&b.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&b.bottom>0&&b.top<innerHeight&&b.right>0&&b.left<innerWidth};
     const buttons=[...document.querySelectorAll('.top button,.page.active button')].filter(visible).map(element=>{const b=element.getBoundingClientRect();return {text:element.textContent.trim()||element.getAttribute('aria-label'),width:b.width,height:b.height};});
     return {buttons,minimumButtonWidth:Math.min(...buttons.map(b=>b.width)),minimumButtonHeight:Math.min(...buttons.map(b=>b.height)),pageOverflow:document.documentElement.scrollWidth>innerWidth,treeScroll:document.querySelector('.tree-scroll').scrollHeight>document.querySelector('.tree-scroll').clientHeight,readerScroll:document.querySelector('.reader-scroll').scrollHeight>document.querySelector('.reader-scroll').clientHeight};
    });
    report.viewports.push({viewport,deviceScaleFactor:3,view,screenshot:name,layout,errors:[...errors]});
   }
   await context.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(__dirname,'design-review.json'),JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.viewports.map(v=>({viewport:v.viewport,view:v.view,minWidth:v.layout.minimumButtonWidth,minHeight:v.layout.minimumButtonHeight,errors:v.errors.length}))));
}
main().catch(error=>{console.error(error);process.exitCode=1;});
