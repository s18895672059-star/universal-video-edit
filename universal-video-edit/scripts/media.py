from pathlib import Path
import subprocess, math
from PIL import Image

class Media:
    def __init__(self,assets,base,ff):
        self.assets=assets;self.base=base;self.ff=ff;self.images={};self.streams={}

    def close_stream(self,key):
        if key in self.streams:
            p,*_=self.streams.pop(key)
            p.terminate();p.stdout.close();p.wait()

    def close(self):
        for key in list(self.streams):self.close_stream(key)

    def get(self,key,t,static=False):
        a=self.assets[key];path=Path(a['path']);path=path if path.is_absolute() else self.base/path
        if a['type']=='image':
            if key not in self.images:self.images[key]=Image.open(path).convert('RGB')
            return self.images[key].copy()
        t=min(max(0,t+a.get('offset',0)),max(0,a['duration']-1/30))
        if static:
            cache=(key,round(t,2))
            if cache not in self.images:
                raw=subprocess.check_output([self.ff,'-v','error','-ss',str(t),'-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
                self.images[cache]=Image.frombytes('RGB',tuple(a['size']),raw)
            return self.images[cache].copy()
        frame=int(t*60)
        if key in self.streams:
            p,last,im=self.streams[key]
            if frame<last or frame-last>120:self.close_stream(key)
        if key not in self.streams:
            p=subprocess.Popen([self.ff,'-v','error','-ss',str(frame/60),'-i',str(path),'-vf','fps=60','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
            self.streams[key]=[p,frame-1,None]
        state=self.streams[key];size=math.prod(a['size'])*3
        while state[1]<frame:
            raw=state[0].stdout.read(size)
            if len(raw)!=size:
                if state[2] is None:raise ValueError(f'Cannot decode {key} at {t}')
                state[1]=frame;break
            state[2]=Image.frombytes('RGB',tuple(a['size']),raw);state[1]+=1
        return state[2].copy()

