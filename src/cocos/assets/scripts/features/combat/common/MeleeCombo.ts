/** Shared rules/presentation timing. A complete chain keeps the former 3 x .44s budget. */
export const MELEE_COMBO=[
 {stage:1,duration:.38,release:.12,active:.10,clip:'attack_sword',reverse:false,strength:1},
 {stage:2,duration:.38,release:.12,active:.10,clip:'attack_sword_2',reverse:true,strength:1.3},
 {stage:3,duration:.56,release:.22,active:.10,clip:'attack_sword_3',reverse:false,strength:1.9},
] as const;
export const meleeCombo=(stage=1)=>MELEE_COMBO[Math.max(0,Math.min(2,Math.floor(stage)-1))];
export const MELEE_CHAIN_GAP=.45,MELEE_INPUT_BUFFER=.12;

/** Transient input state, deliberately outside save data. */
export class MeleeCombo {
 private next=1;private until=-1;private weapon='';private area='';private bufferedUntil=-1;
 begin(time:number,weapon:string,area:string){const stage=time<=this.until&&weapon===this.weapon&&area===this.area?this.next:1;this.weapon=weapon;this.area=area;this.bufferedUntil=-1;return meleeCombo(stage);}
 complete(stage:number,time:number){if(!this.weapon)return;this.next=stage%3+1;this.until=time+MELEE_CHAIN_GAP;}
 buffer(time:number){this.bufferedUntil=time+.20;}
 queued(time:number){return time<=this.bufferedUntil;}
 reset(){this.next=1;this.until=-1;this.bufferedUntil=-1;this.weapon='';this.area='';}
}
