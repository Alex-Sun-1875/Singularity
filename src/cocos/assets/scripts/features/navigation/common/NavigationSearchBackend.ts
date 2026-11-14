import type {Obstacle,Point} from '../../../core/Contracts';

/** The scene's immutable collider footprints; no engine objects cross this API. */
export interface NavigationSearchMap {
 readonly width:number;
 readonly depth:number;
 readonly obstacles:readonly Obstacle[];
}
export interface NavigationSearchBackend {
 /** null means unavailable/unsupported: run the existing TypeScript search. */
 search(map:NavigationSearchMap,start:Point,end:Point):Point[]|null;
 visible?(map:NavigationSearchMap,start:Point,end:Point,radius:number):boolean|null;
 visibleMany?(map:NavigationSearchMap,start:Point,targets:readonly Point[],radius:number):Uint8Array|null;
 connector?(map:NavigationSearchMap,point:Point):Point[]|null;
 simplify?(map:NavigationSearchMap,route:readonly Point[]):Point[]|null;
 release(map:NavigationSearchMap):void;
 reset():void;
}
