import {beat,type CampaignScene} from '../common/CinematicTypes';
export const FIELD_QUEST_SCENES:CampaignScene[]=[
 {id:'field-letter-ending',chapter:1,area:'S19',trigger:'task',task:'dg-letter-return',title:'field.letter.title',beats:[beat('field.orin','field.letter.1',4,{cue:'quiet'}),beat('field.raphael','field.letter.2',4)]},
 {id:'field-hunt-ending',chapter:1,area:'S05',trigger:'task',task:'field-hunt-return',title:'field.hunt.title',beats:[beat('field.nightqi','field.hunt.1',5),beat('field.nightqi','field.hunt.2',5)]},
 {id:'field-lamp-ending',chapter:2,area:'H03',trigger:'task',task:'dg-lamp-return',title:'field.lamp.title',beats:[beat('field.bren','field.lamp.1',5,{cue:'quiet'}),beat('field.bren','field.lamp.2',5)]},
 {id:'field-arms-ending',chapter:2,area:'H01',trigger:'task',task:'field-arms-return',title:'field.arms.title',beats:[beat('field.tarek','field.arms.1',5),beat('field.raphael','field.arms.2',4)]},
 {id:'field-dawn-record',chapter:1,area:'S12',trigger:'task',task:'field-dawn-record',title:'field.dawn.title',beats:[beat('field.record','field.dawn.1',5,{cue:'command'}),beat('field.record','field.dawn.2',5,{cue:'quiet'})]},
 {id:'field-bell-ending',chapter:2,area:'H17',trigger:'task',task:'field-bell-return',title:'field.bell.title',beats:[beat('field.milo','field.bell.1',5,{cue:'bells'}),beat('field.raphael','field.bell.2',5)]},
];
