'use strict';
// Procedural artwork: no images, DOM, fonts or external runtime required.
const COLORS = { ink: '#101a1c', cream: '#f5ead1', ember: '#ffae5e', teal: '#7ad6bb' };
const names = ['营地边境', '焦油工坊', '余烬城门'];
function clamp(n, a, b) { return Math.max(a, Math.min(b, n)); }
function camera(g, width, height) {
  const scale = clamp(Math.min(width / 1040, height / 680), .48, 1.4);
  const p = g.player;
  const visibleW = width / scale, visibleH = height / scale;
  return { x: visibleW > 1600 ? (1600 - visibleW) / 2 : clamp(p.x - visibleW / 2, 0, 1600 - visibleW),
    y: visibleH > 1000 ? (1000 - visibleH) / 2 : clamp(p.y - visibleH / 2, 0, 1000 - visibleH), scale };
}
function worldPoint(g, width, height, sx, sy) { const c = camera(g, width, height); return { x: sx / c.scale + c.x, y: sy / c.scale + c.y }; }
function circle(ctx, x, y, r, color) { ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill(); }
function line(ctx, x1,y1,x2,y2,color,width=1) { ctx.strokeStyle=color; ctx.lineWidth=width; ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.stroke(); }
function label(ctx, str, x, y, size=14, color=COLORS.cream, align='left') { ctx.fillStyle=color; ctx.font=`${size}px sans-serif`; ctx.textAlign=align; ctx.textBaseline='middle'; ctx.fillText(str,x,y); }
function panel(ctx,x,y,w,h,fill='rgba(10,20,23,.87)') { ctx.fillStyle=fill; ctx.fillRect(x,y,w,h); ctx.strokeStyle='rgba(173,202,180,.18)'; ctx.lineWidth=1; ctx.strokeRect(x+.5,y+.5,w-1,h-1); }
function diamond(ctx,x,y,r,color) { ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(x,y-r);ctx.lineTo(x+r,y);ctx.lineTo(x,y+r);ctx.lineTo(x-r,y);ctx.closePath();ctx.fill(); }
function bar(ctx,x,y,w,h,v,color) {ctx.fillStyle='#273536';ctx.fillRect(x,y,w,h);ctx.fillStyle=color;ctx.fillRect(x,y,w*clamp(v,0,1),h);}
function render(ctx, g, width, height) {
  if (!ctx || !g || !g.player || !width || !height) return;
  const p = g.player, map = g.map || g.regions[g.region], c = camera(g,width,height), t = g.time || 0;
  const enemies = map.enemies || [], live = enemies.filter(e=>e.hp>0);
  ctx.save(); ctx.clearRect(0,0,width,height);ctx.fillStyle='#0c171b';ctx.fillRect(0,0,width,height);
  ctx.translate(-c.x*c.scale,-c.y*c.scale);ctx.scale(c.scale,c.scale);
  ctx.fillStyle=['#253632','#30342e','#293133'][g.region] || '#253632';ctx.fillRect(0,0,1600,1000);
  // Hand-laid causeway, moss, scattered stone. Deterministic decoration.
  for(let y=0;y<1000;y+=64) for(let x=0;x<1600;x+=64) {
    const seed=(x*13+y*31)%97;
    ctx.fillStyle=seed%3===0?'rgba(12,22,22,.17)':'rgba(110,132,107,.045)';ctx.fillRect(x+2,y+2,60,60);
    if(seed%5===0){line(ctx,x+14,y+39,x+18,y+28,'#466047',2);line(ctx,x+18,y+39,x+24,y+33,'#466047',2);}
    if(seed%7===0){ctx.fillStyle='#46534a';ctx.fillRect(x+38,y+15,8,4);}
  }
  ctx.fillStyle='rgba(185,162,115,.08)';ctx.fillRect(100,400,1400,112);
  line(ctx,100,404,1500,404,'rgba(202,179,129,.09)',2);line(ctx,100,510,1500,510,'rgba(202,179,129,.09)',2);
  // Broken perimeter walls.
  for(let x=0;x<1600;x+=52){ctx.fillStyle='#46514a';ctx.fillRect(x,0,48,22);ctx.fillRect(x,978,48,22);ctx.fillStyle='#657063';ctx.fillRect(x,0,48,4);}
  for(let y=0;y<1000;y+=52){ctx.fillStyle='#46514a';ctx.fillRect(0,y,22,48);ctx.fillRect(1578,y,22,48);}
  for(const h of map.hazards||[]) {circle(ctx,h.x+2,h.y+5,h.r+8,'#35443b');circle(ctx,h.x,h.y,h.r+3,'#101b20');circle(ctx,h.x,h.y,h.r-5,'#080e14');ctx.strokeStyle='#677564';ctx.lineWidth=3;ctx.beginPath();ctx.arc(h.x,h.y,h.r,Math.PI,Math.PI*2);ctx.stroke();}
  for(const w of map.walls||[]) {ctx.fillStyle='rgba(4,10,13,.35)';ctx.fillRect(w.x+7,w.y+9,w.w,w.h);ctx.fillStyle='#4c5951';ctx.fillRect(w.x,w.y,w.w,w.h);ctx.fillStyle='#6b7766';ctx.fillRect(w.x,w.y,w.w,6);for(let x=w.x+36;x<w.x+w.w;x+=40)line(ctx,x,w.y,x,w.y+w.h,'#36463f',2);}
  // Camp checkpoint flag / warm fire.
  circle(ctx,110,450,45,'rgba(255,169,78,.07)');line(ctx,80,455,80,392,'#a7aa89',4);ctx.fillStyle='#78b79c';ctx.fillRect(80,392,30,20);label(ctx,'营火',109,508,12,'#a4baa6','center');
  for(let i=0;i<5;i++){const a=i*1.3+t*.5;circle(ctx,110+Math.cos(a)*6,455+Math.sin(a)*5,12-i,'#ffae5e');}circle(ctx,110,451,5,'#ffe9ac');
  const exit=g.exit||{x:1450,y:450};
  circle(ctx,exit.x,exit.y,49, live.length?'rgba(202,102,63,.08)':'rgba(110,232,192,.12)');
  ctx.strokeStyle=live.length?'#996e4d':'#88d9b4';ctx.lineWidth=8;ctx.beginPath();ctx.arc(exit.x,exit.y,31,Math.PI,Math.PI*2);ctx.lineTo(exit.x+31,exit.y+35);ctx.stroke();line(ctx,exit.x-31,exit.y,exit.x-31,exit.y+35,ctx.strokeStyle,8);
  if(live.length){for(let i=-20;i<=20;i+=10)line(ctx,exit.x+i,exit.y-19,exit.x+i,exit.y+34,'#9b8060',3);}else{ctx.fillStyle='rgba(133,233,199,.15)';ctx.fillRect(exit.x-24,exit.y-20,48,54);diamond(ctx,exit.x,exit.y+3,8,'#b1f7da');}
  label(ctx,live.length?'击败守卫开启':(g.region===2?'返回营地':'前往下一片区'),exit.x,exit.y+62,13,live.length?'#c9ab82':'#a7eacc','center');
  for(const b of map.barrels||[]) if(b.alive!==false){circle(ctx,b.x+3,b.y+10,18,'rgba(0,0,0,.26)');ctx.fillStyle='#a8452d';ctx.fillRect(b.x-14,b.y-16,28,32);ctx.fillStyle='#e8753c';ctx.fillRect(b.x-10,b.y-15,7,30);line(ctx,b.x-15,b.y-9,b.x+15,b.y-9,'#302f28',4);line(ctx,b.x-15,b.y+9,b.x+15,b.y+9,'#302f28',4);diamond(ctx,b.x,b.y,6,'#ffe2a0');circle(ctx,b.x,b.y-21,3,'#f9ae5c');}
  for(const item of map.pickups||[]) if(item.alive!==false){const bob=Math.sin(t*3+item.x)*3;const colors={oil:'#72c7cb',health:'#9ddca0',coin:'#f3cd79',power:'#d3b7f4',fire:'#ff9e60',upgrade:'#d3b7f4',chest:'#d3b7f4'};const color=colors[item.type]||'#d3b7f4';circle(ctx,item.x,item.y,23,'rgba(228,205,137,.06)');diamond(ctx,item.x,item.y+bob,10,color);diamond(ctx,item.x,item.y+bob,4,'#fff2d0');label(ctx,{oil:'油',heal:'药',health:'药',coin:'金',power:'剑',fire:'火',upgrade:'遗物',chest:'遗物'}[item.type]||'遗物',item.x,item.y+25,11,color,'center');}
  circle(ctx,p.x,p.y+6,25,'rgba(99,229,211,.12)');ctx.strokeStyle='#88e4cf';ctx.lineWidth=2;ctx.beginPath();ctx.arc(p.x,p.y+6,23,0,Math.PI*2);ctx.stroke();
  const actors=[...live.map(e=>({...e,enemy:true})),{...p,enemy:false}].sort((a,b)=>a.y-b.y);
  for(const a of actors){const r=a.boss?29:a.enemy?16:17;circle(ctx,a.x+2,a.y+12,r,'rgba(4,9,13,.32)');
    if(a.enemy && a.windup>0){ctx.strokeStyle='rgba(255,99,73,.7)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(a.x,a.y,a.boss?110:43,0,Math.PI*2);ctx.stroke();}
    if(!a.enemy&&p.dashTimer>0){circle(ctx,a.x-Math.cos(p.angle||0)*20,a.y-Math.sin(p.angle||0)*20,18,'rgba(133,225,211,.28)');}
    ctx.save();ctx.translate(a.x,a.y);if(a.enemy){ctx.fillStyle=a.boss?'#714746':'#744b3c';ctx.beginPath();ctx.moveTo(-r,14);ctx.lineTo(-r*.7,-r);ctx.lineTo(r*.7,-r);ctx.lineTo(r,14);ctx.closePath();ctx.fill();circle(ctx,0,-r*.35,r*.65,a.boss?'#aaa69a':'#b9a68d');ctx.fillStyle='#303338';ctx.fillRect(-r*.65,-r*.5,r*1.3,r*.24);line(ctx,-6,-r*.38,-2,-r*.38,'#ffac62',2);line(ctx,2,-r*.38,6,-r*.38,'#ffac62',2);line(ctx,r+3,-9,r+3,18,'#918776',a.boss?8:4);if(a.boss){diamond(ctx,0,-r-4,6,'#ffd38a');} }
    else {diamond(ctx,0,-32,5,'#9df3e4');ctx.rotate((p.angle||0)+Math.PI/2);ctx.fillStyle='#3f8e88';ctx.beginPath();ctx.moveTo(-13,0);ctx.lineTo(-18,24);ctx.lineTo(14,21);ctx.lineTo(12,-5);ctx.closePath();ctx.fill();circle(ctx,0,-5,11,'#d2cead');ctx.fillStyle='#334d50';ctx.fillRect(-11,-10,22,7);ctx.fillStyle='#e8d7a0';ctx.fillRect(-8,-8,16,2);line(ctx,18,8,18,-28,'#eae2bf',5);line(ctx,10,1,26,1,'#b7985e',4);}
    ctx.restore();if(a.enemy){bar(ctx,a.x-r,a.y-r-13,r*2,4,a.hp/a.maxHp,a.boss?'#f3a367':'#d58c66');}
  }
  if(p.attackTimer>0){ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.angle||0);ctx.fillStyle='rgba(255,233,173,.2)';ctx.strokeStyle='#ffdc94';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(0,0);ctx.arc(0,0,80,-1.05,1.05);ctx.closePath();ctx.fill();ctx.beginPath();ctx.arc(0,0,80,-1.05,1.05);ctx.stroke();ctx.restore();}
  for(const e of g.effects||[]){ctx.save();const alpha=clamp((e.t||.1)*2,0,1);ctx.globalAlpha=alpha; if(/fire|blast|explos/.test(e.type)){const r=e.r||90;circle(ctx,e.x,e.y,r,'rgba(255,122,48,.2)');ctx.strokeStyle='#ffc36d';ctx.lineWidth=3;ctx.beginPath();ctx.arc(e.x,e.y,r*(1.1-alpha*.25),0,Math.PI*2);ctx.stroke();for(let i=0;i<8;i++){const a=i*Math.PI/4+t;circle(ctx,e.x+Math.cos(a)*r*.65,e.y+Math.sin(a)*r*.65,5,'#ffe09b');}}
    else if(e.type==='text'){label(ctx,e.text||'',e.x,e.y-(1-alpha)*20,19,'#ffe1a5','center');}
    else{for(let i=0;i<6;i++){const a=i*1.047;line(ctx,e.x+Math.cos(a)*8,e.y+Math.sin(a)*8,e.x+Math.cos(a)*25,e.y+Math.sin(a)*25,e.type==='heal'?'#92e6bb':'#ffd390',3);}}ctx.restore();}
  ctx.restore();
  // Screen-space HUD. Fixed-size labels remain legible on touch devices.
  ctx.save(); const narrow=width<600, pad=narrow?12:24, hudW=Math.min(narrow?260:320,width-pad*2);
  panel(ctx,pad,pad,hudW,narrow?86:96);label(ctx,'剑 与 火',pad+14,pad+21,narrow?20:23);label(ctx,`${String(g.region+1).padStart(2,'0')} / ${names[g.region]||'边境'}`,pad+hudW-14,pad+22,12,'#a5bbad','right');
  bar(ctx,pad+14,pad+43,hudW-28,8,p.hp/p.maxHp,'#e5a065');label(ctx,`${Math.ceil(p.hp)} / ${p.maxHp}`,pad+14,pad+65,12,'#f0cfaa');label(ctx,`燃油 ${p.oil} / ${p.maxOil}   ·   金 ${p.coins||0}`,pad+hudW-14,pad+65,12,'#a7d5cc','right');
  const objective = live.length?`清除守卫 ${live.length} · 将敌人击落深坑`:(g.region===2?'城门已开 · 前往光门凯旋':'区域已净空 · 前往右侧光门');
  if(!narrow){panel(ctx,width-336,pad+54,312,60);label(ctx,'当前目标',width-320,pad+71,11,'#9eaf9f');label(ctx,objective,width-320,pad+93,13);}
  else {panel(ctx,pad,pad+94,Math.min(width-pad*2,320),30);label(ctx,objective,pad+12,pad+109,11,'#d1d9bd');}
  if(p.upgrade||g.upgrade)label(ctx,(p.upgrade||g.upgrade)==='fire'?'遗物：余烬之心 · 火焰强化':'遗物：破阵刃 · 剑势强化',pad,height-25,12,'#cfb7e9');
  if(g.toast&&g.toastTime>0){const tw=Math.min(width-32,Math.max(240,g.toast.length*14+40));panel(ctx,(width-tw)/2,narrow?height*.29:height-108,tw,42,'rgba(20,33,32,.94)');label(ctx,g.toast,width/2,(narrow?height*.29:height-108)+21,narrow?12:14,'#f7d9a4','center');}
  // Small route map, deliberately hidden on small screens so controls stay clear.
  if(!narrow){const mx=width-170,my=height-118,mw=144,mh=90;panel(ctx,mx-6,my-6,mw+12,mh+12);ctx.fillStyle='#32483e';ctx.fillRect(mx,my,mw,mh);for(const h of map.hazards||[])circle(ctx,mx+h.x/1600*mw,my+h.y/1000*mh,Math.max(2,h.r/1600*mw),'#101d22');for(const e of live)circle(ctx,mx+e.x/1600*mw,my+e.y/1000*mh,e.boss?3:2,'#e19a71');diamond(ctx,mx+exit.x/1600*mw,my+exit.y/1000*mh,3,'#87d8b4');circle(ctx,mx+p.x/1600*mw,my+p.y/1000*mh,3,'#fff3c9');}
  ctx.restore();
}
module.exports = { render, camera, worldPoint };
