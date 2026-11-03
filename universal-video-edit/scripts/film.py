from pathlib import Path
import os,json,math,bisect,subprocess,sys,time
from PIL import Image,ImageDraw,ImageFilter
import drawing as D
from drawing import E,mix,text,rr,line,arrow,panel,tag,icon,portrait,target,f
from media import Media

B=Path.cwd();P=json.loads((B/'edit-plan.json').read_text(encoding='utf-8'));D.P=P
W,H=1920,1080;FF=os.environ['EDIT_FFMPEG'];FPS=60
M=Media(P.get('assets',{}),B,FF);THUMBS={}
STARTS=[s['start'] for s in P['scenes']]

def fit(im,box,mode='contain'):
    x,y,w,h=map(int,box);r=(max if mode=='cover' else min)(w/im.width,h/im.height)
    im=im.resize((max(1,round(im.width*r)),max(1,round(im.height*r))),Image.Resampling.LANCZOS)
    if mode=='cover':
        xx=(im.width-w)//2;yy=(im.height-h)//2;return im.crop((xx,yy,xx+w,yy+h)),(x,y)
    return im,(x+(w-im.width)//2,y+(h-im.height)//2)

def put_media(im,s,aid,box,u,static=False):
    source=M.get(aid,0 if static else u,static)
    pic,xy=fit(source,box,s.get('media_fit','contain'));im.paste(pic,xy)

def speaker(im,src,s,u,i):
    role=s['portrait']
    if role=='none':return
    old=target(P['scenes'][i-1]['portrait']) if i else target(role)
    new=target(role)
    if old[2]<10:old=new
    q=E((u-s.get('portrait_delay',.04))/max(.01,s.get('portrait_duration',.4)))
    v=[mix(a,b,q) for a,b in zip(old,new)]
    saved=D.P;D.P={**P,'crop':s.get('crop',P['crop']),'avatar_crop':s.get('avatar_crop',P['avatar_crop'])}
    portrait(im,src,v[:5],v[5],s.get('accent','#269c93'));D.P=saved

def thumbnail(j,src):
    candidates=[i for i,s in enumerate(P['scenes']) if s['kind'] not in ('hook','collection','gallery')]
    idx=candidates[j%len(candidates)]
    if idx not in THUMBS:
        s=P['scenes'][idx];THUMBS[idx]=scene(idx,s['start']+min(2,(s['end']-s['start'])/2),src,True)
    return THUMBS[idx]

def gallery(i,t,src,static):
    s=P['scenes'][i];u=t-s['start'];duration=s['end']-s['start'];wall=Image.new('RGB',(W,H),'#10171c')
    for j in range(15):
        x=80+j%5*355;y=65+j//5*292
        if j==7:
            nxt=P['scenes'][i+1];thumb=scene(i+1,nxt['start'],src,True)
        else:thumb=thumbnail(j,src)
        wall.paste(thumb.resize((330,186),Image.Resampling.LANCZOS),(x,y))
    phase=u/duration;sel=7 if phase>.35 else int(phase*36)%15
    x=80+sel%5*355;y=65+sel//5*292
    rr(wall,(x-4,y-4,x+334,y+190),None,5,s.get('accent','#269c93'),4)
    q=E((phase-.35)/.28);z=mix(1,1.65,q);cx=mix(960,955,q);cy=mix(540,450,q)
    view=wall.crop((cx-W/2/z,cy-H/2/z,cx+W/2/z,cy+H/2/z)).resize((W,H),Image.Resampling.LANCZOS)
    if phase>.68:
        q=E((phase-.68)/.32);nxt=P['scenes'][i+1]
        child=scene(i+1,nxt['start'],src,static);w=round(mix(545,W,q));h=round(w*H/W)
        view.paste(child.resize((w,h),Image.Resampling.LANCZOS),((W-w)//2,(H-h)//2))
    elif s.get('title'):text(view,(120,960),s['title'],36,'white',maxw=1600)
    return view

def scene(i,t,src,static=False):
    s=P['scenes'][i];k=s['kind'];u=max(0,t-s['start'])
    if k=='gallery':return gallery(i,t,src,static)
    theme=s.get('theme','light');im=D.bg(theme).copy();light=theme=='light'
    ink='#17212a' if light else '#f5f5ed';accent=s.get('accent','#269c93' if light else '#dcb66a')
    card='#ffffff' if light else '#172833';edge='#d4dfdd' if light else '#46606b'
    x=650 if s['portrait']=='left' else 115
    right=1315 if s['portrait']=='right' else 1800;cw=right-x
    tx=360 if s['portrait']=='circle_left' else x
    tw=min(right,1550 if s['portrait']=='circle' else right)-tx
    offset=round(28*(1-E((u-s.get('title_delay',0))/.35)))
    if u>=s.get('title_delay',0):
        if s.get('eyebrow'):text(im,(tx,104+offset),s['eyebrow'],22,accent,maxw=tw)
        text(im,(tx,155+offset),s['title'],64,ink,maxw=tw)
        if s.get('sub'):text(im,(tx,252+offset),s['sub'],28,accent,maxw=tw)
    items=s.get('items',[]);start=s.get('content_delay',.45);du=u-start
    if k in ('cards','comparison','styles','steps','file'):
        count=len(items);gap=24;ww=(cw-(count-1)*gap)/max(1,count)
        for j,label in enumerate(items):
            if du<j*s.get('stagger',.18):continue
            y=405+round(35*(1-E((du-j*s.get('stagger',.18))/.4)))
            xx=x+j*(ww+gap);panel(im,xx,y,ww,300,card,out=edge)
            if k=='file':icon(im,xx+25,y+28,'file',accent)
            elif k=='styles':
                ImageDraw.Draw(im).ellipse((xx+ww/2-55,y+30,xx+ww/2+55,y+140),outline=accent,width=4)
            else:text(im,(xx+24,y+24),f'{j+1:02}',42,accent,maxw=ww-48)
            text(im,(xx+24,y+178),label,42,ink,maxw=ww-48)
            if k=='steps' and j<count-1:arrow(im,xx+ww+3,y+125,xx+ww+gap-3,y+125,accent,3)
    elif k=='bullets':
        for j,label in enumerate(items):
            if du<j*.22:continue
            yy=360+j*108;tag(im,x,yy,str(j+1),accent,n=25);text(im,(x+85,yy+7),label,40,ink,maxw=cw-100)
    elif k=='chat':
        panel(im,x,350,cw,445,card,out=edge)
        for j,label in enumerate(items):
            count=max(0,int((du-j*.75)*s.get('typing_speed',14)))
            if count:text(im,(x+35,390+j*115),label[:count]+('▌' if count<len(label) else ''),36,ink,maxw=cw-70)
    elif k=='timeline':
        tracks=items or ['','',''];cols=[accent,'#7b8793','#b89a76']
        panel(im,x,350,cw,440,card,out=edge)
        for j,label in enumerate(tracks[:3]):
            text(im,(x+25,398+j*110),label,26,ink,maxw=130)
            for z in range(7):
                q=E((du-j*.2-z*.08)/.35);left=x+180+z*(cw-215)/7
                if q:rr(im,(left,390+j*110,left+max(1,((cw-240)/7)*q),450+j*110),cols[j],6)
        q=max(0,min(1,du/max(.1,s['end']-s['start']-start)))
        line(im,[(x+180+(cw-215)*q,370),(x+180+(cw-215)*q,765)],accent,3)
    elif k in ('hook','collection'):
        cols=3 if k=='hook' else 2;rows=2;ww=(cw-24*(cols-1))/cols;hh=ww*9/16
        hh=min(hh,190)
        for j in range(cols*rows):
            if du<j*.09:continue
            pic=thumbnail(j,src);xx=x+j%cols*(ww+24);yy=365+j//cols*(hh+35)
            tile,xy=fit(pic,(xx,yy,ww,hh));im.paste(tile,xy)
    elif k=='metric':
        q=E(max(0,du)/1.1);value=s['value']*q
        label=f"{s.get('prefix','')}{value:,.{s.get('decimals',0)}f}{s.get('suffix','')}"
        text(im,(x,390),label,180,accent,maxw=cw)
        text(im,(x,720),s['data_note'],25,ink,maxw=cw)
    elif k in ('quote','end','stamp'):
        body=s.get('body','');font=100 if k=='end' else 76
        text(im,(x,430),body,font,ink,maxw=cw)
        if k=='stamp':
            label=s.get('stamp','');lay=Image.new('RGBA',(700,160));rr(lay,(3,3,696,156),None,8,accent,5);text(lay,(25,35),label,65,accent,maxw=645)
            lay=lay.rotate(-10,resample=Image.Resampling.BICUBIC,expand=True);im.paste(lay,(x,590),lay)
        elif s.get('footer'):text(im,(x,690),s['footer'],34,accent,maxw=cw)
    elif k=='code':
        panel(im,x,350,cw,445,card,out=edge)
        for j,label in enumerate(s.get('lines',[])[:7]):
            if du>j*.25:text(im,(x+32,380+j*52),label,29,accent,maxw=cw-64,b=False)
    elif k=='orbit':
        cx=x+cw*.65;cy=555;d=ImageDraw.Draw(im)
        for j,r in enumerate([85,125,165]):d.arc((cx-r,cy-r,cx+r,cy+r),int(u*25+j*70),int(u*25+j*70+245),fill=accent,width=3)
        d.ellipse((cx-45,cy-45,cx+45,cy+45),fill=accent)
        for j,label in enumerate(items[:3]):text(im,(x,400+j*115),label,36,ink,maxw=cw*.42)
    elif k=='curve':
        vals=s['values'];lo=min(vals);hi=max(vals);span=max(1e-6,hi-lo)
        box=(x+40,390,cw-80,320);xx,yy,ww,hh=box;line(im,[(xx,yy),(xx,yy+hh),(xx+ww,yy+hh)],edge,3)
        pts=[(xx+j*ww/(len(vals)-1),yy+hh-(v-lo)/span*hh) for j,v in enumerate(vals)]
        progress=E(max(0,du)/1.6)*(len(pts)-1);n=int(progress);shown=pts[:n+1]
        if n<len(pts)-1:shown.append(tuple(mix(a,b,progress-n) for a,b in zip(pts[n],pts[n+1])))
        if len(shown)>1:line(im,shown,accent,6)
        text(im,(x,750),s['data_note'],25,ink,maxw=cw)
        text(im,(x,345),f'{hi:g}',20,ink);text(im,(x,715),f'{lo:g}',20,ink)
    elif k in ('media','triptych','player'):
        if k=='triptych':
            ww=(cw-40)/3
            for j,aid in enumerate(s['media']):
                if du<j*.18:continue
                xx=x+j*(ww+20);yy=350+round(55*(1-E((du-j*.18)/.4)))
                put_media(im,s,aid,(xx,yy,ww,480),max(0,du-j*.18),static)
        elif k=='player':
            screen=M.get(s['screen'],0,True);screen,xy=fit(screen,(x,330,cw,490))
            a,b,c,d=s['player_box'];box=(xy[0]+a*screen.width,xy[1]+b*screen.height,(c-a)*screen.width,(d-b)*screen.height)
            im.paste(screen,xy);put_media(im,s,s['media'][0],box,max(0,du),static)
        else:put_media(im,s,s['media'][0],(x,330,cw,490),max(0,du),static)
    elif k=='interaction':
        for j,label in enumerate(items):
            xx=290 if j==0 else 1200;panel(im,xx,430,400,160,card,out=edge);text(im,(xx+30,480),label,40,ink,maxw=340)
        if .8<du<2:
            for j in range(28):
                xx=(j*317)%W;yy=300+(j*43)%200+(du-.8)*280;rr(im,(xx,yy,xx+7,yy+12),accent,1)
    speaker(im,src,s,u,i)
    if P.get('brand'):text(im,(70,45),P['brand'],20,accent,maxw=1650,b=False)
    return im

def caption_line(im,label,highlights,t,y,size,width):
    if not label:return
    d=ImageDraw.Draw(im)
    while size>18 and d.textlength(label,font=f(size))>width:size-=1
    if d.textlength(label,font=f(size))>width:raise ValueError('Caption too long: split into shorter phrases')
    x=(W-d.textlength(label,font=f(size)))/2
    spans=[h for h in highlights if h['start']<=t<h['end']]
    for j,ch in enumerate(label):
        active=any(h['a']<=j<h['b'] for h in spans)
        d.text((x,y),ch,font=f(size),fill=P.get('caption_accent','#e86e5b') if active else 'white',stroke_width=3 if size>30 else 2,stroke_fill='#20252a',anchor='lt');x+=d.textlength(ch,font=f(size))

def frame(t,src):
    i=max(0,bisect.bisect_right(STARTS,t)-1);s=P['scenes'][i];im=scene(i,t,src);u=t-s['start'];dur=s.get('transition_duration',.35)
    transition=s.get('transition','cut')
    if i and u<dur and transition!='cut' and P['scenes'][i-1]['kind']!='gallery':
        old=P['scenes'][i-1];prev=scene(i-1,max(old['start'],old['end']-1/60),src,True);q=E(u/dur)
        if transition=='fade':im=Image.blend(prev,im,q)
        else:
            mask=Image.new('L',(W,H));d=ImageDraw.Draw(mask)
            if transition=='wipe':d.rectangle((0,0,int(W*q),H),fill=255)
            else:
                r=math.hypot(W,H)/2*q;d.ellipse((W/2-r,H/2-r,W/2+r,H/2+r),fill=255)
            im=Image.composite(im,prev,mask)
    for c in P.get('captions',[]):
        if c['start']<=t<c['end']:
            caption_line(im,c['zh'],c.get('highlights',[]),t,925,46,1670)
            caption_line(im,c.get('en',''),c.get('en_highlights',[]),t,990,25,1710);break
    return im

def source_still(t):
    raw=subprocess.check_output([FF,'-v','error','-ss',str(t),'-i',P['source'],'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
    return Image.frombytes('RGB',tuple(P['source_size']),raw)

if __name__=='__main__':
    try:
        if '--stills' in sys.argv:
            qa=B/'qa';qa.mkdir(exist_ok=True);count=0
            for i,s in enumerate(P['scenes']):
                for j,offset in enumerate([.12,min(.6,(s['end']-s['start'])/2),(s['end']-s['start'])*.85]):
                    t=min(s['end']-1/60,s['start']+offset);frame(t,source_still(t)).save(qa/f'{i:02}_{j}_{s["kind"]}.jpg',quality=94);count+=1
            print(f'{count} native-source preview frames written to {qa}',flush=True)
        else:
            dec=subprocess.Popen([FF,'-v','error','-i',P['source'],'-vf','fps=60','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE)
            enc=subprocess.Popen([FF,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','60','-i','pipe:0','-an','-c:v','libx264','-preset','slow','-crf','12','-threads','8','-vf','scale=out_color_matrix=bt709:out_range=tv','-pix_fmt','yuv420p','-profile:v','high','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',str(B/'silent.mp4')],stdin=subprocess.PIPE)
            n=math.ceil(P['duration']*60);size=math.prod(P['source_size'])*3;src=None
            try:
                for j in range(n):
                    raw=dec.stdout.read(size)
                    if len(raw)==size:src=Image.frombytes('RGB',tuple(P['source_size']),raw)
                    elif src is None or j<n-2:raise RuntimeError(f'Source ended at {j}/{n}')
                    enc.stdin.write(frame(j/60,src).tobytes())
                    if j%300==0:print(f'{j}/{n} frames',flush=True)
            finally:
                enc.stdin.close();enc.wait();dec.terminate();dec.stdout.close();dec.wait()
            if enc.returncode:raise RuntimeError('Encoder failed')
            print(f'Rendered {n} frames',flush=True)
    finally:M.close()
