import {sys} from 'cc';
import {MINIGAME} from 'cc/env';

/** Runtime target is independent of dev/test/release and resource-preview modes. */
export const isTapMinigame=MINIGAME;
export const isHtmlRuntime=!MINIGAME&&sys.isBrowser;
/** Never inspect a browser-injected tap object to decide the runtime. */
export function readTapAPI<T>():T|undefined{return isTapMinigame?(globalThis as {tap?:T}).tap:undefined;}
