"""Collect reviewed frame edits using explicit precedence; never install assets."""
from pathlib import Path
import argparse,json
HERE=Path(__file__).resolve().parent

def read(path):
    path=Path(path);data=json.loads(path.read_text(encoding='utf-8-sig'))
    if isinstance(data,dict):data=data.get('edits',data.get('frames',data))
    if isinstance(data,dict):data=[data]
    for row in data:
        r=dict(row);r['cropPath']=str((path.parent/r['cropPath']).resolve())
        yield r

def main():
    p=argparse.ArgumentParser();p.add_argument('--legs');p.add_argument('--cleaned');p.add_argument('--base-only',action='store_true');args=p.parse_args()
    edits={}
    inputs=[HERE/'edits/static/static.json',HERE/'edits/dynamic/edits.json']
    if args.legs:inputs.append(Path(args.legs))
    if args.cleaned:inputs.append(Path(args.cleaned))
    counts=[]
    for source in inputs:
        rows=list(read(source));counts.append({'source':str(source),'frames':len(rows)})
        for r in rows:edits[(r['image'],r['index'])]=r
    out=HERE/('costume-edits.json' if args.base_only else 'edits/final.json')
    out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(list(edits.values()),ensure_ascii=False,indent=2),encoding='utf-8')
    print({'output':str(out),'uniqueFrames':len(edits),'inputs':counts})

if __name__=='__main__':main()
