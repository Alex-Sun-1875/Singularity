import {_decorator,ButtonComponent as Button,Component,isValid,Label,Node,Sprite,UITransform} from 'cc';
import {UI_MENU_BUTTON as S} from './UiChrome';
import {UI_COLORS as C} from './UiTheme';
import {FeedbackView as F} from './FeedbackView';
import {UiSkin} from './UiSkin';
import {applyRpgFont} from './RpgFont';

const {ccclass,requireComponent}=_decorator;
export interface GoldMenuButtonOptions {
 label:string;width:number;height:number;
 /** Cocos design units per logical screen unit. Input bounds stay on the root. */
 unit?:number;visualHeight?:number;visualOffsetY?:number;pixelScale?:number;fontSize?:number;
 primary?:boolean;disabled?:boolean;wrap?:boolean;
}

/** Shared chamfered metal action with native Cocos input and live text. */
@ccclass('GoldMenuButton')
@requireComponent(UITransform)
export class GoldMenuButton extends Component {
 loaded=false;
 loadError='';
 ready:Promise<void>=Promise.resolve();
 private skin:Sprite|undefined;
 private caption:Label|undefined;
 private button:Button|undefined;
 private activate:()=>void=()=>{};
 private version=0;
 configure(options:GoldMenuButtonOptions,activate:()=>void){
  const u=options.unit??1,w=options.width,h=options.height,visual=options.visualHeight??Math.min(S.visualHeight*u,h-8*u),pixels=options.pixelScale??Math.min(S.visualHeight*u,visual)/S.height;
  this.node.getComponent(UITransform)!.setContentSize(w,h);this.activate=activate;
  if(!this.skin){
   const face=this.part('GoldMenuSkin');this.skin=face.addComponent(Sprite);this.skin.sizeMode=Sprite.SizeMode.CUSTOM;this.skin.type=Sprite.Type.SLICED;this.skin.trim=false;
   this.caption=this.part('GoldMenuCaption').addComponent(Label);this.caption.horizontalAlign=Label.HorizontalAlign.CENTER;this.caption.verticalAlign=Label.VerticalAlign.CENTER;applyRpgFont(this.caption);
   this.button=this.node.getComponent(Button)??this.node.addComponent(Button);this.button.target=face;this.button.transition=Button.Transition.COLOR;this.button.duration=.1;
   this.node.on(Button.EventType.CLICK,this.clicked,this);
  }
  this.skin.node.getComponent(UITransform)!.setContentSize(w/pixels,visual/pixels);this.skin.node.setScale(pixels,pixels,1);
  this.skin.node.setPosition(0,options.visualOffsetY??0);this.caption!.node.setPosition(0,options.visualOffsetY??0);
  const label=this.caption!;label.node.getComponent(UITransform)!.setContentSize(Math.max(1,w-16*u),h);label.string=options.label;label.fontSize=options.fontSize??S.fontSize*pixels;label.lineHeight=label.fontSize*1.4;label.enableWrapText=!!options.wrap;label.overflow=Label.Overflow.CLAMP;
  this.setInteractable(!options.disabled);
  const version=++this.version;this.loaded=false;this.loadError='';
  this.ready=UiSkin.frame('ui/quiet-bronze/'+(options.primary?S.primary:S.secondary),0,this.node).then(frame=>{if(isValid(this,true)&&version===this.version){this.skin!.spriteFrame=frame;this.loaded=true;}}).catch(error=>{if(isValid(this,true)&&version===this.version){this.loadError=String(error);console.warn('Gold menu button skin unavailable:',error);}});
 }
 setLabel(value:string){if(this.caption)this.caption.string=value;}
 setInteractable(enabled:boolean){if(this.button)this.button.interactable=enabled;if(this.caption)this.caption.color=enabled?C.ink:F.color('text.disabled');}
 private part(name:string){const node=new Node(name);node.layer=this.node.layer;this.node.addChild(node);node.addComponent(UITransform);return node;}
 private clicked(){if(this.button?.interactable)this.activate();}
 onDestroy(){this.version++;this.node.off(Button.EventType.CLICK,this.clicked,this);}
}
