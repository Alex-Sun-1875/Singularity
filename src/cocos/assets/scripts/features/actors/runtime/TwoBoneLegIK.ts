/* Two-bone position solve adapted from Cocos Creator 3.8.8:
 * cocos/animation/marionette/pose-graph/pose-nodes/ik/solve-two-bone-ik.ts
 * MIT License
 * Copyright (c) 2013-2016 Chukong Technologies Inc.
 * Copyright (c) 2017-2023 Xiamen Yaji Software Co., Ltd.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
import {Node,Quat,Vec3} from 'cc';

/** Node adapter for the engine's analytic solve. Rotates joints without
 * translating/scaling the leg bones or depending on experimental pose graphs. */
export class TwoBoneLegIK {
 private readonly a=new Vec3();private readonly b=new Vec3();private readonly c=new Vec3();
 private readonly target=new Vec3();private readonly direction=new Vec3();private readonly hint=new Vec3();
 private readonly solvedKnee=new Vec3();private readonly solvedFoot=new Vec3();
 private readonly from=new Vec3();private readonly to=new Vec3();private readonly rotation=new Quat();
 private upperLength=0;private lowerLength=0;
 constructor(readonly thigh:Node,readonly calf:Node,readonly foot:Node){}
 solve(target:Vec3,footRotation:Quat,weight:number){
  this.a.set(this.thigh.worldPosition);this.b.set(this.calf.worldPosition);this.c.set(this.foot.worldPosition);
  Vec3.lerp(this.target,this.c,target,weight);
  const ab=Vec3.distance(this.a,this.b),bc=Vec3.distance(this.b,this.c),distance=Vec3.distance(this.a,this.target);
  this.upperLength=ab;this.lowerLength=bc;
  if(distance<.00001||ab<.00001||bc<.00001)return;
  Vec3.subtract(this.direction,this.target,this.a).normalize();
  if(distance>=ab+bc){
   Vec3.scaleAndAdd(this.solvedKnee,this.a,this.direction,ab);
   Vec3.scaleAndAdd(this.solvedFoot,this.a,this.direction,ab+bc);
  }else{
   this.solvedFoot.set(this.target);
   const cosine=Math.max(-1,Math.min(1,(ab*ab+distance*distance-bc*bc)/(2*ab*distance))),along=ab*cosine;
   Vec3.subtract(this.hint,this.b,this.a);Vec3.projectOnPlane(this.to,this.hint,this.direction).normalize();
   Vec3.scaleAndAdd(this.solvedKnee,this.a,this.direction,along);
   Vec3.scaleAndAdd(this.solvedKnee,this.solvedKnee,this.to,Math.sqrt(Math.max(0,ab*ab-along*along)));
  }
  Vec3.subtract(this.from,this.b,this.a).normalize();Vec3.subtract(this.to,this.solvedKnee,this.a).normalize();
  Quat.rotationTo(this.rotation,this.from,this.to);Quat.multiply(this.rotation,this.rotation,this.thigh.worldRotation);this.thigh.setWorldRotation(this.rotation);
  this.b.set(this.calf.worldPosition);this.c.set(this.foot.worldPosition);
  Vec3.subtract(this.from,this.c,this.b).normalize();Vec3.subtract(this.to,this.solvedFoot,this.b).normalize();
  Quat.rotationTo(this.rotation,this.from,this.to);Quat.multiply(this.rotation,this.rotation,this.calf.worldRotation);this.calf.setWorldRotation(this.rotation);
  Quat.slerp(this.rotation,this.foot.worldRotation,footRotation,weight);this.foot.setWorldRotation(this.rotation);
 }
}
