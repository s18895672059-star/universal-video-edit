from functools import lru_cache
from pathlib import Path
import math, os
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W,H=1920,1080
P={}
BLUE='#345deb';TEAL='#269c93';CORAL='#e86e5b';LIME='#d9ff43';GOLD='#dcb66a'
FONT_DIR=Path(os.environ.get('EDIT_FONT_DIR',Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'))
@lru_cache(None)
def f(n,b=True):
    key='EDIT_FONT_BOLD' if b else 'EDIT_FONT_REGULAR'
    path=os.environ.get(key) or str(FONT_DIR/('msyhbd.ttc' if b else 'msyh.ttc'))
    return ImageFont.truetype(path,max(8,n))
@lru_cache(None)
def mono(n):return f(n,False)
@lru_cache(None)
def latin(n):return f(n,True)
def E(t):return 1-(1-max(0,min(1,t)))**3


def mix(a,b,q):return a+(b-a)*q


def text(im,xy,s,n=40,col='#15202b',maxw=None,b=True,ft=None):
 d=ImageDraw.Draw(im)
 while maxw and n>18 and d.textlength(s,font=ft or f(n,b))>maxw:n-=1
 if maxw and d.textlength(s,font=ft or f(n,b))>maxw:raise ValueError('Text overflows layout; shorten the label or widen its container: '+s)
 d.text(xy,s,font=ft or f(n,b),fill=col,anchor='lt')


def rr(im,box,col,r=18,out=None,width=2):ImageDraw.Draw(im).rounded_rectangle(tuple(map(int,box)),radius=r,fill=col,outline=out,width=width)


def line(im,pts,c,w=3):ImageDraw.Draw(im).line(pts,fill=c,width=w,joint='curve')


def arrow(im,x,y,xx,yy,c=BLUE,w=4):
 line(im,[(x,y),(xx,yy)],c,w);a=math.atan2(yy-y,xx-x);ImageDraw.Draw(im).polygon([(xx,yy),(xx-16*math.cos(a-.5),yy-16*math.sin(a-.5)),(xx-16*math.cos(a+.5),yy-16*math.sin(a+.5))],fill=c)


@lru_cache(128)
def shadow(w,h,r):
 z=Image.new('RGBA',(w+80,h+90));ImageDraw.Draw(z).rounded_rectangle((40,35,w+40,h+35),r,fill=(0,0,0,45));return z.filter(ImageFilter.GaussianBlur(17))


def panel(im,x,y,w,h,c='white',r=20,out=None,sh=True):
 x,y,w,h=map(int,(x,y,w,h))
 if sh:im.paste(shadow(w,h,r),(x-40,y-25),shadow(w,h,r))
 rr(im,(x,y,x+w,y+h),c,r,out)


def tag(im,x,y,s,c=BLUE,fg='white',n=24):
 w=int(ImageDraw.Draw(im).textlength(s,font=f(n)))+34;rr(im,(x,y,x+w,y+n+24),c,8);text(im,(x+17,y+10),s,n,fg);return w


@lru_cache(None)
def bg(th):
 c={'light':(248,248,244),'dark':(12,14,18),'tech':(9,18,25),'gold':(15,15,11)}[th]
 yy,xx=np.mgrid[:H,:W];g=np.exp(-((xx-1050)**2/(1100**2)+(yy-530)**2/(650**2)))
 a=np.zeros((H,W,3),np.uint8)
 for j,v in enumerate(c):a[:,:,j]=np.clip(v+g*(2 if th=='light' else 8),0,255)
 im=Image.fromarray(a);d=ImageDraw.Draw(im)
 if th=='light':
  d.polygon([(0,880),(1920,880),(1920,1080),(0,1080)],fill='#eeefed');d.polygon([(0,880),(80,825),(1830,825),(1920,880)],fill='#f3f4f1')
  for x in [64,1856]:rr(im,(x,100,x+22,815),'#fdfdfb',8,out='#eceee9')
 else:
  col='#172129' if th=='tech' else '#1b1c20' if th=='dark' else '#222015'
  for x in range(0,1920,80):line(im,[(x,0),(x,1080)],col,1)
  for y in range(0,1080,80):line(im,[(0,y),(1920,y)],col,1)
  if th=='tech':
   for x in range(-1800,3700,180):line(im,[(960,750),(x,1080)],'#1c2c35',1)
 return im


def icon(im,x,y,typ,col=BLUE):
 d=ImageDraw.Draw(im)
 if typ=='file':
  line(im,[(x,y+4),(x+38,y+4),(x+55,y+20),(x+55,y+69),(x,y+69),(x,y+4)],col,4)
  for yy in [30,42,54]:line(im,[(x+12,y+yy),(x+42,y+yy)],col,3)
 elif typ=='play':d.polygon([(x,y),(x+44,y+28),(x,y+56)],fill=col)
 elif typ=='check':line(im,[(x,y+28),(x+16,y+45),(x+51,y+6)],col,5)
 else:
  for j in range(8):a=j*math.pi/4;line(im,[(x+25+18*math.cos(a),y+25+18*math.sin(a)),(x+25+29*math.cos(a),y+25+29*math.sin(a))],col,3)


def portrait(im,source,box,circle=0,col='#dfe4de'):
 x,y,w,h,r=map(int,box);q=max(0,min(1,circle));crop=tuple(mix(a*540 if j%2==0 else a*960,b*540 if j%2==0 else b*960,q) for j,(a,b) in enumerate(zip(P["crop"],P["avatar_crop"])))
 crop=tuple(v*(source.width/540 if j%2==0 else source.height/960) for j,v in enumerate(crop));v=source.crop(crop);sw,sh=v.size;scale=max(w/sw,h/sh);v=v.resize((math.ceil(sw*scale),math.ceil(sh*scale)),Image.Resampling.LANCZOS);vx=(v.width-w)//2;vy=(v.height-h)//2;v=v.crop((vx,vy,vx+w,vy+h))
 mask=Image.new('L',(w,h));ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),r,fill=255)
 im.paste(shadow(w,h,r),(x-40,y-25),shadow(w,h,r));im.paste(v,(x,y),mask);rr(im,(x,y,x+w,y+h),None,r,col,3)
 if w>340:tag(im,x+18,y+15,'● REC · 原声', '#212b2e','#eef0df',14)


def target(role):
 return {'right':(1375,170,435,655,24,0),'left':(110,165,435,660,24,0),'circle':(1620,108,224,224,112,1),'circle_left':(78,112,224,224,112,1),'center':(830,355,260,260,130,1),'none':(-500,0,1,1,0,0)}[role]
