export class TouchOwnership {
 private owners=new Map<number,string>();
 private movement={x:0,z:0};
 begin(id:number,control:string):boolean {
   if(this.owners.has(id))return false;
   if(control==='move'&&Array.from(this.owners.values()).includes('move'))return false;
   if(control!=='move'&&Array.from(this.owners.values()).some(v=>v!=='move'))return false;
   this.owners.set(id,control);return true;
 }
 move(id:number,x:number,z:number):void {
   if(this.owners.get(id)!=='move')return;
   const length=Math.hypot(x,z); const scale=length>.15?Math.min(1,length)/length:0;
   this.movement={x:x*scale,z:z*scale};
 }
 end(id:number,cancelled:boolean):string|undefined {
   const owner=this.owners.get(id);this.owners.delete(id);
   if(owner==='move')this.movement={x:0,z:0};
   return cancelled||owner==='move'?undefined:owner;
 }
 owner(id:number){return this.owners.get(id);}
 vector(){return {...this.movement};}
 clear(){this.owners.clear();this.movement={x:0,z:0};}
}
