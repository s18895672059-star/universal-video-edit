import argparse,json,os,re,shutil,subprocess,sys
from pathlib import Path
from schema import validate

def ffmpeg():
    ff=os.environ.get('EDIT_FFMPEG') or shutil.which('ffmpeg')
    if not ff:
        from imageio_ffmpeg import get_ffmpeg_exe
        ff=get_ffmpeg_exe()
    return ff

def inspect(ff,path):
    result=subprocess.run([ff,'-hide_banner','-i',str(path)],capture_output=True,text=True,errors='replace').stderr
    video=next((line for line in result.splitlines() if 'Video:' in line),None)
    if not video:raise ValueError(f'No video stream: {path}')
    if any(v in video for v in ['smpte2084','arib-std-b67','bt2020']):
        raise ValueError('HDR/wide-gamut source: preserve color in a dedicated pipeline or perform explicit tone mapping before using this SDR renderer')
    rotation=re.search(r'rotation of\s+([\d.-]+)',result)
    if rotation and abs(float(rotation[1]))>.01:raise ValueError('Rotated source: normalize orientation first and re-inspect')
    size=list(map(int,re.search(r'\b(\d{2,5})x(\d{2,5})\b',video).groups()))
    hh,mm,ss=re.search(r'Duration: (\d+):(\d+):([\d.]+)',result).groups()
    fps=re.search(r'([\d.]+) fps',video)
    return dict(source=str(path),source_size=size,duration=int(hh)*3600+int(mm)*60+float(ss),source_fps=float(fps[1]) if fps else None,has_audio='Audio:' in result,stream=video.strip())

def main():
    ap=argparse.ArgumentParser(description='Reference-style editorial toolkit; all industry content comes from edit-plan.json')
    ap.add_argument('action',choices=['doctor','prepare','validate','preview','render'])
    ap.add_argument('source',type=Path,nargs='?');ap.add_argument('project',type=Path,nargs='?')
    args=ap.parse_args();ff=ffmpeg();os.environ['EDIT_FFMPEG']=ff
    if args.action=='doctor':
        import PIL,numpy,drawing
        drawing.f(30);drawing.f(30,False)
        subprocess.run([ff,'-version'],check=True,stdout=subprocess.DEVNULL)
        enc=subprocess.check_output([ff,'-hide_banner','-encoders'],text=True,stderr=subprocess.DEVNULL)
        if 'libx264' not in enc:raise ValueError('FFmpeg needs libx264')
        print(json.dumps(dict(python=sys.version,Pillow=PIL.__version__,numpy=numpy.__version__,ffmpeg=ff,font='OK'),ensure_ascii=False,indent=2));return
    if not args.source or not args.project:ap.error('source and project are required')
    source=args.source.resolve(strict=True);project=args.project.resolve();project.mkdir(parents=True,exist_ok=True)
    scripts=Path(__file__).resolve().parent;info=inspect(ff,source)
    def run(*cmd):subprocess.run([str(v) for v in cmd],cwd=project,check=True)
    if args.action=='prepare':
        (project/'source-info.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
        for i,q in enumerate([.1,.5,.9]):run(ff,'-y','-v','error','-ss',info['duration']*q,'-i',source,'-frames:v','1',f'source_{i}.png')
        if not info['has_audio']:
            (project/'transcript.jsonl').write_text('',encoding='utf-8');print('Silent input: create captions only from supplied text');return
        run(ff,'-y','-v','error','-i',source,'-vn','-ar','16000','-ac','1','audio.wav')
        from faster_whisper import WhisperModel
        model=WhisperModel(os.environ.get('EDIT_WHISPER_MODEL','small'),device='cpu',compute_type='int8')
        segments,_=model.transcribe(str(project/'audio.wav'),word_timestamps=True,language=os.environ.get('EDIT_LANGUAGE') or None)
        with (project/'transcript.jsonl').open('w',encoding='utf-8') as f:
            for s in segments:f.write(json.dumps(dict(start=s.start,end=s.end,text=s.text,words=[dict(start=w.start,end=w.end,text=w.word) for w in s.words or []]),ensure_ascii=False)+'\n')
        print('Prepared. Codex must now author and proofread edit-plan.json.');return
    plan=json.loads((project/'edit-plan.json').read_text(encoding='utf-8-sig'))
    plan.update(source=str(source),source_size=info['source_size'],duration=info['duration'],fps=60)
    for a in plan.get('assets',{}).values():
        p=Path(a['path']);p=p if p.is_absolute() else project/p
        if a['type']=='video':
            ai=inspect(ff,p);a.update(size=ai['source_size'],duration=ai['duration'])
    validate(plan,project)
    (project/'edit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    if args.action=='validate':print('Plan validation passed');return
    if args.action=='preview':run(sys.executable,'-X','utf8',scripts/'film.py','--stills');return
    run(sys.executable,'-X','utf8',scripts/'film.py')
    inputs=['-i','silent.mp4'];maps=['-map','0:v:0'];audio=[]
    music=plan.get('music',{}).get('mode','none')=='synth'
    if info['has_audio']:inputs+=['-i',str(source)]
    if music:
        run(sys.executable,'-X','utf8',scripts/'sound.py');idx=2 if info['has_audio'] else 1;inputs+=['-i','music.wav']
        if info['has_audio']:
            graph=f'[1:a]asplit=2[voice][key];[{idx}:a][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=300[bg];[voice][bg]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1:LRA=7[a]'
        else:graph=f'[{idx}:a]anull[a]'
        audio=['-filter_complex',graph,'-map','[a]']
    elif info['has_audio']:audio=['-map','1:a:0']
    run(ff,'-y','-v','error',*inputs,*maps,*audio,'-c:v','copy','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t',plan['duration'],'-movflags','+faststart','final_1080p60.mp4')
    run(ff,'-v','error','-xerror','-i','final_1080p60.mp4','-f','null','-')
    out=inspect(ff,project/'final_1080p60.mp4')
    if out['source_size']!=[1920,1080] or out['source_fps']!=60 or abs(out['duration']-plan['duration'])>.05:raise RuntimeError('Output metadata validation failed')
    (project/'export-report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(project/'final_1080p60.mp4')

if __name__=='__main__':main()
