export interface Point { x: number; z: number }
export interface Obstacle extends Point { width: number; depth: number; height: number; kind?: string }
export interface Building extends Obstacle { name: string; style: 'inn'|'house'|'tower'|'mill'|'tent'|'ruin'|'workshop'|'gate'|'barn'; rotation?: number; enter?: string }
export interface ExitDef extends Point { id: string; to: string; label: string; entry: Point; requires?: string; unlock?: string; requiredLevel?:number }
export interface InteractionDef extends Point {
  id: string; label: string; action: string; description: string; radius?: number;
  actor?: string; actorModel?:string; npcId?:string; item?: string; amount?: number; merchant?: string; evidence?: string; check?:string; eventId?:string;
}
export interface EnemySpawn extends Point { id: string; kind: 'raider'|'shield'|'archer'|'captain'; hp?: number; contentId?:string; level?:number; bossId?:string; templateId?:string; respawnSeconds?:number; packId?:string;lootChapter?:number; trainingDummy?:boolean; trainingAttacks?:boolean; trainingEnemy?:boolean }
export interface AreaDef {
  id: string; name: string; subtitle: string; kind: 'town'|'wild'|'camp'|'ruin'|'underground'|'interior';
  palette: 'meadow'|'forest'|'stone'|'marsh'|'cave'|'warm';
  width: number; depth: number; spawn: Point; atlas: Point;
  exits: ExitDef[]; objects: InteractionDef[]; buildings: Building[]; obstacles: Obstacle[]; enemies: EnemySpawn[];
  checkpoint?: boolean;
  recommendedLevel?:number; campaignRegion?:string;
}
export interface InputFrame { x: number; z: number; aim?: number; target?:Point; attack?: boolean; dash?: boolean; push?: boolean; skill?: boolean; spell?: 0|1; combatSlot?:0|1|2|3; ultimate?:boolean; healSkill?:boolean }
export interface WorldQuery {
  move(from: Point, delta: Point, radius: number): Point;
  visible(from: Point, to: Point): boolean;
  height(point: Point): number;
  path?(from: Point, to: Point): Point[];
  /** Repair an actor embedded in scenery when entering/restoring a scene.
   * Return the original point when clear, or undefined if no safe repair exists. */
  recoverPosition?(point: Point, radius: number): Point | undefined;
  /** Optional presentation check for placing visible reinforcement squads.
   * Collision, line of sight and damage continue to use their world queries. */
  inView?(point: Point): boolean;
}
export interface GameEvent { type: string; text?: string; id?: string; at?: Point; value?: number; [key: string]: unknown }
export interface CombatSkillEvent extends GameEvent {
 type:'skill_cast'|'skill_release'|'skill_segment'|'skill_hit'|'skill_status'|'skill_zone'|'skill_end';
 skillId:string; family:string; rank:number; castId:string; shape:string;
 from:Point; to?:Point; sourceId?:string; targetId?:string; segment:number; duration?:number;
 radius?:number; width?:number; length?:number; depth?:number; angle?:number; angleDegrees?:number;anglesDegrees?:number[];
 geometry?:import('../features/combat/data/PureSkills').SkillGeometry; projectileId?:string; child?:boolean;
}
/** Presentation intent only: these fields never filter collisions or choose hits. */
export interface AttackFeedbackMetadata {
 feedbackTargetId?:string; feedbackTarget?:Point; feedbackReported?:boolean;
 feedbackActionId?:string; feedbackFailure?:'blocked'|'expired';
}
export interface SkillProjectileMetadata extends AttackFeedbackMetadata {
 skillId?:string; rank?:number; castId?:string; segment?:number; targetId?:string; child?:boolean;
 from?:Point; previousPosition?:Point; frozenPath?:Point[]; pathProgress?:number; pathLength?:number; width?:number;
 chainOrigin?:Point;
}
