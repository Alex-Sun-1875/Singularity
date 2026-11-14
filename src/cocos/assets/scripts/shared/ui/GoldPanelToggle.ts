import {_decorator,Component,isValid,Label,Node,UITransform} from 'cc';
import {applyRpgFont} from './RpgFont';
import {UI_SETTINGS_REFERENCE as R} from './UiChrome';
import {UiSkin} from './UiSkin';
import {UI_COLORS as C} from './UiTheme';
import type {GoldPanelVariant} from './GoldPanelShell';

const {ccclass,requireComponent}=_decorator;
export interface GoldPanelToggleOptions {width:number;height:number;on:boolean;label?:string;unit?:number;variant?:GoldPanelVariant}

/** Rendering-only switch: the owning row keeps the single, full-size hit target. */
@ccclass('GoldPanelToggle')
@requireComponent(UITransform)
export class GoldPanelToggle extends Component {
 loaded=false;
 loadError='';
 ready:Promise<void>=Promise.resolve();
 private owned:Node[]=[];
 private version=0;
 configure(o:GoldPanelToggleOptions):void {
  const version=++this.version,reference=o.variant==='settings',u=reference?o.width/R.toggleWidth:o.unit??1;this.loaded=false;this.loadError='';
  for(const n of this.owned){n.removeFromParent();n.destroy();}this.owned=[];
  this.node.getComponent(UITransform)!.setContentSize(o.width,o.height);
  const art=this.part('ToggleArtwork',o.width,o.height);UiSkin.toggle(art,o.width,o.height,o.on,u,reference);
  const text=this.part('ToggleState',reference?28*u:24*u,o.height).addComponent(Label);
  text.node.setPosition(reference?-R.toggleTextX*u:(o.on?-1:1)*11*u,0);text.string=o.label??(o.on?'开':'关');text.color=C.ink;text.fontSize=(reference?R.toggleStateSize:14)*u;text.lineHeight=text.fontSize*1.4;text.horizontalAlign=Label.HorizontalAlign.CENTER;text.verticalAlign=Label.VerticalAlign.CENTER;text.enableWrapText=true;text.overflow=Label.Overflow.CLAMP;applyRpgFont(text);
  this.ready=Promise.all(['double-gold-toggle-track-v6','double-gold-toggle-thumb-v6'].map(id=>UiSkin.frame('ui/quiet-bronze/'+id,0,this.node))).then(()=>{if(isValid(this,true)&&version===this.version)this.loaded=true;}).catch(error=>{if(isValid(this,true)&&version===this.version){this.loadError=String(error);console.warn('Gold panel toggle unavailable:',error);}});
 }
 private part(name:string,width:number,height:number):Node {const n=new Node(name);n.layer=this.node.layer;this.node.addChild(n);n.addComponent(UITransform).setContentSize(width,height);this.owned.push(n);return n;}
 onDestroy(){this.version++;}
}
