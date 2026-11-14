"""Read current sprites and retain their geometry/hash inventory, not backups."""
from pathlib import Path
import importlib.util
import json
import sys
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('current_frame_inventory',HERE.parent/'local-qwen21-unified-v3/prepare.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

def main():
    m=json.loads(helper.MANIFEST.read_text(encoding='utf-8-sig'));frames=helper.inventory(m)
    priorities=['explore_idle_W01','idle_W01','explore_run_W01','run_W01','attack_sword_W01','explore_walk_W01','spell']
    def priority(r):return min([priorities.index(v['action']) for v in r['refs'] if v['action'] in priorities] or [len(priorities)])
    records=sorted(frames.values(),key=lambda r:(priority(r),r['di'],r['phase'],r['image']))
    data={'manifestSHA256':helper.digest(helper.MANIFEST),'actions':len(m['actions']),'frames':records,
        'images':[{'image':n,'sha256':helper.digest(helper.ACTOR/n),'metaSHA256':helper.digest(str(helper.ACTOR/n)+'.meta')} for n in sorted({r['image'] for r in records})]}
    (HERE/'inventory.json').write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print({'actions':len(m['actions']),'frames':len(records),'images':len(data['images'])})

if __name__=='__main__':main()
