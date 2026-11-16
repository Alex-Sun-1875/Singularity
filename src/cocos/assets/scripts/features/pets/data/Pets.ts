import {petText} from '../locales';
/** Content release switch: saves, URLs and build profiles cannot enable pets. */
export const PET_POLICY=Object.freeze({enabled:false,unlockChapter:3,capacity:12,maxBond:100,maxEssence:999999,maxTransactions:20000,maxSources:2048});
export type PetSpeciesId='ember_fox'|'stone_turtle'|'dew_sprite'|'tabby_cat'|'hunting_dog'|'grey_wolf'|'mountain_tiger'|'hunting_hawk'|'spotted_deer'|'griffin'|'white_tiger'|'dragon';
export type PetRole='attack'|'guard'|'heal';
export type PetSkillId='ferocity'|'haste'|'devotion'|'thick_hide'|'moisture'|'headwind'|'daybreak'|'keen_edge';
export type PetBranch='A'|'B';
export const PET_QUALITIES=['普通','珍兽','神兽'] as const;
export type PetQuality=typeof PET_QUALITIES[number];
export const PET_PROMOTIONS=[{quality:'珍兽',level:20,bond:40,gold:150,essence:40},{quality:'神兽',level:60,bond:80,gold:600,essence:180}] as const;
export const PET_RESEARCH_COSTS=[{gold:0,essence:0},{gold:0,essence:0},{gold:50,essence:10},{gold:100,essence:20},{gold:180,essence:35},{gold:300,essence:60}] as const;
export const PET_RESEARCH_VALUES:Readonly<Record<PetSkillId,number>>={ferocity:.4,haste:1.2,devotion:2,thick_hide:.8,moisture:1.2,headwind:1,daybreak:1,keen_edge:.6};
export interface PetSignatureDefinition {name:string;description:string;branches:readonly {id:PetBranch;name:string;description:string}[]}
export interface PetSpeciesDefinition {id:PetSpeciesId;name:string;role:PetRole;nativeQuality:PetQuality;description:string;nativeSkill:string;signature:PetSignatureDefinition}
const definition=(id:PetSpeciesId,name:string,role:PetRole,nativeQuality:PetQuality,description:string,nativeSkill:string,skill:string,trigger:string,a:string,ad:string,b:string,bd:string):PetSpeciesDefinition=>({id,name,role,nativeQuality,description,nativeSkill,signature:{name:skill,description:trigger,branches:[{id:'A',name:a,description:ad},{id:'B',name:b,description:bd}]}});
export const PET_SPECIES:readonly PetSpeciesDefinition[]=[
 definition('ember_fox',petText('species.fox'),'attack','普通','赤褐狐狸，擅长稳定进攻。','余烬共鸣','追烬','直接命中后，向仍存活的原目标产生一次伤害回响。','猎烬','强化低生命目标的回响。','暖烬','用短时防护替代回响。'),
 definition('stone_turtle',petText('species.turtle'),'guard','普通','石纹甲龟，擅长承受重击。','稳甲','稳甲承压','受到明显重击后，缓冲接下来的攻击。','承岳','集中保护下一击。','绵岩','以较弱持续防护应对多次攻击。'),
 definition('dew_sprite',petText('species.sprite'),'heal','普通','洁白小兔，帮助治疗与资源周转。','温养','回春应和','真实恢复生命后，短时增强职业资源自然恢复。','润根','更平缓、更长的资源恢复。','护芽','改为受治疗增强。'),
 definition('tabby_cat','花猫','attack','普通','灵巧花猫，适合近身混战。','灵巧','受压反扑','短时间被不同敌人伤害后，获得反攻窗口。','追击','强化群敌压力后的进攻。','守身','改为短时防护。'),
 definition('hunting_dog','猎犬','heal','普通','忠实猎犬，擅长重新接战时的整备。','同行','整装待发','真正脱战后再接敌，获得短时资源恢复。','引航','增强开战资源整备。','守夜','用防护替代资源恢复。'),
 definition('grey_wolf','苍狼','guard','珍兽','灰色野狼，擅长群敌压力下反击。','群战','逆势反击','承受三次不同攻击后，获得短时反攻窗口。','逆势','受压后转入进攻。','敛锋','放弃反攻，改为防护。'),
 definition('mountain_tiger','山虎','heal','珍兽','山林猛虎，擅长受伤后的恢复。','复元','伤后回转','低生命时得到真实治疗，获得资源恢复窗口。','回涌','强化资源周转。','护身','改为较短的脱险防护。'),
 definition('hunting_hawk','猎鹰','attack','珍兽','锐目猎鹰，擅长远距单体目标。','鹰眼','远距标定','远距连续命中同目标后，强化对该目标的伤害。','凌空','保留远距单体优势。','贴翼','改为成功闪避后触发，峰值较低。'),
 definition('spotted_deer','花鹿','heal','珍兽','温顺花鹿，适合移动与资源整备。','轻行','换气','资源偏低时成功避开真实攻击，获得恢复窗口。','潜息','保留低资源条件，缩短等待。','轻渡','降低资源条件依赖，峰值较低。'),
 // Retain the historical key so existing companion and journey proofs survive.
 definition('griffin','凤凰','guard','神兽','火红金羽的不死鸟，擅长在危急时以焰翼护主。','焰羽','焰羽庇护','遭遇将会致命的敌方攻击时，尝试减轻这一击；不会复活或锁血。','炽羽','集中缓冲危急命中。','余焰','在较低生命时提前触发，但保护较弱。'),
 definition('white_tiger','白虎','guard','神兽','白色猛虎，擅长命中与闪避的攻守节奏。','镇守','回锋','记住一次直接命中，随后成功闪避才回击原目标。','回声','维持命中、闪避、回击节奏。','静守','取消回击，改为闪避后的资源恢复。'),
 definition('dragon','巨龙','attack','神兽','幼年巨龙，擅长恢复行动后的反制。','龙威','龙威反制','从真实敌方控制中恢复后，首个命中产生回响。','破令','保留恢复行动后的反攻。','守志','取消回响，改为短时防护。'),
];
export const PET_SKILLS:readonly {id:PetSkillId;name:string;description:string}[]=[
 {id:'ferocity',name:'威势',description:'提高造成的伤害。'},{id:'haste',name:'活泉',description:'提高职业资源自然恢复，不放大药水或退款。'},
 {id:'devotion',name:'心契',description:'放大出战伙伴的天性属性。'},{id:'thick_hide',name:'厚护',description:'提高生命上限，不直接恢复生命。'},
 {id:'moisture',name:'润泽',description:'提高真实治疗量，不复活死亡角色。'},{id:'headwind',name:'逆风',description:'生命低于35%时获得独立减伤，恢复到40%后退出。'},
 {id:'daybreak',name:'破晓',description:'对生命高于80%的目标提高伤害。'},{id:'keen_edge',name:'砺锋',description:'对精英与首领提高伤害，不改变机制抗性。'},
];
export const petSpecies=(id:unknown)=>PET_SPECIES.find(species=>species.id===id);
export const petSkill=(id:unknown)=>PET_SKILLS.find(skill=>skill.id===id);
export const petSignatureGrowth=(level:number)=>{const growth=Math.log2(level+1);return growth/(growth+6);};
