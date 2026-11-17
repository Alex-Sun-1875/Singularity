export const zh={
 'entry':'兑换码','entry.detail':'装备、宝石、金币与培养材料 · 每旅程限领',
 'campaign.legend':'传奇启程','campaign.gems3':'晶辉珍藏','campaign.gems4':'星耀典藏','campaign.gems5':'巅峰珍礼',
 'reason.invalid':'未识别兑换码，请检查输入。','reason.claimed':'本旅程已领取该礼包，可查看原领取记录。',
 'reason.busy':'请先结束当前操作，再领取礼包。','reason.selection':'请选满武器和宝石属性。',
 'reason.owned':'本旅程已拥有或地面待拾取，请选择其他武器。','reason.stale':'状态或选择已变化，请重新确认完整奖励。',
 'reason.limit':'领取或宝石记录已达容量上限，领取资格仍保留。','reason.full':'背包或材料容量不足，领取资格仍保留。',
 'reason.failed':'领取未完成，请重新查看奖励。','source':'兑换礼包 · {name}',
} as const;
export type RedemptionMessageKey=keyof typeof zh;
