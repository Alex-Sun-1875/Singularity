import type {FeedbackRole} from './FeedbackPalette';

type Insets=readonly [number,number,number,number];
type SkinDefinition={readonly asset:string;readonly insets?:Insets};
const skin=(name:string,version:'v2'|'v5'='v2',insets?:Insets):SkinDefinition=>({asset:`prep-${name}-${version}`,insets});

/** Approved management UI art. Asset versions and nine-slice source pixels live here. */
export const PREPARATION_SKINS={
 frame:skin('frame','v2',[32,32,32,32]),header:skin('header'),surface:skin('surface'),
 logo:skin('logo','v5'),rule:skin('rule','v5'),active:skin('active','v5'),'shell-rule':skin('shell-rule','v5'),
 identity:skin('identity','v5',[30,30,6,6]),plaque:skin('plaque','v2',[20,20,12,12]),
 socket:skin('socket','v5',[12,12,12,12]),'socket-selected':skin('socket-selected','v5',[18,18,18,18]),
 'side-tab':skin('side-tab','v5',[24,24,16,16]),'side-tab-selected':skin('side-tab-selected','v5',[24,24,16,16]),
 'button-dark':skin('button-dark','v2',[20,20,12,12]),'button-gold':skin('button-gold','v2',[20,20,12,12]),
 card:skin('card','v5',[28,28,28,28]),'card-selected':skin('card-selected','v2',[28,28,28,28]),
 'attribute-row':skin('attribute-row','v5',[24,24,24,24]),'skill-row':skin('skill-row','v5',[24,24,20,20]),'skill-selected':skin('skill-selected','v5',[24,24,20,20]),
 'point-counter':skin('point-counter','v5',[20,20,12,12]),'skill-cost':skin('skill-cost','v5',[20,20,12,12]),step:skin('step','v2',[20,20,12,12]),
 scope:skin('scope','v2',[20,20,12,12]),'scope-active':skin('scope-active','v5',[24,24,12,12]),categories:skin('categories','v2',[20,20,12,12]),chip:skin('chip','v2',[20,20,12,12]),
 'badge-gold':skin('badge-gold','v2',[20,20,12,12]),'badge-teal':skin('badge-teal','v2',[20,20,12,12]),
 hero:skin('hero'),'hero-narrow':skin('hero-narrow'),smoke:skin('smoke'),'crest-sword':skin('crest-sword','v5'),
 'attribute-strength':skin('attribute-strength'),'attribute-dexterity':skin('attribute-dexterity'),'attribute-intellect':skin('attribute-intellect'),'attribute-vitality':skin('attribute-vitality'),
 'item-sword':skin('item-sword'),'item-head':skin('item-head'),'item-chest':skin('item-chest'),'item-hands':skin('item-hands'),'item-feet':skin('item-feet'),'item-necklace':skin('item-necklace'),'item-ring':skin('item-ring'),'item-bow':skin('item-bow'),'item-staff':skin('item-staff'),
 'item-steel-sword':skin('item-steel-sword','v5'),'item-blue-bow':skin('item-blue-bow','v5'),'item-lightning-staff':skin('item-lightning-staff','v5'),'empty-offhand':skin('empty-offhand','v5'),'weapon-bow':skin('weapon-bow','v5'),
 'inspect-sword':skin('inspect-sword'),'inspect-staff':skin('inspect-staff'),
 'stat-life':skin('stat-life','v5'),'stat-power':skin('stat-power','v5'),'stat-plan':skin('stat-plan','v5'),'stat-target':skin('stat-target','v5'),'stat-radius':skin('stat-radius','v5'),info:skin('info','v5'),
 'stat-level':skin('stat-level','v5'),'stat-weapon':skin('stat-weapon','v5'),'stat-upgrade':skin('stat-upgrade','v5'),'stat-source':skin('stat-source','v5'),
} as const;
export type PreparationSkinName=keyof typeof PREPARATION_SKINS;
/** Compatibility for existing dynamic skin names; new components use the catalog above. */
export function preparationSkinAsset(name:string):string{return PREPARATION_SKINS[name as PreparationSkinName]?.asset??`prep-${name}-v2`;}

const legacyInsets:Record<string,Insets>={
 'prep-card-v2':[28,28,28,28],'prep-attribute-row-v2':[24,24,24,24],
 'prep-skill-row-v2':[24,24,20,20],'prep-skill-selected-v2':[24,24,20,20],
};
for(const definition of Object.values(PREPARATION_SKINS))if(definition.insets)legacyInsets[definition.asset]=definition.insets;
export const PREPARATION_SKIN_INSETS:Readonly<Record<string,Insets>>=legacyInsets;

/** Layout values use the 844×390 artwork grid, except explicitly logical-screen values. */
export const PREPARATION_DESIGN={
 canvas:{width:844,height:390,sourceWidth:1844},
 colorRoles:{ink:'text.preparation',accent:'text.preparationAccent',selected:'state.selected',disabled:'text.disabled'} satisfies Record<string,FeedbackRole>,
 typography:{minimumLogical:11,body:14,lineHeight:1.3,navigation:17,footer:16,identity:15.5,sideTab:18,rowTitle:17,attributeName:19.5,number:20,delta:16,small:12.5},
 interaction:{hitLogical:48,gapLogical:8},
 shell:{phoneHeightLogical:354,phoneVerticalGutterLogical:24,phoneHorizontalGutterLogical:32,desktopWidthLogical:1040,desktopHorizontalGutterLogical:80,desktopVerticalGutterLogical:48,referenceMinWidthLogical:1000,backdropAlpha:112,margin:18,contentTop:32},
 frame:{asset:'double-gold-frame-rpg-v4',pixelScaleLogical:.5,clipInsetSource:14,clipRadiusSource:12},
 header:{visibleHeightLogical:40,referenceCenterY:16,referenceHitHeight:28,visualOffsetLogical:10,tabStart:200,tabWidth:72,tabMinimumGap:8,underlineOffset:13,underlineWidth:82,underlineHeight:7,logoX:72,logoWidth:70,logoHeight:19,leftSeparatorX:135,rightSeparatorX:782,separatorHeight:12,closeFont:21,coinX:704,coinSize:16,goldX:746,goldWidth:57,goldFont:16},
 footer:{widths:[122,130,122],gaps:[10,12],rightInset:12,buttonHeight:31.5,fire:{x:34,width:30,height:31},statusX:54,statusMinFont:12,statusMaxFont:14,returnArrowSize:16,returnArrowInset:20,returnTextOffset:11},
 artwork:{coin:'rpg-coin-v2',campfire:'rpg-campfire-v2',footerRule:'rpg-footer-rule-v4',returnArrow:'rpg-return-arrow-v3',offhand:'rpg-painted-offhand-v5',familyPaintings:{WAR:'rpg-profession-war-v1',BOW:'rpg-profession-bow-v1',FIR:'rpg-profession-fir-v1',THU:'rpg-profession-thu-v1'},mainWeaponIcons:{WAR:'rpg-family-war-v3',BOW:'prep-weapon-bow-v5',FIR:'rpg-family-fir-v3',THU:'rpg-family-thu-v3'}},
 decoration:{ruleHeight:7,smokeWidth:200,smokeHeight:56},
 identity:{height:22,labelHeight:22,textInset:12},
 tab:{height:35,selectedHeight:42,labelHeight:30,textInset:12,referenceHitHeight:35},
 row:{selectedExtraWidth:2,selectedExtraHeight:1},card:{selectedExtraWidth:1,selectedExtraHeight:1},
 badge:{width:52,height:18,textInset:5,compactHeight:16,compactFont:11.5,font:12.5},
 step:{width:48,height:43,labelHeight:40,labelInset:4,font:29,disabledAlpha:150},
 caption:{font:12.5,height:21,asciiWidth:.55,labelInset:2},
 professionCard:{artInset:16,artHeight:.42,artY:.15,titleY:-.19,titleInset:14,titleHeight:26,titleFont:18,ruleY:-.32,ruleInset:30,descriptionY:-.42,descriptionInset:12,descriptionHeight:18,descriptionFont:12.5,badgeWidth:48,badgeRight:30,badgeTop:17},
 attributeRow:{centerX:390,width:400,maxHeight:61,gap:8,iconX:-157,iconWidth:62,iconHeight:50,nameX:-96,nameWidth:68,nameHeight:30,separatorX:-60,separatorHeight:28,beforeX:-40,beforeWidth:36,arrowX:-7,arrowWidth:24,arrowFont:19,afterX:20,afterWidth:34,deltaX:56,deltaWidth:42,referenceButtonX:116,referenceButtonStep:53,referenceButtonWidth:43,compactButtonX:113},
 skillRow:{width:302,height:47,iconX:-116,iconSize:40,nameX:-15,nameWidth:140,labelHeight:27,levelX:101,levelWidth:86,levelFont:13.5},
 counter:{skillWidth:108,skillTitleWidth:104,extraWidth:2,titleInset:6,costInset:4,backgroundInset:2,titleY:11,costY:-11,labelHeight:22,attributeTitleFont:14.5,attributeCostFont:13,skillTitleFont:12.5,skillCostFont:12},
 layouts:{character:{portrait:[0,224],attributes:[232,332],overview:[572,272]},equipment:{portrait:[0,264],inventory:[264,300],detail:[568,276]},profession:{portrait:[0,204],cards:{left:216,width:348,maxHeight:126,referenceTop:48},detail:[576,268]},allocation:{attributeSidebar:[0,182],skillSidebar:[132,110],attributeRows:[190,404],skillRows:[250,314],attributeDetail:[598,246],skillDetail:[574,270]}},
 inventory:{columns:4,gridWidth:284,gridLeft:272,categoryWidth:76,scopeHeight:32,scopeCurrentY:59,scopeAllY:55,categoryCurrentY:96,categoryAllY:87,categoryHeight:26,gridCurrentTop:124,gridAllTop:110,gridCurrentHeight:174,gridAllHeight:199,currentRowHeight:76,allRowHeight:61,referenceRowGap:7,maxTileWidth:66,countCurrentY:309,countAllY:322,
  identity:{reference:{x:139,y:49,width:160,height:24,textWidth:150,font:15},compact:{x:132,width:116,height:21,textWidth:108,font:13}},
  sockets:{left:47,right:225,top:118,step:52,handY:288,mainX:70,offX:207,sideSize:44,handSize:50,compactHandSize:38,handLabelGap:11,compactLabelY:-20},
 },
} as const;
