import {platformStorage} from '../../../platform/PlatformStorage';
import {htmlPreviewOption,rememberHtmlPreviewOption} from '../../../platform/HtmlPreview';

export interface HairstyleDefinition {id:string;label:string;description:string;nodes:string[];geometryRoot?:string}
export interface HairstyleOption {id:string;label:string;description:string;selected:boolean}
/** Painted variants preserve the approved face and costume while matching each hair choice. */
export const HAIRSTYLE_PORTRAITS:Readonly<Record<string,string>>={
 curly:'portraits/raphael-hair-curly-v1',dante:'portraits/raphael-hair-dante-v1',
 nero:'portraits/raphael-hair-nero-v1',vergil:'portraits/raphael-hair-vergil-v1',
};
const KEY='sword-and-fire:player-hairstyle:v1';

/** Cosmetic preference stays independent of journey progress and equipment. */
export function readHairstyle():string {
 try{return htmlPreviewOption('hair')||platformStorage.getItem(KEY)||'curly';}catch{return 'curly';}
}
export function rememberHairstyle(id:string){
 try{platformStorage.setItem(KEY,id);}catch{/* Cosmetic preferences cannot prevent play. */}
 rememberHtmlPreviewOption('hair',id);
}
