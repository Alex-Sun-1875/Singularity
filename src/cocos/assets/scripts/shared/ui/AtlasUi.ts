import {Color,HorizontalTextAlignment,Sprite,SpriteFrame,VerticalTextAlignment} from 'cc';
import {AutoSizeType,ButtonMode,Controller,GButton,GComponent,GGraph,GImage,GObject,GTextField,OverflowType,UIPackage} from 'fairygui-cc';
import {UiSkin} from './UiSkin';

export {UI_COLORS as ATLAS_COLORS} from './UiTheme';
import {UI_COLORS as ATLAS_COLORS} from './UiTheme';

/** Project skin over the upstream FairyGUI Button, Controller and clipping widgets. */
export class AtlasUi {
 static ready=false;
 private static pending:Promise<void>|null=null;
 private static frames=new Map<string,SpriteFrame>();

 static load():Promise<void>{
  if(this.ready)return Promise.resolve();
  if(!this.pending)this.pending=Promise.all([
   new Promise<void>((resolve,reject)=>UIPackage.loadPackage('ui/fairygui/MainMenu',(error)=>error?reject(error):resolve())),
   ...['button-normal','button-hover','button-pressed','button-disabled','panel-frame','panel-surface','divider-horizontal','indicator-selected'].map(name=>this.frame('ui/quiet-bronze/'+name)),
  ]).then(()=>{this.ready=true;}).catch(error=>{this.pending=null;throw error;});
  return this.pending;
 }
 static frame(path:string,inset=0):Promise<SpriteFrame>{
  const cached=this.frames.get(path);if(cached)return Promise.resolve(cached);
  return UiSkin.frame(path,inset).then(frame=>{this.frames.set(path,frame);return frame;});
 }
 static place<T extends GObject>(parent:GComponent,item:T,name:string,x:number,y:number,w:number,h:number):T {
  item.name=name;item.node.name=name;item.setSize(w,h);item.setPosition(x,y);parent.addChild(item);return item;
 }
 static panel(parent:GComponent,name:string,x:number,y:number,w:number,h:number,color=ATLAS_COLORS.panel,border=true):GComponent {
  const item=this.place(parent,new GComponent(),name,x,y,w,h);item.opaque=true;
  this.fill(item,'Fill',0,0,w,h,color);
  if(border){this.image(item,'Surface','panel-surface',0,0,w,h,Color.WHITE,true);this.image(item,'Border','panel-frame',0,0,w,h,Color.WHITE,true);this.ornament(item,w,h);}
  return item;
 }
 static ornament(parent:GComponent,w:number,h:number):void {
  const ornament=this.place(parent,new GGraph(),'BronzeCornerwork',0,0,w,h);ornament.touchable=false;
  const g=ornament._content;g.lineWidth=.9;g.strokeColor=new Color(ATLAS_COLORS.line.r,ATLAS_COLORS.line.g,ATLAS_COLORS.line.b,180);
  for(const[cx,cy,sx,sy]of [[12,-12,1,-1],[w-12,-12,-1,-1],[12,-h+12,1,1],[w-12,-h+12,-1,1]]){
   const p=(x:number,y:number)=>({x:cx+x*sx,y:cy+y*sy});let a=p(0,36),b=p(0,0),c=p(36,0);g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.lineTo(c.x,c.y);g.stroke();
   a=p(5,25);b=p(5,5);c=p(25,5);g.moveTo(a.x,a.y);g.bezierCurveTo(b.x,b.y,b.x,b.y,c.x,c.y);g.stroke();
   a=p(8,16);b=p(16,8);g.moveTo(a.x,a.y);g.lineTo(b.x,b.y);g.stroke();const gem=p(3,3);g.fillColor=ATLAS_COLORS.gold;g.circle(gem.x,gem.y,1.7);g.fill();
  }
 }
 static fill(parent:GComponent,name:string,x:number,y:number,w:number,h:number,color:Color):GGraph {
  const item=this.place(parent,new GGraph(),name,x,y,w,h);item.touchable=false;item.drawRect(0,Color.TRANSPARENT,color);return item;
 }
 static image(parent:GComponent,name:string,asset:string,x:number,y:number,w:number,h:number,color:Color,sliced=false):GImage {
  const item=this.place(parent,new GImage(),name,x,y,w,h);item.touchable=false;
  const path=asset.includes('/')?asset:'ui/quiet-bronze/'+(asset==='divider'?'divider-horizontal':asset);
  // FairyGUI retains logical bounds and clipping; its native visual child uses source pixels.
  item._content.enabled=false;
  const skin=UiSkin.sprite(item.node,path,w,h,path.startsWith('ui/quiet-bronze/')?Color.WHITE:color,sliced||asset==='divider');skin.node.setPosition(w/2,-h/2);
  return item;
 }
 static text(parent:GComponent,value:string,x:number,y:number,w:number,h=36,size=18,color=ATLAS_COLORS.ink,center=false):GTextField {
  const item=this.place(parent,new GTextField(),'Text',x,y,w,h);item.autoSize=AutoSizeType.Shrink;item.font='SimSun';item.fontSize=size;item.color=color;item.align=center?HorizontalTextAlignment.CENTER:HorizontalTextAlignment.LEFT;item.verticalAlign=VerticalTextAlignment.CENTER;item.leading=Math.round(size*.4);item.text=value;return item;
 }
 static button(parent:GComponent,name:string,title:string,x:number,y:number,w:number,h:number,run:()=>void,active=false,size=18):GButton {
  const item=UIPackage.createObject('MainMenu','Button') as GButton;
  this.place(parent,item,name,x,y,w,h);item.opaque=true;item.sound=null;
  for(const key of ['n1','n2','n3']){
   const skin=item.getChild(key) as GImage;skin.alpha=0;skin.touchable=false;
  }
  const background=this.image(item,'QuietBronze','button-normal',0,0,w,h,Color.WHITE,true);item.setChildIndex(background,0);
  const wash=this.fill(item,'ActiveTeal',4,4,w-8,h-8,ATLAS_COLORS.active);item.setChildIndex(wash,1);wash.visible=active;
  const skin=background.node.children.find(node=>node.name.startsWith('Skin:'))!.getComponent(Sprite)!;
  const mark=this.image(item,'Selected','indicator-selected',10,(h-26)/2,12,26,Color.WHITE);mark.visible=active;
  const controller=item.getController('button');
  const refresh=()=>{if(item.isDisposed)return;const state=controller.selectedPage,selected=active||item.selected;mark.visible=selected;wash.visible=selected;skin.spriteFrame=this.frames.get('ui/quiet-bronze/button-'+(state.includes('disabled')?'disabled':state==='down'?'pressed':state==='over'||state==='selectedOver'?'hover':'normal'))!;};
  controller.onChanged(refresh);refresh();void Promise.resolve().then(refresh);
  const label=item.getTextField();label.font='Microsoft YaHei';label.autoSize=AutoSizeType.Shrink;label.setPosition(active?28:14,0);label.setSize(w-(active?42:28),h);label.fontSize=size;label.color=ATLAS_COLORS.ink;label.singleLine=true;item.title=title;
  item.onClick(run);return item;
 }
 static controller(parent:GComponent,name:string,pages:string[],selected:number):Controller {
  const controller=new Controller();controller.name=name;for(const page of pages)controller.addPage(page);parent.addController(controller);controller.selectedIndex=selected;return controller;
 }
 static radio(button:GButton,controller:Controller,index:number):void {button.mode=ButtonMode.Radio;button.relatedController=controller;button.relatedPageId=controller.getPageId(index);button.selected=controller.selectedIndex===index;}
}

export class AtlasViewport extends GComponent {
 constructor(){super();this.opaque=true;this.setupOverflow(OverflowType.Hidden);}
}
