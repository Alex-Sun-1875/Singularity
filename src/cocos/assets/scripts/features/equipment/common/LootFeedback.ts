/** Shared drop semantics; presentation timers never delay pickup or delete loot. */
export const EQUIPMENT_DROP_NOTICE_SECONDS=24;
export function equipmentDropPriority(quality:string):number {
 return quality==='神器'?3:quality==='传奇'?2:quality==='史诗'?1:0;
}
export function highlightedEquipment(quality:string):boolean{return equipmentDropPriority(quality)>0;}
