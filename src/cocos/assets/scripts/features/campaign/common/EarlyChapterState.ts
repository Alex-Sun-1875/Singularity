import type {GameState} from '../../../core/GameSession';

type State=Pick<GameState,'flags'|'progression'>;
/** Named newcomers have a physical reason to be in their eventual return area.
 * Completion leaves them there for revisits rather than respawning a duplicate. */
export function earlyNpcVisible(id:string,s:State):boolean {
 const f=s.flags;
 if(id==='early-npc-eina')return !!f['dg:letter-complete'];
 if(id==='early-npc-millwright')return !!f.workers_returned;
 if(id==='early-npc-repairs')return s.progression.secondChapter&&!!f['chapter2-side:forge:complete']&&!!f['dg:lamp-complete'];
 if(id==='early-npc-ledger')return s.progression.secondChapter&&!!f['field:arms-complete'];
 return true;
}
export type EarlyWorldKind='lamp'|'wheel'|'bench'|'switch'|'record';
export interface EarlyWorldState {id:string;eventId:string;kind:EarlyWorldKind;visible:boolean;complete:boolean}
const stateProps=new Set(['side-lantern-lamp','side-water-turn','c1-town-return','c2-stop-west','c2-stop-east','field-lamp-fallback','side-repairs-lamp','side-forge-bench-test','side-ledger-settle','side-repairs-settle','c2-pressure-return','c2-contact-failsafe','c2-post-settle']);
export const isEarlyStateProp=(eventId:string|undefined)=>!!eventId&&stateProps.has(eventId);
/** Small content-owned state descriptions; presentation never changes a flag,
 * collision, path, reward, light budget or task completion. */
export function earlyWorldStates(area:string,f:Record<string,boolean>):EarlyWorldState[]{
 const has=(key:string)=>!!f[key];
 const state=(id:string,eventId:string,kind:EarlyWorldKind,visible:boolean,complete:boolean):EarlyWorldState=>({id,eventId,kind,visible,complete});
 switch(area){
  case 'S06':return [state('camp-lamp','side-lantern-lamp','lamp',has('dg:letter-complete'),has('early:side-lantern-lamp'))];
  case 'S07':return [state('mill-wheel','side-water-turn','wheel',has('early:side-water-request'),has('early:side-water-turn'))];
  case 'S01-T6':return [state('return-bench','c1-town-return','bench',has('workers_returned'),has('early:c1-town-return'))];
  case 'H03':return [
   state('workshop-west','c2-stop-west','switch',has('journey:task:highland-workers'),has('early:c2-stop-west')),
   state('workshop-east','c2-stop-east','switch',has('early:c2-stop-west'),has('early:c2-stop-east')),
   state('backup-lamp','field-lamp-fallback','lamp',has('dg:lamp-steady'),has('early:field-lamp-fallback')),
   state('repaired-lamp','side-repairs-lamp','lamp',has('early:side-repairs-support'),has('early:side-repairs-lamp')),
  ];
  case 'H01':return [
   state('public-bench','side-forge-bench-test','bench',has('chapter2-side:forge:complete'),has('early:side-forge-bench-test')),
   state('corrected-register','side-ledger-settle','record',has('field:arms-complete'),has('early:side-ledger-settle')),
   state('repair-return','side-repairs-settle','bench',has('early:side-repairs-request'),has('early:side-repairs-settle')),
  ];
  case 'U1-07':return [state('furnace-disconnect','c2-pressure-return','switch',has('u107_furnace_stopped'),has('early:c2-pressure-return'))];
  case 'U1-08':return [state('contact-disconnect','c2-contact-failsafe','switch',has('m4_contact'),has('early:c2-contact-failsafe'))];
  case 'H07':return [state('outpost-record','c2-post-settle','record',has('journey:task:highland-ridge'),has('early:c2-post-settle'))];
  default:return [];
 }
}
