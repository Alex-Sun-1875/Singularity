import {gameResources as resources} from '../../../shared/assets/GameResources';
import {JsonAsset,Node,Prefab} from 'cc';
import {NativeActorMaterials,type NativeActorMaterialManifest} from './NativeActorMaterials';
import {EQUIPMENT} from '../../equipment/data/Equipment';

/** Physical variants are separate prefabs, not equipment names on one mesh. */
export const EQUIPMENT_WEAPON_RESOURCES:Readonly<Record<string,string>>={
 W01:'design-w01',W02:'design-w02',W03:'design-w03',W04:'design-w04',W05:'design-w05',W06:'design-w06',
 W07:'design-w07',W08:'design-w08',W09:'design-w09',W10:'design-w10',
 W11:'design-w11',W12:'design-w12',W13:'design-w13',W14:'design-w14',
 'DR2-03':'design-dr2-03','DR3-03':'design-dr3-03','DR4-03':'design-dr4-03','DU1-04':'design-du1-04','DU2-04':'design-du2-04',
 DE02:'design-de02',DE05:'design-de05',DE06:'design-de06',L01:'design-l01',L02:'design-l02',
};
export const WEAPON_VARIANT_PREFIX='WeaponVariant:';

export function weaponAttachmentKind(id:string):'sword'|'greatsword'|'bow'|'staff' {
 const family=EQUIPMENT[id]?.kind,art=EQUIPMENT[id]?.artSource??id;return family==='bow'?'bow':family==='staff'?'staff':art==='L01'?'greatsword':'sword';
}
export function playerWeaponVariants(kind:string):string[]{return Object.entries(EQUIPMENT_WEAPON_RESOURCES).filter(([id])=>weaponAttachmentKind(id)===kind).map(([,resource])=>resource);}

/** Also used by CharacterPreview after cloning a paused equipped actor. */
export function selectEquipmentWeaponVariants(root:Node,weapon:string):void {
 const resource=EQUIPMENT_WEAPON_RESOURCES[EQUIPMENT[weapon]?.artSource??weapon]??EQUIPMENT_WEAPON_RESOURCES.W01;
 const visit=(node:Node)=>{
  if(node.name.startsWith(WEAPON_VARIANT_PREFIX))node.active=node.name===WEAPON_VARIANT_PREFIX+resource;
  for(const child of node.children)visit(child);
 };
 visit(root);
}

type WeaponManifest={props:Record<string,NativeActorMaterialManifest&{materials:NonNullable<NativeActorMaterialManifest['materials']>;stowedResource?:string}>};

/** Reuses the existing native PBR adapter on the attached prop instances. */
export class WeaponMaterials {
 private native=new NativeActorMaterials();
 private manifest:Promise<WeaponManifest>|null=null;
 private static readManifest():Promise<WeaponManifest>{return new Promise<WeaponManifest>((resolve,reject)=>resources.load('actors/props-native/manifest',JsonAsset,(error,asset)=>error?reject(error):resolve(asset.json as WeaponManifest)));}
 private load():Promise<WeaponManifest>{
  if(!this.manifest)this.manifest=WeaponMaterials.readManifest();
  return this.manifest;
 }
 static async preloadPlayer(weapon:string,quiver?:string){
  const manifest=await this.readManifest(),variant=EQUIPMENT_WEAPON_RESOURCES[EQUIPMENT[weapon]?.artSource??weapon]??EQUIPMENT_WEAPON_RESOURCES.W01;
  const names=new Set([variant,manifest.props[variant]?.stowedResource??variant,'arrow',...(quiver?[quiver]:[])]);
  await Promise.all([
   ...Array.from(names,name=>new Promise<Prefab>((resolve,reject)=>resources.load(`actors/props-native/${name}/${name}/${name}`,Prefab,(error,asset)=>error?reject(error):resolve(asset)))),
   NativeActorMaterials.preload({materials:Array.from(names).flatMap(name=>manifest.props[name]?.materials??[])}),
  ]);
 }
 async apply(model:Node,resource:string):Promise<void>{
  const manifest=await this.load(),record=manifest.props[resource];
  if(!record)throw new Error('Missing redesigned weapon material record: '+resource);
  const report=await this.native.apply(model,{runtimeProfile:'native-kit-v1',materials:record.materials});
  if(report.unmatched.length)throw new Error('Weapon PBR material names do not match '+resource+': '+report.unmatched.join(', '));
 }
 async stowedResource(resource:string):Promise<string>{return (await this.load()).props[resource]?.stowedResource??resource;}
 destroy(){this.native.destroy();}
}
