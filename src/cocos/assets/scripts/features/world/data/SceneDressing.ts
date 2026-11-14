/** Composition only. Gameplay locations and immutable WorldData remain authoritative. */
export type ScenePlacement={
 key:string;x:number;z:number;width:number;depth:number;height:number;yaw?:number;
 dressing?:'supper'|'ledger'|'sideboard';
};

// One near-side table and one smaller door-side group break the old symmetric
// arrangement. The centre aisle and the approach to Mira stay open.
export const INN_OPENING:readonly ScenePlacement[]=[
 {key:'round-table',x:-2.8,z:-9.8,width:1.9,depth:1.9,height:.79,dressing:'supper'},
 {key:'stool',x:-4.12,z:-9.5,width:.58,depth:.58,height:.46,yaw:12},
 {key:'chair',x:-2.35,z:-8.35,width:.68,depth:.72,height:1.08,yaw:12},
 {key:'round-table',x:1.8,z:-2.8,width:1.65,depth:1.65,height:.77,dressing:'ledger'},
 {key:'stool',x:2.96,z:-2.35,width:.58,depth:.58,height:.46,yaw:35},
 {key:'stool',x:.7,z:-1.85,width:.58,depth:.58,height:.46,yaw:-15},
 // Conversation-side service furniture sits clear of Mira and the sample/cup.
 {key:'shelf',x:-10.7,z:-.8,width:2.1,depth:.6,height:1.12,dressing:'sideboard'},
 {key:'barrel',x:-11.7,z:-1.65,width:.7,depth:.7,height:.9,yaw:17},
];
