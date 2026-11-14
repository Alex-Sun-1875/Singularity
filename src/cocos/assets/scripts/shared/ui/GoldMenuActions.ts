import {_decorator,Component,isValid,Node,UITransform} from 'cc';
import {GoldMenuButton,type GoldMenuButtonOptions} from './GoldMenuButton';
import {UI_FRAME_LAYOUT,UI_MENU_BUTTON} from './UiChrome';

const {ccclass,requireComponent}=_decorator;
export interface GoldMenuAction {label:string;action:string;primary?:boolean;disabled?:boolean;height?:number}
export interface GoldMenuActionsLayout {width:number;height:number;gap?:number;unit?:number;visualHeight?:number;visualGap?:number;pixelScale?:number;fontSize?:number;wrap?:boolean}

/** A centered stack of data-driven actions. Owners retain routing and backdrops. */
@ccclass('GoldMenuActions')
@requireComponent(UITransform)
export class GoldMenuActions extends Component {
 loaded=false;
 ready:Promise<void>=Promise.resolve();
 private owned:Node[]=[];
 private version=0;
 configure(actions:readonly GoldMenuAction[],layout:GoldMenuActionsLayout,activate:(action:string)=>void){
  const version=++this.version,u=layout.unit??1,gap=layout.gap??UI_FRAME_LAYOUT.gap*u,heights=actions.map(a=>a.height??layout.height),height=heights.reduce((sum,h)=>sum+h,0)+Math.max(0,actions.length-1)*gap;
  for(const node of this.owned){node.removeFromParent();node.destroy();}this.owned=[];this.loaded=false;
  const visuals=heights.map(h=>layout.visualHeight??Math.max(UI_MENU_BUTTON.visualHeight*u,h-14*u));
  this.node.getComponent(UITransform)!.setContentSize(layout.width,height);const buttons:GoldMenuButton[]=[];let top=height/2,visualTop=(visuals.reduce((s,h)=>s+h,0)+Math.max(0,actions.length-1)*(layout.visualGap??gap))/2;
  actions.forEach((action,i)=>{
   const node=new Node(action.action);node.layer=this.node.layer;this.node.addChild(node);this.owned.push(node);const center=top-heights[i]/2;node.setPosition(0,center,0);top-=heights[i]+gap;
   // Tighten the painted stack without moving or overlapping native hit targets.
   const inset=Math.max(0,(heights[i]-visuals[i])/2-u),desired=visualTop-visuals[i]/2-center,offset=layout.visualGap===undefined?0:Math.max(-inset,Math.min(inset,desired));visualTop-=visuals[i]+(layout.visualGap??gap);
   const options:GoldMenuButtonOptions={label:action.label,width:layout.width,height:heights[i],unit:u,primary:action.primary,disabled:action.disabled,wrap:layout.wrap,fontSize:layout.fontSize,pixelScale:layout.pixelScale,visualHeight:visuals[i],visualOffsetY:offset};
   const button=node.addComponent(GoldMenuButton);button.configure(options,()=>activate(action.action));buttons.push(button);
  });
  this.ready=Promise.all(buttons.map(b=>b.ready)).then(()=>{if(isValid(this,true)&&version===this.version)this.loaded=buttons.every(b=>b.loaded);});
 }
 onDestroy(){this.version++;}
}
