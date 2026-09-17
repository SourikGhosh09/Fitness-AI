import React, {useEffect, useRef, useState} from 'react';
import {AppState, Linking, Pressable, StyleSheet, Text, View} from 'react-native';
import {Image} from 'expo-image';
import {api, tutorialMediaSource} from './api';

type Tutorial = {
  exercise_id: string;
  status: 'available' | 'license_required' | 'unavailable' | 'asset_missing';
  animation_url: string | null;
  poster_url: string | null;
  source_page: string | null;
  attribution: string;
  width: number;
  height: number;
  cache_policy: 'none';
  expires_at: number | null;
};

export function ExerciseTutorial({exerciseId, name}: {exerciseId:string; name:string}) {
  const [tutorial, setTutorial] = useState<Tutorial|null>(null);
  const [playing, setPlaying] = useState(false);
  const [mediaSource, setMediaSource] = useState<{uri:string;headers:{Authorization:string}}|null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('Animation starts only when you choose to play it.');
  const request = useRef(0);
  useEffect(() => {
    request.current++;
    setTutorial(null); setMediaSource(null); setPlaying(false); setBusy(false);
    const subscription = AppState.addEventListener('change', state => {
      if (state !== 'active') {request.current++; setPlaying(false); setMediaSource(null); setBusy(false);}
    });
    return () => {request.current++; subscription.remove();};
  }, [exerciseId]);
  useEffect(() => {
    if (!playing || !tutorial?.expires_at) return;
    // Recheck expiry periodically without scheduling timers beyond the native limit.
    const timer = setInterval(() => {
      if (Date.now() >= tutorial.expires_at!*1000) {
        setPlaying(false); setMessage('Tutorial access has expired. Written instructions remain available.');
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [playing, tutorial?.expires_at]);
  async function watch() {
    if (busy) return;
    if (playing) {setPlaying(false); setMediaSource(null); setMessage('Stopped. Play again to restart the demonstration.'); return;}
    const generation = ++request.current;
    setBusy(true);
    try {
      // Never replay cached grants. Each playback request checks the current server rights record.
      const result = await api<Tutorial>('/exercises/'+encodeURIComponent(exerciseId)+'/tutorial');
      if (generation !== request.current) return;
      setTutorial(result);
      if (result.status === 'available' && result.animation_url && (result.expires_at===null || result.expires_at*1000>Date.now())) {
        const source = await tutorialMediaSource(result.animation_url);
        if (generation !== request.current) return;
        setMediaSource(source); setPlaying(true); setMessage('Exercise demonstration · follow the written steps at your own pace.');
      } else {
        setPlaying(false);
        setMessage(result.status==='asset_missing' ? 'The tutorial file is unavailable. Follow the written steps and try again later.' : result.status==='license_required' ? 'Tutorial access is unavailable. Follow the written instructions.' : 'No animation is available for this exercise. Follow its written instructions.');
      }
    } catch {
      if (generation === request.current) setMessage('Could not load the tutorial. Check your connection; written instructions still work.');
    } finally {if (generation === request.current) setBusy(false);}
  }
  async function openSource() {
    if (!tutorial?.source_page) return;
    try {await Linking.openURL(tutorial.source_page);} catch {setMessage('Could not open GitHub. Try again when connected.');}
  }
  return <View style={styles.root}>
    <Text style={styles.title}>Movement tutorial</Text>
    {playing && mediaSource && <View style={styles.frame}>
      <Image source={mediaSource} style={styles.image} contentFit="contain"
        autoplay cachePolicy="none" transition={0} accessible accessibilityLabel={'Animated demonstration of '+name}
        onError={() => {setPlaying(false); setMediaSource(null); setMessage('Animation unavailable. Check your connection or sign in again; written steps remain available.');}} />
    </View>}
    <Text accessibilityLiveRegion="polite" style={styles.message}>{message}</Text>
    <Pressable accessibilityRole="button" accessibilityLabel={playing?'Stop tutorial for '+name:'Watch tutorial for '+name}
      accessibilityState={{disabled:busy}} disabled={busy} onPress={() => void watch()} style={styles.button}>
      <Text style={styles.buttonText}>{busy?'Loading tutorial…':playing?'Stop tutorial':'Watch tutorial'}</Text>
    </Pressable>
    {tutorial?.source_page && <Pressable accessibilityRole="link" accessibilityLabel={'View original '+name+' tutorial on GitHub'} onPress={() => void openSource()} style={styles.source}>
      <Text style={styles.link}>View original tutorial on GitHub ↗</Text>
    </Pressable>}
    {!!tutorial && <Text style={styles.credit}>{tutorial.attribution}</Text>}
  </View>;
}
const styles = StyleSheet.create({
  root:{gap:12,backgroundColor:'#101915',padding:16,borderRadius:16},
  title:{fontSize:16,fontWeight:'600',color:'#f1f5ee'},
  frame:{alignItems:'center'}, image:{width:180,height:180,backgroundColor:'#ffffff'},
  message:{color:'#b5c3b9',fontSize:14,lineHeight:21},
  button:{minHeight:52,padding:14,borderRadius:12,backgroundColor:'#d1f599',alignItems:'center',justifyContent:'center'},
  buttonText:{color:'#101915',fontSize:15,fontWeight:'700'},
  source:{minHeight:48,justifyContent:'center'},link:{color:'#d1f599',fontSize:14,textDecorationLine:'underline'},
  credit:{color:'#b5c3b9',fontSize:12,lineHeight:18},
});
