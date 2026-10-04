from pathlib import Path
import re,json,hashlib,sys
O=Path(__file__).resolve().parent
source=Path(sys.argv[1]) if len(sys.argv)>1 else O.parents[2]/'prototype/pilot-flow.html'
html=source.read_text();css=html.split('<style>',1)[1].split('</style>',1)[0]
variables=dict(re.findall(r'(--[\w-]+):([^;}]+)',css))
def norm(c):
 c=c.strip().lower()
 if c=='white':return '#ffffff'
 if c.startswith('var('):return norm(variables[c[4:-1]])
 if re.fullmatch(r'#[a-f0-9]{3}',c):return '#'+''.join(x*2 for x in c[1:])
 if re.fullmatch(r'#[a-f0-9]{6}',c):return c
 return None
def luminance(c):
 v=[int(c[i:i+2],16)/255 for i in (1,3,5)]
 return sum(w*(t/12.92 if t<=.04045 else ((t+.055)/1.055)**2.4) for w,t in zip([.2126,.7152,.0722],v))
def ratio(a,b):
 x,y=sorted([luminance(a),luminance(b)]);return (y+.05)/(x+.05)
backgrounds=set()
for match in re.finditer(r'background:([^;}]+)',css):
 c=norm(match[1])
 if c and luminance(c)>=.5:backgrounds.add(c)
muted=norm(variables['--muted'])
footer_css=re.search(r'\.report-footer\{([^}]+)\}',css).group(1)
footer=norm(re.search(r'color:([^;}]+)',footer_css).group(1))
svg=O.joinpath('donut-all.svg').read_text() if O.joinpath('donut-all.svg').exists() else ''
svg_fill_match=re.search(r'<text\b[^>]*font-size="12"[^>]*fill="([^"]+)"',svg)
svg_fill=norm(svg_fill_match[1]) if svg_fill_match else None
results=[]
for bg in sorted(backgrounds):
 actual=ratio(muted,bg);results.append({'foreground':muted,'background':bg,'usage':'muted small text, conservative test across all declared opaque light backgrounds','ratio':actual,'minimum':4.5,'status':'PASS' if actual>=4.5 else 'FAIL'})
for usage,fg in [('parent report footer',footer),('donut center small label',svg_fill),('correct answer text',norm(variables['--teal'])),('incorrect answer text',norm(variables['--red']))]:
 actual=ratio(fg,'#ffffff') if fg else 0;results.append({'foreground':fg,'background':'#ffffff','usage':usage,'ratio':actual,'minimum':4.5,'status':'PASS' if actual>=4.5 else 'FAIL'})
summary={'sourceHtmlSha256':hashlib.sha256(html.encode()).hexdigest(),'method':'WCAG relative luminance calculation from edited CSS and generated SVG. Opaque colors only; actual browser compositing, disabled opacity, rendering and exact ancestor backgrounds are unverified. Decorative color dots and borders are excluded.','foreground':muted,'opaqueLightBackgroundCount':len(backgrounds),'results':results,'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results)}
O.joinpath('contrast-calculation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,ensure_ascii=False,indent=2))
if summary['failed']:raise SystemExit(1)
