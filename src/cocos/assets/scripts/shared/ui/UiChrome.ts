import {CompactGraphics} from './CompactGraphics';
import {Color,Graphics,Node} from 'cc';

/** One subdued clean-gold family shared with the v13 SVG surrounds. */
export const UI_FRAME_GOLD={
 metal:new Color(185,148,86),light:new Color(210,185,133),
 ornament:new Color(194,155,90),glint:new Color(217,204,162),shadow:new Color(29,23,12),
};

/** Shared skin geometry. Control measurements are logical screen units. */
export const UI_FRAME_LAYOUT={skin:'unified-gold-panel-v13',panelSkin:'double-gold-frame-v6',panelMaterial:'double-gold-inset-v6',crestSkin:'double-gold-stag-v6',crestShadowSkin:'double-gold-stag-shadow-v11',crestWidth:118,crestHeight:72,crestOffset:12,crestShadowPadding:4,capsuleSkin:'menu-pill-frame-v5',cornerRadius:12,padding:12,hit:48,gap:8,closeInset:8,closeGlyph:14} as const;

/** Approved two-mode header. Measurements are logical screen pixels. */
export const UI_PANEL_HEADER={height:64,hit:48,inset:12,gap:8,glyph:20,stroke:1.8,feedback:32,fallbackCapsuleWidth:118,fallbackCapsuleHeight:64} as const;

/** Measured slots from the approved 425×506 settings panel; input minima win. */
export const UI_GOLD_PANEL_RULES={
 title:{skin:'settings-title-rule-v11',width:356,height:8},
 row:{skin:'settings-row-rule-v11',width:347,height:8},
 vertical:{skin:'settings-footer-rule-v11',width:8,height:36},
} as const;

/** Logical screen insets and visible action rhythm for content-sized menus. */
export const UI_GOLD_PANEL_CONTENT={textInset:8,introTop:8,bodyBottom:8,actionVisualGap:16} as const;

/** Settings owns reference positions; other panels share the same rule skins. */
export const UI_SETTINGS_REFERENCE={width:425,height:506,titleX:-3,titleY:39.5,titleSize:34,closeOffset:49,closeSize:26,tabsY:104,tabsTextY:99,tabsFirstX:92,tabsStep:124.5,tabsSize:26,tabRuleOffset:25,tabActiveXOffset:2,rowFirstY:185,rowStep:75,rowHeight:60,rowRuleFirstY:223,rowSize:26,iconX:59,iconSize:36,labelX:90,toggleWidth:96,toggleHeight:42,toggleRight:36,toggleStateSize:26,toggleTextX:15,footerY:446.25,footerFirstX:122.5,footerStep:188.5,footerSize:24,bottom:35,mobileWidth:272,crestReserve:52,
 rules:{title:{...UI_GOLD_PANEL_RULES.title,x:213,y:67},tabs:{...UI_GOLD_PANEL_RULES.row,x:216.5,y:130},row:{...UI_GOLD_PANEL_RULES.row,x:216.5},footer:{...UI_GOLD_PANEL_RULES.vertical,x:210,y:446}},
} as const;

/** Shared action skin; layout owners choose visible size and input bounds. */
export const UI_MENU_BUTTON={width:434,height:82,fontSize:38,visualHeight:34,primary:'start-menu-primary-v8',secondary:'start-menu-secondary-v8'} as const;

/** Approved centered title-menu art; native source pixels and input units differ. */
export const UI_START_MENU={width:1844,height:853,titleWidth:272,titleHeight:97,titleY:125.5,subtitleWidth:200,subtitleHeight:54,subtitleY:205,ruleWidth:276,ruleHeight:23,ruleY:260.5,buttonWidth:UI_MENU_BUTTON.width,buttonHeight:UI_MENU_BUTTON.height,buttonFirstY:335,buttonStep:109,labelSize:UI_MENU_BUTTON.fontSize,hit:48,gap:8,maxWidth:220,footerY:809,footerClearance:18,primary:UI_MENU_BUTTON.primary,secondary:UI_MENU_BUTTON.secondary,title:'start-menu-title-v8',subtitle:'start-menu-subtitle-v8',rule:'start-menu-rule-v8'} as const;

/** Project-original scroll/leaf engraving, shared by rectangular and round frames. */
export class UiChrome {
 private static passes(width:number){return [
  {x:.22,y:-.24,width:width+.65,color:new Color(UI_FRAME_GOLD.shadow.r,UI_FRAME_GOLD.shadow.g,UI_FRAME_GOLD.shadow.b,230)},
  {x:0,y:0,width,color:new Color(UI_FRAME_GOLD.light.r,UI_FRAME_GOLD.light.g,UI_FRAME_GOLD.light.b,238)},
  {x:-.08,y:.12,width:Math.max(.28,width*.42),color:new Color(UI_FRAME_GOLD.glint.r,UI_FRAME_GOLD.glint.g,UI_FRAME_GOLD.glint.b,185)},
 ];}
 private static drawFrameCorners(g:Graphics,w:number,h:number,offsetX:number,offsetY:number,ornamentScale=1):void {
  const corner=Math.min(29,w*.15,h*.28)*ornamentScale;
  for(const sx of [-1,1])for(const sy of [-1,1]){
   const x=sx*(w/2-7)+offsetX,y=sy*(h/2-7)+offsetY,k=corner/28;
   const point=(t:number,d:number)=>({x:x-sx*t*k,y:y-sy*d*k});
   const move=(t:number,d:number)=>{const p=point(t,d);g.moveTo(p.x,p.y);};
   const curve=(a:number,b:number,c:number,d:number,e:number,f:number)=>{const p=point(a,b),q=point(c,d),r=point(e,f);g.bezierCurveTo(p.x,p.y,q.x,q.y,r.x,r.y);};
   move(28,1);curve(13,2,3,10,1,28);g.stroke();
   move(21,3);curve(8,1,6,16,15,14);curve(23,12,14,6,13,11);g.stroke();
   move(5,19);curve(2,9,13,2,17,7);curve(20,12,10,15,11,9);g.stroke();
  }
 }
 /** The original panel corner engraving, without its centered border vines. */
 static cornerOrnaments(parent:Node,w:number,h:number,ornamentScale=1):Graphics {
  const g=parent.addComponent(CompactGraphics);
  for(const pass of this.passes(1.05)){g.lineWidth=pass.width;g.strokeColor=pass.color;this.drawFrameCorners(g,w,h,pass.x,pass.y,ornamentScale);}
  return g;
 }
 static frame(parent:Node,w:number,h:number):Graphics {
  const g=parent.addComponent(CompactGraphics),stem=Math.min(18,w*.065);
  // The SVG owns the two metal lips. Native engraving adds only curls/leaves,
  // so its color and density remain identical at every stretched panel size.
  for(const pass of this.passes(1.05)){
   g.lineWidth=pass.width;g.strokeColor=pass.color;
   this.drawFrameCorners(g,w,h,pass.x,pass.y);
   // Centered vines stay on the border band rather than under panel text.
   for(const sy of [-1,1]){
    const y=sy*(h/2-4)+pass.y,x=pass.x;
    g.moveTo(x-stem,y);g.bezierCurveTo(x-stem*.65,y-sy*3,x-4,y-sy*3,x,y);g.bezierCurveTo(x+4,y-sy*3,x+stem*.65,y-sy*3,x+stem,y);g.stroke();
    g.moveTo(x-3,y);g.bezierCurveTo(x-5,y-sy*5,x+5,y-sy*5,x+3,y);g.stroke();
   }
   if(h>=70)for(const sx of [-1,1]){
    const x=sx*(w/2-4)+pass.x,y=pass.y,t=Math.min(12,h*.12);
    g.moveTo(x,y-t);g.bezierCurveTo(x-sx*3,y-t*.4,x-sx*3,y+t*.4,x,y+t);g.stroke();
    g.moveTo(x,y-3);g.bezierCurveTo(x-sx*5,y-6,x-sx*5,y+5,x,y+3);g.stroke();
   }
  }
  return g;
 }
 static circle(parent:Node,r:number):Graphics {
  const g=parent.addComponent(CompactGraphics);this.drawCircle(g,r);return g;
 }
 static drawCircle(g:Graphics,r:number):void {
  g.lineWidth=2;g.strokeColor=UI_FRAME_GOLD.shadow;g.circle(0,0,r);g.stroke();g.lineWidth=1.3;g.strokeColor=UI_FRAME_GOLD.metal;g.circle(0,0,r-.6);g.stroke();g.lineWidth=.8;g.strokeColor=UI_FRAME_GOLD.light;g.circle(0,0,r-3);g.stroke();
  for(let i=0;i<4;i++){const a=i*Math.PI/2,x=Math.sin(a)*r,y=Math.cos(a)*r;g.moveTo(x-2,y);g.lineTo(x,y+2);g.lineTo(x+2,y);g.lineTo(x,y-2);g.close();g.stroke();}
 }
 /** Raised paired leaves sit inside the wider skill bezel, clear of key/count corners. */
 static skillOrnament(parent:Node,r:number):Graphics {
  const g=parent.addComponent(CompactGraphics);if(r<=0)return g;
  const unit=r/32;
  for(const pass of this.passes(.62)){
   g.lineWidth=pass.width;g.strokeColor=pass.color;
   for(let i=0;i<4;i++){
    const angle=i*Math.PI/2;
    const point=(t:number,inset:number)=>{const a=angle+t*unit/r,d=r-inset*unit;return {x:Math.cos(a)*d+pass.x,y:Math.sin(a)*d+pass.y};};
    const move=(t:number,inset:number)=>{const p=point(t,inset);g.moveTo(p.x,p.y);};
    const curve=(a:number,b:number,c:number,d:number,e:number,f:number)=>{const p=point(a,b),q=point(c,d),s=point(e,f);g.bezierCurveTo(p.x,p.y,q.x,q.y,s.x,s.y);};
    // A shallow vine follows the band; each closed leaf folds back into it.
    move(-9,2.2);curve(-5,2.8,5,2.8,9,2.2);g.stroke();
    for(const side of [-1,1]){
     move(side*.8,2.6);curve(side*3.2,1.1,side*7.2,1.2,side*8.5,2.4);curve(side*6.1,4.4,side*2.8,4.2,side*3.1,2.6);g.stroke();
    }
    // The narrow central bud makes the four settings read as deliberate mounts.
    move(0,1.3);curve(-1.5,2.5,-1.1,3.9,0,4.6);curve(1.1,3.9,1.5,2.5,0,1.3);g.stroke();
   }
  }
  return g;
 }
 /** Eight map vines and four small rim curls use the same panel engraving. */
 static circleOrnament(parent:Node,r:number,scale=1):Graphics {
  const g=parent.addComponent(CompactGraphics);if(r<=0||scale<=0)return g;
  const small=r<48,unit=Math.max(.24,Math.min(1.3,r/120))*scale,count=small?4:8;
  const radial=small?Math.min(.48,r/60):.43,width=small?Math.max(.45,.85*Math.sqrt(unit)):1.05;
  for(const pass of this.passes(width)){
   g.lineWidth=pass.width;g.strokeColor=pass.color;
   for(let i=0;i<count;i++){
    // Cardinal small curls avoid key/count corners. Intercardinal map vines
    // leave compass letters and the chart opening clear.
    const angle=small?i*Math.PI/2:Math.PI/8+i*Math.PI/4;
    const point=(t:number,inset:number)=>{const a=angle+t*unit*.9/r,d=r-inset*unit*radial;return {x:Math.cos(a)*d+pass.x,y:Math.sin(a)*d+pass.y};};
    const move=(t:number,inset:number)=>{const p=point(t,inset);g.moveTo(p.x,p.y);};
    const curve=(t1:number,d1:number,t2:number,d2:number,t3:number,d3:number)=>{const p1=point(t1,d1),p2=point(t2,d2),p3=point(t3,d3);g.bezierCurveTo(p1.x,p1.y,p2.x,p2.y,p3.x,p3.y);};
    if(small){
     move(-17,10);curve(-9,4,4,5,16,10);curve(10,16,1,16,1,10);curve(3,6,10,8,8,12);curve(6,14,3,13,4,11);g.stroke();
    }else{
     move(-23,10);curve(-14,16,14,16,23,10);g.stroke();
     for(const side of [-1,1]){move(side*3,10);curve(side*8,4,side*17,6,side*21,11);curve(side*15,18,side*7,17,side*10,10);curve(side*12,7,side*17,10,side*15,13);g.stroke();}
     move(-3,9);curve(-2,3,3,3,5,5);curve(7,9,2,12,-3,9);g.stroke();
    }
   }
  }
  return g;
 }
}
