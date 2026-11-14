"""Execute prepared native ComfyUI mask graphs against localhost only."""
from pathlib import Path
import argparse
import json
import shutil
import time
import urllib.request
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parent
COMFY = Path(r"F:\Models\ComfyUI_windows_portable\ComfyUI")
RESEARCH = Path(r"F:\Models\deployment-research")
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(path, body=None):
    request = urllib.request.Request("http://127.0.0.1:8188" + path,
        data=None if body is None else json.dumps(body).encode(), headers={"Content-Type":"application/json"})
    with HTTP.open(request, timeout=20) as response:
        return json.load(response)


def run(case):
    name = case["name"]
    source = Path(case["directory"])
    output = ROOT / "results" / name
    output.mkdir(parents=True, exist_ok=True)
    graph_name = "klein-4b-consistency-mask-" + ("single" if case["single_reference"] else "two") + "-reference-api.json"
    graph = json.loads((RESEARCH / graph_name).read_text(encoding="utf-8-sig"))
    local_inputs = COMFY / "input" / "consistency-trial" / name
    local_inputs.mkdir(parents=True, exist_ok=True)
    for file in ["guide.png", "noise-mask.png"] + ([] if case["single_reference"] else ["reference.png"]):
        shutil.copy2(source / file, local_inputs / file)
    graph["4"]["inputs"]["image"] = "consistency-trial/"+name+"/guide.png"
    graph["25"]["inputs"]["image"] = "consistency-trial/"+name+"/noise-mask.png"
    if not case["single_reference"]:
        graph["5"]["inputs"]["image"] = "consistency-trial/"+name+"/reference.png"
    graph["9"]["inputs"]["text"] = (source / "prompt.txt").read_text(encoding="utf-8")
    graph["21"]["inputs"]["noise_seed"] = case["seed"]
    graph["26"]["inputs"]["step"] = case["skip_steps"]
    graph["24"]["inputs"]["filename_prefix"] = "consistency-trial/"+name
    (output / "workflow-api.json").write_text(json.dumps(graph,indent=2),encoding="utf-8")
    started = time.monotonic()
    submission = api("/prompt", {"prompt":graph,"client_id":"consistency-local"})
    (output / "submission.json").write_text(json.dumps(submission,indent=2),encoding="utf-8")
    if submission.get("node_errors"):
        raise RuntimeError(submission["node_errors"])
    prompt_id = submission["prompt_id"]
    print("Queued", name, prompt_id, flush=True)
    for _ in range(360):
        records = api("/history/"+prompt_id)
        if prompt_id not in records:
            time.sleep(2)
            continue
        history = records[prompt_id]
        (output / "history.json").write_text(json.dumps(history,indent=2),encoding="utf-8")
        if history.get("status",{}).get("status_str") != "success":
            raise RuntimeError("Local model failed; see "+str(output / "history.json"))
        images=[item for value in history["outputs"].values() for item in value.get("images",[])]
        if not images:
            raise RuntimeError("No model image output")
        item=images[0]
        raw_path=COMFY/"output"/item.get("subfolder","")/item["filename"]
        shutil.copy2(raw_path,output/"raw-model.png")
        generated=Image.open(raw_path).convert("RGB")
        guide=Image.open(source/"guide.png").convert("RGB")
        mask=Image.open(source/"composite-mask.png").convert("L")
        if generated.size!=guide.size:
            raise RuntimeError("Unexpected model dimensions")
        composite=Image.composite(generated,guide,mask)
        composite.save(output/"candidate.png")
        frozen=np.asarray(mask)==0
        assert np.array_equal(np.asarray(composite)[frozen],np.asarray(guide)[frozen])
        report={"case":name,"prompt_id":prompt_id,"elapsed_seconds":round(time.monotonic()-started,2),"size":list(composite.size),"outside_mask_equal_to_guide":True,"local_endpoint":"127.0.0.1:8188","proxy_used":False,"cloud_generation":False,"production_modified":False,"status":"awaiting visual review","guide_notes":case["notes"]}
        (output/"result.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
        print(json.dumps(report),flush=True)
        return
    raise TimeoutError("Prompt still running; inspect queue before resubmitting")


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--case")
    args=parser.parse_args()
    cases=json.loads((ROOT/"cases.json").read_text(encoding="utf-8"))
    for case in cases:
        if args.case is None or case["name"]==args.case:
            run(case)
