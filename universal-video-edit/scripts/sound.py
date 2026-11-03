from pathlib import Path
import json,wave
import numpy as np
p=json.loads(Path('edit-plan.json').read_text(encoding='utf-8'));sr=48000;n=round(p['duration']*sr);a=np.zeros((n,2),np.float32)
gain=float(p.get('music',{}).get('gain',.006));gain=max(0,min(.03,gain))
for i,start in enumerate(np.arange(0,p['duration'],4.5)):
    z=int(start*sr);length=min(int(5*sr),n-z);t=np.arange(length)/sr
    env=np.minimum(1,t/.65)*np.minimum(1,(length/sr-t)/1.2)
    chord=[[146.83,174.61,220],[130.81,164.81,196],[116.54,146.83,174.61]][i%3]
    pad=sum(np.sin(2*np.pi*f*t) for f in chord)/3*env*gain
    a[z:z+length,0]+=pad;a[z:z+length,1]+=pad*.97
fade=np.minimum(1,np.arange(n)/sr)*np.minimum(1,(n-np.arange(n))/sr);a*=fade[:,None]
with wave.open('music.wav','w') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(sr);f.writeframes((np.clip(a,-1,1)*32767).astype('<i2').tobytes())
