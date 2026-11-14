const {chromium}=require('playwright'),assert=require('node:assert/strict'),fs=require('node:fs');
(async()=>{const b=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true});try{
 const page=await b.newPage({viewport:{width:1280,height:720}}),errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto('http://localhost:7456/');await page.waitForFunction(()=>globalThis.__chapter?.inspect().ready, undefined, {timeout:60000});
 const result=await page.evaluate(async()=>{
  const app=__chapter.app;app.menu='qa';app.clearInput();const p=app.session.state.player,from={x:p.x,z:p.z};
  // A physical-only wall is deliberately absent from the algebraic footprint
  // query. This proves the controller result actually constrains game rules.
  const wall=new cc.Node('PhysicsOnlyWall');app.world.root.addChild(wall);wall.setPosition(p.x+1.7,1.5,p.z);const box=wall.addComponent(app.world.colliders[0].constructor);box.size=new cc.Vec3(.3,3,8);box.setGroup(2);box.setMask(8);
  await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
  const footprint=app.world.move(from,{x:4,z:0},.32);for(let i=0;i<30;i++)app.session.advance(.1,{x:1,z:0});
  const actual={x:p.x,z:p.z},capsule={x:app.capsule.node.position.x,z:app.capsule.node.position.z};wall.destroy();
  return {from,footprint,actual,capsule,physicsEngine:app.capsule.constructor.name,wallMask:box.getMask(),wallGroup:box.getGroup(),controllerMask:app.capsule.getMask(),controllerGroup:app.capsule.getGroup()};
 });
 assert.ok(result.footprint.x-result.from.x>3,'footprint baseline must be unconstrained');assert.ok(result.actual.x-result.from.x>.4,'character must move');assert.ok(result.actual.x-result.from.x<1.4,'real Bullet wall must block the player');assert.ok(Math.hypot(result.actual.x-result.capsule.x,result.actual.z-result.capsule.z)<.001);assert.equal(errors.length,0,errors.join('\n'));fs.writeFileSync('test-results/browser-physics.json',JSON.stringify({...result,errors},null,2));console.log(result);
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1;});



