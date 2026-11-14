"""Copy native image_gen output and record provenance/measurement; never edit pixels."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--raw', type=Path, required=True)
    parser.add_argument('--worker', default='root')
    args = parser.parse_args()
    job = next(j for j in json.loads((HERE/'generation-jobs.json').read_text(encoding='utf8'))['jobs'] if j['image'] == args.image)
    target, master, output = Path(job['editTarget']), Path(job['masterPath']), Path(job['outputPath'])
    if sha(target) != job['sha256']:
        raise ValueError('Frozen edit target changed')
    if args.raw.resolve() == output.resolve():
        raise ValueError('Native original must remain separate')
    template = (HERE/'head-edit.prompt-template.txt').read_text(encoding='utf8').rstrip('\n')
    directions = 'Rows are FRONT, RIGHT PROFILE, BACK, LEFT PROFILE.' if job['layout'][1] == 4 else 'Four2x2cells are FRONT, RIGHT PROFILE, BACK, LEFT PROFILE in reading order.'
    prompt = template.format(headPx=job['targetHeadCrownToChinPixels'], width=job['size'][0], height=job['size'][1], cols=job['layout'][0], rows=job['layout'][1], count=job['layout'][0]*job['layout'][1], directions=directions)
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.raw, output)
    digest = sha(output)
    if digest != sha(args.raw):
        raise ValueError('Native byte copy mismatch')
    prompt_file = output.with_suffix('.prompt.txt')
    prompt_file.write_text(prompt+'\n', encoding='utf8')
    spec = importlib.util.spec_from_file_location('identity_native_measure', HERE.parent/'weapon-carry-v1/measure-install.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    a = helper.alpha(output)
    geometry = None
    error = None
    try:
        if list(a.shape[::-1]) != job['size']:
            raise ValueError('Native canvas dimensions changed')
        geometry = helper.native_geometry(a, job['layout'])
    except ValueError as exc:
        error = str(exc)
    record = {'tool':'built-in image_gen','sourcePath':str(output),'rawOutputPath':str(args.raw.resolve()),'sha256':digest,'rawSourceSHAEqual':True,'pixelEdits':False,'editTarget':str(target),'editTargetSHA256':job['sha256'],'identityMaster':str(master),'identityMasterSHA256':sha(master),'promptFile':str(prompt_file),'promptSHA256':sha(prompt_file),'worker':args.worker,'measurement':geometry,'nativeGeometryError':error,'scope':'Fixed-head identity edit; preserve original body/equipment/action phases. Visual/body-registration review remains required.','status':'generated; pending complete-set measurement and installation'}
    output.with_suffix('.provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'image':args.image,'source':str(output),'sha256':digest,'nativeSize':list(a.shape[::-1]),'alphaBelow16Fraction':float((a<16).mean()),'nativeGeometryError':error},ensure_ascii=False))

if __name__ == '__main__':
    main()
