import React from 'react';
import Svg,{Path} from 'react-native-svg';

// Stitch design language: a calm, precise training instrument.
// One accent (volt), one semantic set (readiness), near-black base.
export const colors={
  bg:'#0A0C10',
  surface:'#14171E',
  surface2:'#1A1E28',
  well:'#05060A',
  volt:'#C8F04A',
  voltSoft:'#232B12',
  onVolt:'#0A0C10',
  ready:'#5FD68B',
  moderate:'#F0B64A',
  deload:'#F05A5A',
  text:'#F5F7FA',
  muted:'#8B93A3',
  line:'#232834',
  indigoBubble:'#2E3350',
};

export function readinessBand(score:number|null|undefined):'ready'|'moderate'|'deload'{
  if(score==null)return 'moderate';
  if(score>=70)return 'ready';
  if(score>=40)return 'moderate';
  return 'deload';
}
export function bandColor(band:'ready'|'moderate'|'deload'){
  return band==='ready'?colors.ready:band==='moderate'?colors.moderate:colors.deload;
}
export function bandLabel(band:'ready'|'moderate'|'deload'){
  return band==='ready'?'READY // PRIME':band==='moderate'?'MODERATE // STEADY':'DELOAD // RECOVER';
}

// Stroke icon set (24x24, Lucide-style). No emoji glyphs.
const ICONS:Record<string,React.ReactNode>={
  today:<Path d="M3 12h4l3 8 4-16 3 8h4"/>,
  plan:<><Path d="M5 5h14v15H5z"/><Path d="M5 10h14M9 3v4M15 3v4"/></>,
  log:<><Path d="M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z"/><Path d="M12 8v8M8 12h8"/></>,
  exercises:<><Path d="M7 7v10M17 7v10M3 10v4M21 10v4M7 12h10"/></>,
  progress:<><Path d="M5 20v-6M10 20V6M15 20v-9M20 20v-13"/></>,
  coach:<Path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z"/>,
  profile:<><Path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z"/><Path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></>,
};
export function Icon({name,color,size=22}:{name:string;color:string;size?:number}){
  return <Svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">{ICONS[name]??null}</Svg>;
}

// Semicircle readiness gauge: the one hero element of the Today screen.
function polar(cx:number,cy:number,r:number,deg:number){
  const rad=(180-deg)*Math.PI/180;
  return [cx+r*Math.cos(rad),cy-r*Math.sin(rad)];
}
export function gaugeArc(score:number){
  const cx=90,cy=88,r=72;
  const clamped=Math.max(0,Math.min(100,score));
  const [x0,y0]=polar(cx,cy,r,0),[x1,y1]=polar(cx,cy,r,180);
  const [xe,ye]=polar(cx,cy,r,clamped*1.8);
  const track=`M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`;
  const large=clamped>50?1:0;
  const fill=clamped<=0?'':`M ${x0} ${y0} A ${r} ${r} 0 ${large} 0 1 ${xe} ${ye}`;
  return {track,fill,end:[xe!,ye!] as const};
}
export function Gauge({score,band,size=180}:{score:number;band:'ready'|'moderate'|'deload';size?:number}){
  const {track,fill,end}=gaugeArc(score);
  return <Svg width={size} height={size*0.55} viewBox="0 0 180 96" fill="none">
    <Path d={track} stroke={colors.line} strokeWidth={10} strokeLinecap="round"/>
    {!!fill&&<Path d={fill} stroke={bandColor(band)} strokeWidth={10} strokeLinecap="round"/>}
    {!!fill&&<Path d={`M ${end[0]-5} ${end[1]} a 5 5 0 1 0 0.1 0`} fill={bandColor(band)} stroke="none"/>}
  </Svg>;
}
