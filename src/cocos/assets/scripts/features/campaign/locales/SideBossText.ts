import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'forge.name':'夺料机首','orders.name':'井链号令卫','bridge.name':'截路督军',
 'forge.description':'失控矿机占住物料支架，用连续重击与缺口震环封锁车道。留意预警与重击后的空当。',
 'orders.description':'井链守卫把过期号令当作现令执行。沿侧面接近，观察三刃追击与停顿，再取回中继封签。',
 'bridge.description':'督军在前哨近侧勒索运料队。避开盾冲与横扫，从恢复空当夺回路障通行册。',
} as const;
const en:Record<keyof typeof zh,string>={
 'forge.name':'Cargo Reclaimer','orders.name':'Chainwell Command Warden','bridge.name':'Roadblock Warlord',
 'forge.description':'A rogue mining machine has seized the material rack. Watch its heavy strikes and gapped shock ring, then punish its recovery.',
 'orders.description':'The chainwell warden still enforces an expired command. Approach from the side, read the three-blade pursuit and recover the relay seal.',
 'bridge.description':'The warlord extorts haulers beside the outpost. Evade shield charges and sweeps, then recover the roadblock ledger during its recovery.',
};
export const sideBossText=registerMessages('side-bosses',zh,en);
