import {_decorator,Graphics,Mask} from 'cc';
import {CompactGraphics} from './CompactGraphics';

const {ccclass}=_decorator;

/** Keep the engine's stencil, hit testing and resize lifecycle. Mask reuses an
 * existing Graphics component, so its geometry can use our fitted GFX buffers
 * without replacing the native mask implementation or changing its outline. */
@ccclass('CompactMask')
export class CompactMask extends Mask {
 protected _createGraphics():void {
  if(!this.node.getComponent(Graphics))this.node.addComponent(CompactGraphics);
  super._createGraphics();
 }
}
