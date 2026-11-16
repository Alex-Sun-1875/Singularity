import {taskPanelText as text} from '../locales/TaskPanelText';
export const taskPanelTabs=(active:string)=>(['chapters','main','side'] as const).map(id=>({label:text(`tab.${id}`),action:'journey-tasks:'+id,selected:active===id}));
