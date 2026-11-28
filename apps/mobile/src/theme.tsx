import React from 'react';
import {View} from 'react-native';
import {Ionicons} from '@expo/vector-icons';

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

// Stroke icon set via Ionicons (font glyphs - no extra native view code).
const ICONS:Record<string,React.ComponentProps<typeof Ionicons>['name']>={
  today:'pulse-outline',
  plan:'calendar-outline',
  log:'add-circle-outline',
  exercises:'barbell-outline',
  progress:'stats-chart-outline',
  coach:'sparkles-outline',
  profile:'person-outline',
};
export function Icon({name,color,size=22}:{name:string;color:string;size?:number}){
  return <Ionicons name={ICONS[name]??'ellipse-outline'} color={color} size={size}/>;
}

// Segmented readiness gauge: 20 instrument ticks, filled by score, colored by band.
export function Gauge({score,band,size=180}:{score:number;band:'ready'|'moderate'|'deload';size?:number}){
  const clamped=Math.max(0,Math.min(100,score==null||isNaN(score)?0:score));
  const lit=Math.round(clamped/100*20);
  const color=bandColor(band);
  return <View style={{flexDirection:'row',alignItems:'flex-end',gap:4,height:56,justifyContent:'center'}}>
    {Array.from({length:20},(_,i)=><View key={i} style={{width:6,borderRadius:3,height:16+Math.round(36*Math.sin(Math.PI*(i+0.5)/20)),backgroundColor:i<lit?color:colors.line}}/>)}
  </View>;
}
