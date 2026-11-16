/** Future cosmetic authorization. Rendering owns application; cosmetics carry no combat stats. */
export type AppearanceTarget='character'|'weapon';
export interface AppearanceDefinition {
 readonly appearanceId:string;
 readonly target:AppearanceTarget;
 readonly nameKey:string;
 readonly resourceId:string;
}
export interface AppearanceAuthorization {
 readonly appearanceId:string;
 readonly source:'achievement'|'purchase';
 readonly sourceId:string;
}
export interface AppearanceSnapshot {
 readonly accountId:string;
 readonly revision:number;
 readonly authorizations:readonly AppearanceAuthorization[];
 readonly equipped:Readonly<Partial<Record<AppearanceTarget,string>>>;
}
/** No implementation is registered until identity, authorization and assets are available. */
export interface AppearanceService {
 restore():Promise<AppearanceSnapshot>;
 apply(appearanceId:string):Promise<AppearanceSnapshot>;
 remove(target:AppearanceTarget):Promise<AppearanceSnapshot>;
}
