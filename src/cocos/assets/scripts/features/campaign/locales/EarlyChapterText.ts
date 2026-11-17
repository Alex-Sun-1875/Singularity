import {registerMessages} from '../../../shared/i18n/Localization';

export interface EarlyChapterMessage {key:string;zh:string;en:string}
/** All early-chapter text is bundled with its authored content. */
export function registerEarlyChapterText(messages:readonly EarlyChapterMessage[]){
 const zh:Record<string,string>={},en:Record<string,string>={};
 for(const message of messages){zh[message.key]=message.zh;en[message.key]=message.en;}
 return registerMessages('earlyChapter',zh,en);
}
