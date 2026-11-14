import {Color} from 'cc';
import {FeedbackView as F} from './FeedbackView';

/** iPhone 14 landscape aspect at the established 720-unit UI scale. */
export const UI_DESIGN_SIZE={width:1558,height:720} as const;

/** Information stays compact; frequent combat touches keep room from the edge. */
export const UI_HUD_INSETS={information:6,combat:16} as const;

/** Honey-gold metal over warm near-black insets; ivory text and clear spell colors. */
export const UI_COLORS={
 background:new Color(12,9,7),panel:new Color(25,19,14,248),dark:new Color(9,7,5),
 inset:new Color(18,18,16,248),
 button:new Color(34,24,16),toggleOff:new Color(56,47,35),active:new Color(23,54,57),hover:new Color(48,34,23),
 gold:new Color(218,174,101),goldLight:F.color('state.ready'),line:new Color(141,96,48),ink:F.color('text.normal'),
 muted:new Color(194,163,122),green:F.color('state.success'),unknown:F.color('text.disabled'),
 route:F.color('map.exit'),purple:F.color('quality.epic'),danger:new Color(94,39,60),red:F.color('state.failure'),
};

// Approved management UI layout, skins and semantic color roles.
export {PREPARATION_DESIGN,PREPARATION_SKINS} from './PreparationTheme';
