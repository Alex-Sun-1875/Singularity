import {Director,Node,SpriteFrame,Texture2D,RenderTexture,director,isValid} from 'cc';
type Entry={promise:Promise<SpriteFrame>;owners:Set<Node>;permanent:boolean;frame?:SpriteFrame;texture?:Texture2D|RenderTexture;queued:boolean};
/** Node/page leases for dynamic frames; retire only after their last draw. */
export class FrameCache {
 private entries=new Map<string,Entry>();private owners=new Map<Node,Set<string>>();private observed=new WeakSet<Node>();
 getReady(key:string,owner:Node):SpriteFrame|undefined{const entry=this.entries.get(key);if(!entry?.frame?.isValid||!isValid(owner,true))return;this.attach(key,entry,owner);return entry.frame;}
 get(key:string,owner:Node|undefined,load:()=>SpriteFrame|Promise<SpriteFrame>):Promise<SpriteFrame>{
  if(owner&&!isValid(owner,true))return Promise.reject(new Error('Frame owner was destroyed'));
  let entry=this.entries.get(key);
  if(!entry){
   entry={promise:null,owners:new Set(),permanent:!owner,queued:false};this.entries.set(key,entry);const current=entry;
   const accept=(frame:SpriteFrame)=>{
    const texture=frame.texture as Texture2D|RenderTexture;if(texture){texture.addRef();current.texture=texture;}current.frame=frame;
    if(this.entries.get(key)!==current){frame.destroy();texture?.decRef();}else this.retire(key,current);return frame;
   };
   try{const result=load();current.promise=result instanceof SpriteFrame?Promise.resolve(accept(result)):result.then(accept,error=>{if(this.entries.get(key)===current)this.entries.delete(key);throw error;});}
   catch(error){this.entries.delete(key);current.promise=Promise.reject(error);}
  }
  if(!owner)entry.permanent=true;
  else this.attach(key,entry,owner);
  return entry.promise;
 }
 private attach(key:string,entry:Entry,owner:Node){
   entry.owners.add(owner);let keys=this.owners.get(owner);if(!keys){keys=new Set();this.owners.set(owner,keys);}keys.add(key);
   if(!this.observed.has(owner)){this.observed.add(owner);owner.once(Node.EventType.NODE_DESTROYED,()=>this.releaseOwner(owner));}
 }
 releaseOwner(owner:Node){const keys=this.owners.get(owner);if(!keys)return;this.owners.delete(owner);for(const key of keys){const entry=this.entries.get(key);if(entry){entry.owners.delete(owner);this.retire(key,entry);}}}
 private retire(key:string,entry:Entry){
  if(entry.permanent||entry.owners.size||entry.queued||!entry.frame)return;entry.queued=true;
  director.once(Director.EVENT_AFTER_DRAW,()=>{entry.queued=false;if(this.entries.get(key)!==entry||entry.permanent||entry.owners.size)return;this.entries.delete(key);entry.frame?.destroy();entry.texture?.decRef();});
 }
 inspect(){return {entries:this.entries.size,owners:this.owners.size,textureBytes:Array.from(new Set(Array.from(this.entries.values(),entry=>entry.texture))).reduce((n,t)=>n+(t?.getGFXTexture()?.size??0),0)};}
 dispose(){for(const entry of this.entries.values()){entry.frame?.destroy();entry.texture?.decRef();}this.entries.clear();this.owners.clear();}
}
