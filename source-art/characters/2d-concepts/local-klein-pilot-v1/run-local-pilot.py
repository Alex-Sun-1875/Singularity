"""Run the official native Klein two-reference graph against localhost only."""
import argparse
import json
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = Path(r"F:\Models")
COMFY = MODELS / "ComfyUI_windows_portable" / "ComfyUI"
BASE = "http://127.0.0.1:8188"
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def api(path, payload=None, timeout=15):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with HTTP.open(request, timeout=timeout) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--megapixels", type=float, default=0.375)
    parser.add_argument("--seed", type=int, default=1707)
    parser.add_argument("--name", default="running-head-reference")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--input-image", default="running-right-input.png")
    parser.add_argument("--reference-image", default="standing-right-input.png")
    parser.add_argument("--prompt-file", default="pilot-prompt.txt")
    args = parser.parse_args()
    destination = ROOT / "results" / args.name
    destination.mkdir(parents=True, exist_ok=True)
    input_directory = COMFY / "input" / "local-klein-pilot"
    input_directory.mkdir(parents=True, exist_ok=True)
    for source_name, role in ((args.input_image, "main"), (args.reference_image, "reference")):
        shutil.copy2(ROOT / source_name, input_directory / (args.name + "-" + role + ".png"))
    workflow = json.loads((MODELS / "deployment-research" / "klein-4b-two-reference-api-3080.json").read_text(encoding="utf-8-sig"))
    workflow["4"]["inputs"]["image"] = "local-klein-pilot/" + args.name + "-main.png"
    workflow["5"]["inputs"]["image"] = "local-klein-pilot/" + args.name + "-reference.png"
    for node in ("6", "7"):
        workflow[node]["inputs"]["megapixels"] = args.megapixels
    prompt = (ROOT / args.prompt_file).read_text(encoding="utf-8")
    workflow["9"]["inputs"]["text"] = prompt
    workflow["21"]["inputs"]["noise_seed"] = args.seed
    workflow["24"]["inputs"]["filename_prefix"] = "local-klein-pilot/" + args.name
    (destination / "workflow-api.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    (destination / "prompt.txt").write_text(prompt, encoding="utf-8")
    started = time.monotonic()
    response = api("/prompt", {"prompt": workflow, "client_id": "local-klein-pilot"})
    (destination / "submission.json").write_text(json.dumps(response, indent=2), encoding="utf-8")
    if response.get("node_errors"):
        raise RuntimeError(json.dumps(response["node_errors"]))
    prompt_id = response["prompt_id"]
    print("Queued local inference:", prompt_id, flush=True)
    while time.monotonic() - started < args.timeout:
        history = api("/history/" + prompt_id)
        if prompt_id in history:
            record = history[prompt_id]
            (destination / "history.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
            if record.get("status", {}).get("status_str") != "success":
                raise RuntimeError("Local inference failed; see " + str(destination / "history.json"))
            outputs = []
            for node in record.get("outputs", {}).values():
                for item in node.get("images", []):
                    source = COMFY / "output" / item.get("subfolder", "") / item["filename"]
                    target = destination / item["filename"]
                    shutil.copy2(source, target)
                    outputs.append(str(target))
            if not outputs:
                raise RuntimeError("Inference returned no saved image")
            report = {"completed_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.monotonic() - started, 2), "prompt_id": prompt_id, "megapixels": args.megapixels, "seed": args.seed, "endpoint": BASE, "proxy_used": False, "cloud_image_generation": False, "outputs": outputs}
            (destination / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2), flush=True)
            return
        time.sleep(5)
    raise TimeoutError("Local inference remains queued/running; inspect localhost history before resubmitting")


if __name__ == "__main__":
    main()
