/** Shared normal-play prices. Build profiles never multiply currency rewards. */
export const GOLD_CAPACITY=9_999_999;
export const GOLD_PENDING_LIMIT=9_000_000_000;
export const GEM_PRICES=[0,240,760,2400,7560,23760] as const;
export const GEM_SYNTHESIS_FEES=[0,40,120,360,1080] as const;
export const GEM_TRADE_LEVELS=[0,6,16,32,48,64] as const;
export const GEM_TRADE_CHAPTERS=[0,1,2,4,5,7] as const;
export const SHOP_PRICES={health:12,resource:12,drills:6} as const;
export const CHAPTER_ECONOMY=[1800,3600,5400,7800,10800,14400,18600,24000].map((total,index)=>({
 chapter:index+1,released:index<2,total,main:total*2/5,boss:total/10,fixed:total/6,exploration:total/3,
 ordinaryGold:[3,4,5,6,8,10,12,15][index],
}));
