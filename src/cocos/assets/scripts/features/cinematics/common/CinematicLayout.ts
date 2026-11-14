/** Measurements in logical screen pixels, aligned to the approved 844×390 proposal. */
export const CINEMATIC_STYLE={referenceWidth:844,referenceHeight:390,caption:18,speaker:14,lineHeight:27,
 captionWidth:580,speakerTop:274,captionTop:300,captionBottom:350,
 skipRight:22,skipTop:14,continueRight:22,continueBottom:24,controlSize:13,
 hit:48,gap:8,gradientHeight:148,gradientAlpha:.84,enter:.18,change:.12,exit:.16} as const;
export interface CinematicInsets{left:number;right:number;top:number;bottom:number}
export function cinematicLayout(width:number,height:number,insets:CinematicInsets){
 const s=CINEMATIC_STYLE,unit=height/s.referenceHeight,hit=s.hit*unit;
 const left=Math.max(22*unit,insets.left),right=width-Math.max(s.skipRight*unit,insets.right),
  top=Math.max(s.skipTop*unit,insets.top),bottom=height-Math.max(s.continueBottom*unit,insets.bottom);
 const controlWidth=86*unit,continueX=right-controlWidth/2,continueY=bottom-hit/2;
 // The subtitle and continue button own separate input/visual columns.
 const captionRight=right-controlWidth-s.gap*unit,
  captionWidth=Math.max(160*unit,Math.min(s.captionWidth*unit,captionRight-left)),
  captionX=Math.min(width*.5,captionRight-captionWidth/2),
  captionBottom=Math.min(height*350/390,bottom),captionY=captionBottom-27*unit;
 return {unit,hit,controlWidth,left,right,top,bottom,captionWidth,captionX,captionY,
  speakerY:captionY-49*unit,skipX:right-controlWidth/2,skipY:top+hit/2,continueX,continueY};
}
/** No shrinking: split long localized lines into readable two-line subtitle pages. */
export function subtitlePages(text:string,width:number,fontSize:number):string[]{
 const capacity=Math.max(8,width/fontSize),lines:string[]=[];let line='',used=0;
 const tokens=text.match(/[A-Za-z0-9]+(?:['’][A-Za-z]+)?|\s+|[^A-Za-z0-9\s]/gu)??[];
 for(const token of tokens){
  if(token.includes('\n')){if(line.trim())lines.push(line.trim());line='';used=0;continue;}
  const weight=Array.from(token).reduce((n,c)=>n+(/[\x00-\x7f]/.test(c)?/[ilI.,'! ]/.test(c)?.29:.55:1),0);
  if(used+weight>capacity&&line.trim()&&!/^[，。！？；：、,.!?;:）】》”’]$/.test(token)){lines.push(line.trim());line='';used=0;}
  line+=token;used+=weight;
 }
 if(line.trim())lines.push(line.trim());
 const pages:string[]=[];for(let i=0;i<lines.length;i+=2)pages.push(lines.slice(i,i+2).join('\n'));
 return pages.length?pages:[''];
}
export function subtitleSeconds(text:string,authored:number,pages:number):number{
 const cjk=(text.match(/[^\x00-\x7f\s]/g)??[]).length,words=(text.match(/[A-Za-z0-9]+/g)??[]).length;
 return Math.max(2.5,authored/Math.max(1,pages),1.2+cjk*.09+words/3);
}
