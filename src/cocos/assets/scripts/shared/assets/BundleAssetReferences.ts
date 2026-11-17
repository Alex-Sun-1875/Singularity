import {_decorator,Asset,Component} from 'cc';

const {ccclass,property}=_decorator;

/** Build-only prefab entries give Cocos explicit, typed asset dependencies.
 * They are never instantiated by the game; normal Asset Manager loads each
 * requested UUID from its owning selective bundle. */
@ccclass('BundleAssetReferences')
export class BundleAssetReferences extends Component {
 @property([Asset]) assets:Asset[]=[];
}
