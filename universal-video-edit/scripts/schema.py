from pathlib import Path
import math

KINDS={'hook','cards','bullets','steps','chat','file','timeline','collection','styles','comparison','metric','quote','code','orbit','curve','media','triptych','player','interaction','gallery','end','stamp'}
ROLES={'left','right','circle','circle_left','center','none'}

def require(condition,message):
    if not condition: raise ValueError(message)

def crop_ok(v):
    return len(v)==4 and 0<=v[0]<v[2]<=1 and 0<=v[1]<v[3]<=1

def validate(p,base):
    require(p.get('version')==2,'Plan version must be 2')
    require(p.get('fps',60)==60,'This renderer uses 60 fps')
    require(p.get('output_size',[1920,1080])==[1920,1080],'This renderer supports 1920x1080; other formats require a new layout')
    for key in ['crop','avatar_crop']: require(crop_ok(p[key]),f'Invalid normalized {key}')
    scenes=p['scenes']; require(bool(scenes),'Empty scenes')
    require(scenes[0]['start']==0 and abs(scenes[-1]['end']-p['duration'])<.035,'Scenes must cover the complete source')
    assets=p.get('assets',{})
    for key,a in assets.items():
        path=Path(a['path']); path=path if path.is_absolute() else base/path
        require(path.is_file(),f'Missing asset {key}: {path}')
        require(a.get('type') in ('image','video'),f'Invalid asset type: {key}')
        if a['type']=='video': require(a.get('size') and a.get('duration',0)>0,f'Video asset {key} needs display size and duration')
    for i,s in enumerate(scenes):
        k=s['kind']; require(k in KINDS,f'Unknown kind {k}')
        require(s['portrait'] in ROLES,f'Invalid portrait at scene {i}')
        require(s['end']>s['start'] and (i==0 or abs(scenes[i-1]['end']-s['start'])<.001),f'Timeline gap/overlap at {i}')
        require(s.get('theme','light') in ('light','dark','tech','gold'),f'Invalid theme at {i}')
        require(s.get('transition','cut') in ('cut','fade','wipe','circle'),f'Invalid transition at {i}')
        require(0<s.get('transition_duration',.35)<=s['end']-s['start'],f'Transition too long at {i}')
        require(isinstance(s.get('title'),str),f'Missing title at {i}')
        for key in ['crop','avatar_crop']:
            if key in s: require(crop_ok(s[key]),f'Invalid scene {key}')
        for aid in s.get('media',[]): require(aid in assets,f'Unknown asset {aid}')
        if k in ('media','player'): require(len(s.get('media',[]))==1,f'{k} requires one real asset')
        if k=='triptych':
            require(len(s.get('media',[]))==3 and len(set(s['media']))==3,'Triptych needs three distinct asset IDs')
            require(len({str(assets[a]['path']) for a in s['media']})==3,'Triptych needs three distinct files, not copies of one clip')
        if k=='player':
            require(s.get('screen') in assets and assets[s['screen']]['type']=='image','Player needs a genuine screen image')
            require(crop_ok(s.get('player_box',[])),'Player needs normalized player_box within screen')
        if k=='gallery': require(i+1<len(scenes) and scenes[i+1]['kind'] not in ('gallery','hook','collection'),'Gallery must lead into a concrete scene')
        if k=='curve':
            require(len(s.get('values',[]))>=2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in s['values']),'Curve requires actual numeric values')
            require(bool(s.get('data_note')),'Curve needs source/illustration note')
        if k=='metric': require(isinstance(s.get('value'),(float,int)) and bool(s.get('data_note')),'Metric needs numeric value and source note')
        if k in ('hook','collection','gallery'): require(any(v['kind'] not in ('hook','collection','gallery') for v in scenes),'Preview wall needs concrete scenes')
        if k=='interaction': require(s['portrait']=='center','Interaction uses center portrait')
        elif s['portrait']=='center': require(False,'Center portrait is reserved for interaction')
        if k=='triptych': require(s['portrait']=='none','Triptych replaces speaker window')
        if k in ('cards','steps','comparison','styles','bullets','chat','file','interaction'):
            limits={'cards':3,'steps':6,'comparison':3,'styles':3,'bullets':4,'chat':3,'file':3,'interaction':2}
            require(1<=len(s.get('items',[]))<=limits[k],f'Invalid item count for {k}')
    last=0
    for c in p.get('captions',[]):
        require(last<=c['start']<c['end']<=p['duration']+.02,'Caption time invalid/overlap')
        last=c['end']; require(isinstance(c['zh'],str),'Caption zh must be text')
        for key,field in [('highlights','zh'),('en_highlights','en')]:
            for h in c.get(key,[]):
                require(c['start']<=h['start']<h['end']<=c['end'],'Highlight time outside caption')
                require(0<=h['a']<h['b']<=len(c.get(field,'')),'Highlight character range invalid')
    require(p.get('music',{}).get('mode','none') in ('none','synth'),'music.mode must be none or synth')

