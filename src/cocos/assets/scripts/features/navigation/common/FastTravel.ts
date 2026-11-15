import type {AreaDef,Point} from '../../../core/Contracts';
import {playableArea} from '../../journey/data/ChapterJourney';

export type Waypoint={id:string;name:string;area:string;point:Point};
/** One authored safe arrival per location. Ordinary exits never become destinations. */
export function authoredWaypoint(area:AreaDef):Waypoint|undefined {
 if(!playableArea(area.id))return;
 const checkpoint=area.objects.find(object=>object.action==='checkpoint');
 if(!checkpoint&&!area.checkpoint)return;
 const point=checkpoint??area.spawn;
 return {id:area.id,name:area.name,area:area.id,point:{x:point.x,z:point.z}};
}
export function waypointUnlocked(flags:Record<string,boolean>,area:AreaDef):boolean {
 // Old checkpoint proofs are migrated once by GameSession.restore.
 return !!authoredWaypoint(area)&&!!flags[`visited:${area.id}`]&&!!flags[`waypoint:${area.id}`];
}
