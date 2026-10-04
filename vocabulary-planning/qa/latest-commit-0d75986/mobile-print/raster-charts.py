from pathlib import Path
import json, re, hashlib
import fitz
from PIL import Image
O=Path('/workspace/korean_word/vocabulary-planning/qa/latest-commit-0d75986/mobile-print')
metadata=json.loads((O/'generated-markup-validation.json').read_text());palette=['#087487','#D68220','#C54040','#9AA6AF'];rgb=[tuple(bytes.fromhex(c[1:])) for c in palette];results=[]
for f in metadata['fixtures']:
 s=O/f"donut-{f['name']}.svg";doc=fitz.open(stream=s.read_bytes(),filetype='svg');pix=doc[0].get_pixmap(matrix=fitz.Matrix(3,3));pix.save(O/f"donut-{f['name']}.png");img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);pixels=list(img.getdata());counts=[sum(p==c for p in pixels) for c in rgb];ring=sum(counts);ratios=[n/ring if ring else 0 for n in counts];errors=[abs(a-b) for a,b in zip(ratios,f['expected'])]
 results.append({'fixture':f['name'],'expected_ratios':f['expected'],'raster_ratios':ratios,'max_absolute_error':max(errors),'tolerance':0.003,'status':'PASS' if max(errors)<0.003 else 'FAIL','source_svg_sha256':hashlib.sha256(s.read_bytes()).hexdigest()})
O.joinpath('chart-raster-validation.json').write_text(json.dumps({'method':'MuPDF SVG rasterization of current committed renderDonut output; no HTML/CSS layout or browser printing exercised','results':results,'actual_mobile_and_browser_print':'NOT RUN'},ensure_ascii=False,indent=2));print(json.dumps(results,ensure_ascii=False,indent=2))
