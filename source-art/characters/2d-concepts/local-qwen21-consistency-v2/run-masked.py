"""Local Qwen 2.1 Turbo masked retouch adapter; no cloud generation.

Original-pixel geometry guides and reviewed masks are prepared separately.
This runner records actual native inference and leaves raw output untouched.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parent
COMFY = Path(r"F:\Models\ComfyUI_windows_portable\ComfyUI")
URL = "http://127.0.0.1:8188"
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SIGMAS = "1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0"


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def api(path, body=None):
    req = urllib.request.Request(URL + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with HTTP.open(req, timeout=30) as response:
        return json.load(response)


def node(class_type, **inputs):
    return {"class_type": class_type, "inputs": inputs}


def local_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def run(case):
    name = case["name"]
    out = ROOT / "results" / name
    out.mkdir(parents=True, exist_ok=True)
    if (out / "result.json").exists() or (out / "submission.json").exists():
        raise RuntimeError("Inspect the existing job before reusing this case name: " + name)
    input_dir = COMFY / "input" / "qwen21-consistency-v2" / name
    input_dir.mkdir(parents=True, exist_ok=True)
    provenance = {}
    for role in ["guide", "mask", "reference"]:
        if not case.get(role):
            continue
        source = local_path(case[role])
        with Image.open(source) as image:
            if image.size != (512, 768):
                raise ValueError("Expected fixed 512x768 prepared canvas: " + str(source))
            if role != "mask" and image.mode != "RGBA":
                raise ValueError("Expected true RGBA: " + str(source))
            if role == "mask" and image.convert("L").getextrema()[1] == 0:
                raise ValueError("Empty edit mask")
        shutil.copy2(source, input_dir / (role + ".png"))
        shutil.copy2(source, out / ("input-" + role + ".png"))
        provenance[role] = {"path": str(source.resolve()), "snapshot": str(out / ("input-" + role + ".png")), "sha256": digest(source)}
    prompt = local_path(case["prompt"]).read_text(encoding="utf-8").strip()
    graph = {
        "1": node("UNETLoader", unet_name="qwen_image_2.1_turbo_int8_convrot.safetensors", weight_dtype="default"),
        "2": node("CLIPLoader", clip_name="qwen3vl_8b_int8_convrot.safetensors", type="qwen_image", device="cpu"),
        "3": node("VAELoader", vae_name="qwen_image_2.1_vae_bf16.safetensors"),
        "4": node("LoadImage", image=f"qwen21-consistency-v2/{name}/guide.png"),
        "6": node("JoinImageWithAlpha", image=["4", 0], alpha=["4", 1]),
        "8": node("TextEncodeQwenImage21", clip=["2", 0], vae=["3", 0], prompt=prompt,
                  negative_prompt="", resolution=0, **{"images.image_1": ["6", 0]}),
        "9": node("QwenImage21Cache", model=["1", 0], device="cpu", dtype="default"),
        "10": node("CFGGuider", model=["9", 0], positive=["8", 0], negative=["8", 1], cfg=1),
        "11": node("RandomNoise", noise_seed=case.get("seed", 20261107)),
        "12": node("KSamplerSelect", sampler_name="euler"),
        "13": node("ManualSigmas", sigmas=SIGMAS),
        "14": node("SamplerCustomAdvanced", noise=["11", 0], guider=["10", 0], sampler=["12", 0],
                   sigmas=["13", 0], latent_image=["20", 0]),
        "15": node("VAEDecode", samples=["14", 0], vae=["3", 0]),
        "16": node("SaveImage", images=["15", 0], filename_prefix="qwen21-consistency-v2/" + name),
        "17": node("VAEEncode", pixels=["6", 0], vae=["3", 0]),
        "18": node("LoadImageMask", image=f"qwen21-consistency-v2/{name}/mask.png", channel="red"),
        "20": node("SetLatentNoiseMask", samples=["17", 0], mask=["18", 0]),
    }
    if case.get("reference"):
        graph["5"] = node("LoadImage", image=f"qwen21-consistency-v2/{name}/reference.png")
        graph["7"] = node("JoinImageWithAlpha", image=["5", 0], alpha=["5", 1])
        graph["8"]["inputs"]["images.image_2"] = ["7", 0]
    (out / "workflow-api.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    try:
        submitted = api("/prompt", {"prompt": graph, "client_id": "raphael-qwen21-consistency-v2"})
    except urllib.error.HTTPError as error:
        (out / "submission-error.txt").write_text(error.read().decode("utf-8", errors="replace"), encoding="utf-8")
        raise
    (out / "submission.json").write_text(json.dumps(submitted, indent=2), encoding="utf-8")
    if submitted.get("node_errors") or not submitted.get("prompt_id"):
        raise RuntimeError("Graph rejected: " + str(submitted))
    prompt_id = submitted["prompt_id"]
    print("Queued", name, prompt_id, flush=True)
    next_report = started + 30
    while time.monotonic() - started < 3600:
        records = api("/history/" + prompt_id)
        if prompt_id in records:
            history = records[prompt_id]
            (out / "history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            if history.get("status", {}).get("status_str") != "success":
                raise RuntimeError("Local inference failed: " + str(out / "history.json"))
            item = history["outputs"]["16"]["images"][0]
            raw = COMFY / "output" / item.get("subfolder", "") / item["filename"]
            shutil.copy2(raw, out / "raw-model.png")
            with Image.open(out / "raw-model.png") as image:
                mode, size = image.mode, list(image.size)
            report = {"model": "Qwen-Image-2.1-Turbo INT8 convrot", "case": name,
                      "prompt_id": prompt_id, "started_utc": started_utc,
                      "elapsed_seconds": round(time.monotonic() - started, 2),
                      "new_model_inference": True, "endpoint": URL, "cloud_generation": False,
                      "steps": 8, "cfg": 1, "sampler": "euler", "seed": case.get("seed", 20261107),
                      "native_noise_mask": True, "initial_latent": "prepared RGBA guide encoded by the local VAE",
                      "reference_inputs": provenance, "mode": mode, "size": size,
                      "raw_output_sha256": digest(out / "raw-model.png"),
                      "postprocessing_applied_to_raw": False, "production_modified": False}
            (out / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({k: report[k] for k in ["case", "prompt_id", "elapsed_seconds", "mode", "size"]}), flush=True)
            return
        if time.monotonic() >= next_report:
            print(f"{name}: local inference pending {round(time.monotonic() - started)} s", flush=True)
            next_report += 30
        time.sleep(2)
    raise TimeoutError("Inspect the existing queue before resubmitting")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case")
    args = parser.parse_args()
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    for case in cases:
        if args.case is None or args.case == case["name"]:
            run(case)
