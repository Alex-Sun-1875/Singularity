import {game,Game,screen} from 'cc';
import {readTapAPI} from './RuntimePlatform';

type MenuRect=Readonly<{left:number;top:number;right:number;bottom:number;windowWidth:number;windowHeight:number}>;
type Metrics=Readonly<{windowSize:Readonly<{width:number;height:number}>;devicePixelRatio:number;menuRect:MenuRect|null}>;
let snapshot:Metrics|undefined;
let owners=0;
let revision=0;
const invalidate=()=>{snapshot=undefined;revision++;};
let releaseMenuChanges:(()=>void)|undefined;

function read():Metrics{
 // The minigame getters can synchronously cross the native bridge. Copy once;
 // never retain the engine's mutable Size or query it from every presenter.
 if(!snapshot||owners===0){
  const size=screen.windowSize;
  let menuRect:MenuRect|null=null;
  // TapTap's installed official plugin declares this synchronous menu API.
  // Its rectangle and getWindowInfo dimensions use window logical pixels.
  const tap=readTapAPI<{getMenuButtonBoundingClientRect?():{left:number;top:number;right:number;bottom:number};getWindowInfo?():{windowWidth:number;windowHeight:number}}>();
  try{
   const menu=tap?.getMenuButtonBoundingClientRect?.(),window=tap?.getWindowInfo?.();
   if(menu&&window&&[menu.left,menu.top,menu.right,menu.bottom,window.windowWidth,window.windowHeight].every(Number.isFinite)&&menu.right>menu.left&&menu.bottom>menu.top&&window.windowWidth>0&&window.windowHeight>0)
    menuRect=Object.freeze({...menu,windowWidth:window.windowWidth,windowHeight:window.windowHeight});
  }catch{/* Older hosts retain the Cocos safe rectangle and reserved header corner. */}
  snapshot=Object.freeze({windowSize:Object.freeze({width:size.width,height:size.height}),devicePixelRatio:screen.devicePixelRatio,menuRect});
 }
 return snapshot;
}

export const viewportMetrics={
 get revision(){return revision;},
 get windowSize(){return read().windowSize;},
 get devicePixelRatio(){return read().devicePixelRatio;},
 get menuRect(){return read().menuRect;},
};

/** Retain before constructing UI; release when the owning scene is destroyed. */
export function retainViewportMetrics():()=>void{
 if(owners++===0){
  invalidate();
  screen.on('window-resize',invalidate);
  game.on(Game.EVENT_SHOW,invalidate);
  const tap=readTapAPI<{onMenuButtonBoundingClientRectWeightChange?(run:()=>void):void;offMenuButtonBoundingClientRectWeightChange?(run:()=>void):void}>();
  if(tap?.onMenuButtonBoundingClientRectWeightChange&&tap.offMenuButtonBoundingClientRectWeightChange){
   try{tap.onMenuButtonBoundingClientRectWeightChange(invalidate);releaseMenuChanges=()=>tap.offMenuButtonBoundingClientRectWeightChange!(invalidate);}catch{/* Optional on older hosts. */}
  }
 }
 let released=false;
 return()=>{
  if(released)return;released=true;
  if(--owners===0){
   screen.off('window-resize',invalidate);
   game.off(Game.EVENT_SHOW,invalidate);
   releaseMenuChanges?.();releaseMenuChanges=undefined;
   invalidate();
  }
 };
}
