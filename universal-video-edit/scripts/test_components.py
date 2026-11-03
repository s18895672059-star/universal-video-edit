"""Create synthetic fixtures and exercise every component without any user footage."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw
from edit import ffmpeg

def main():
    ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);ap.add_argument('--render',action='store_true');args=ap.parse_args()
    project=args.project.resolve();project.mkdir(parents=True,exist_ok=True)
    if (project/'edit-plan.json').exists():raise ValueError('Use an empty test project to avoid overwriting your edit plan')
    pkg=Path(__file__).resolve().parent.parent;media=project/'media';media.mkdir(exist_ok=True);ff=ffmpeg();os.environ['EDIT_FFMPEG']=ff
    def run(*cmd):subprocess.run([str(v) for v in cmd],check=True)
    source=project/'source.mp4'
    run(ff,'-y','-v','error','-f','lavfi','-i','testsrc2=size=640x960:rate=15','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','44','-c:v','libx264','-preset','fast','-crf','18','-c:a','aac',source)
    for i,c in enumerate('abc'):
        run(ff,'-y','-v','error','-f','lavfi','-i',f'testsrc2=size=320x480:rate=15,hue=h={i*90}','-t','3','-an','-c:v','libx264','-preset','fast',media/f'{c}.mp4')
    im=Image.new('RGB',(1000,700),'#303842');d=ImageDraw.Draw(im);d.rectangle((150,140,850,595),fill='black');d.text((20,20),'SYNTHETIC TEST SCREEN',fill='white');im.save(media/'screen.png')
    p=json.loads((pkg/'examples/component-catalog.json').read_text(encoding='utf-8'))
    (project/'edit-plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    run(sys.executable,'-X','utf8',pkg/'scripts/edit.py','preview',source,project)
    if args.render:run(sys.executable,'-X','utf8',pkg/'scripts/edit.py','render',source,project)
    print('Synthetic component test completed:',project)

if __name__=='__main__':main()
