/** Shared lifecycle contract; implementations own their platform-specific APIs. */
export interface ScreenAwake {
 setForeground(foreground:boolean):void;
 dispose():void;
}
