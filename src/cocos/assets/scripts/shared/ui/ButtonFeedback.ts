import {_decorator,ButtonComponent as Button,Component,EventTouch,Node,UITransform} from 'cc';

const {ccclass}=_decorator;
export type ButtonFeedbackState='idle'|'hover'|'pressed';

/** State only: callers retain their native Button, hit region and artwork. */
@ccclass('ButtonFeedback')
export class ButtonFeedback extends Component {
 private button:Button|null=null;
 private paint:((state:ButtonFeedbackState)=>void)|null=null;
 private hovered=false;
 private pressed=false;
 private touching=false;
 private state:ButtonFeedbackState='idle';
 private listening=false;

 configure(button:Button,paint:(state:ButtonFeedbackState)=>void):this {
  this.button=button;this.paint=paint;
  if(!this.listening){
   this.listening=true;
   this.node.on(Node.EventType.MOUSE_ENTER,this.enter,this);
   this.node.on(Node.EventType.MOUSE_LEAVE,this.leave,this);
   this.node.on(Node.EventType.TOUCH_START,this.press,this);
   this.node.on(Node.EventType.TOUCH_MOVE,this.move,this);
   this.node.on(Node.EventType.TOUCH_END,this.end,this);
   this.node.on(Node.EventType.TOUCH_CANCEL,this.reset,this);
  }
  this.reset();return this;
 }
 /** Repaint after a visual resize or an explicit interactable change. */
 refresh():void {this.apply(true);}
 reset():void {
  this.hovered=false;this.pressed=false;this.touching=false;this.state='idle';this.draw('idle');
  if(this.enabled)this.enabled=false;
 }
 private available():boolean {
  return !!this.node?.isValid&&!!this.button?.isValid&&this.button.enabled&&this.button.interactable&&this.node.activeInHierarchy;
 }
 private apply(force=false):void {
  if(!this.available()){this.reset();return;}
  const next:ButtonFeedbackState=this.pressed?'pressed':this.hovered?'hover':'idle';
  if(force||next!==this.state){this.state=next;this.draw(next);}
  // Idle buttons do not need per-frame polling. Node listeners still receive input.
  this.enabled=next!=='idle'||this.touching;
 }
 private draw(state:ButtonFeedbackState):void {if(this.node?.isValid)this.paint?.(state);}
 private enter():void {if(this.available()){this.hovered=true;this.apply();}}
 private leave():void {this.hovered=false;this.pressed=false;this.apply();}
 private press():void {if(this.available()){this.touching=true;this.pressed=true;this.apply();}}
 private move(event:EventTouch):void {
  if(!this.touching)return;
  if(!this.available()){this.reset();return;}
  // Match Cocos Button: hitTest consumes screen coordinates, not UI coordinates.
  this.pressed=this.node.getComponent(UITransform)?.hitTest(event.getLocation(),event.windowId)??false;
  if(!this.pressed)this.hovered=false;
  this.apply();
 }
 private end():void {this.touching=false;this.pressed=false;this.apply();}
 update():void {if(!this.available())this.reset();}
 onDisable():void {if(this.state!=='idle'||this.hovered||this.pressed||this.touching)this.reset();}
 onDestroy():void {this.node.targetOff(this);this.paint=null;this.button=null;}
}

export function bindButtonFeedback(node:Node,button:Button,paint:(state:ButtonFeedbackState)=>void):ButtonFeedback {
 return (node.getComponent(ButtonFeedback)??node.addComponent(ButtonFeedback)).configure(button,paint);
}
