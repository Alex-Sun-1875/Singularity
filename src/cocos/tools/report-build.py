"""Measure a real build; Web gzip is descriptive and is not a Tap package size."""
from pathlib import Path
import gzip,json,sys
from datetime import datetime,timezone
root=Path(sys.argv[1] if len(sys.argv)>1 else 'build/web-desktop')
files=[p for p in root.rglob('*') if p.is_file()]
if not (root/'index.html').exists():
    raise SystemExit('No completed HTML build at '+str(root))
raw=sum(p.stat().st_size for p in files)
gz=sum(len(gzip.compress(p.read_bytes(),compresslevel=6)) for p in files)
bundles={p.name:sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) for p in (root/'assets').iterdir() if p.is_dir()}
report={'measuredAt':datetime.now(timezone.utc).isoformat(),'version':json.loads(Path('package.json').read_text(encoding='utf-8'))['version'],'platform':root.name,'files':len(files),'rawBytes':raw,'gzipBytes':gz,'rawMiB':round(raw/1048576,2),'gzipMiB':round(gz/1048576,2),'bundleBytes':bundles,'note':'Entire Web build, including preserved 3D comparison resources and 2D artwork. Not a TapTap initial package or device performance measurement.'}
Path('test-results').mkdir(exist_ok=True)
Path(sys.argv[2] if len(sys.argv)>2 else 'test-results/build-size.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
