export interface AnimationModeMemory {realtime:boolean}
/** Keep the real-time evaluator through short action gaps while combat is ready.
 * A safe exploration frame releases it back to Cocos' baked animation path. */
export function useBakedAnimation(memory:AnimationModeMemory,needsRealtime:boolean,combatReady:boolean):boolean {
 memory.realtime=needsRealtime||combatReady&&memory.realtime;
 return !memory.realtime;
}
