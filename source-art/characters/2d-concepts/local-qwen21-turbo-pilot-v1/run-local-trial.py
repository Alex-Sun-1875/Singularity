"""Run the official native Qwen 2.1 Turbo sampling chain on localhost only.

This adapter saves untouched model output. It does not retouch it or install it
into the game. All image IO and inference stay on this computer.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import time
import urllib.request
from datetime import datetime, timezone
from PIL import Image

ROOT = Path(__file__).resolve().parent
COMFY = Path(r"F:\Models\ComfyUI_windows_portable\ComfyUI")
ENDPOINT = "http://127.0.0.1:8188"
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
SIGMAS = "1.0, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0"


def request(path, body=None):
    req = urllib.request.Request(
        ENDPOINT + path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with HTTP.open(req, timeout=30) as response:
        return json.load(response)


def sha256(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def node(kind, **inputs):
    return {"class_type": kind, "inputs": inputs}


def run(case_name, seed):
    manifest = json.loads((ROOT / "input-manifest.json").read_text(encoding="utf-8"))
    base_name = "front-run" if case_name == "front-proportions" else case_name
    case = next(item for item in manifest["groups"] if item["name"] == base_name)
    target_dir = COMFY / "input" / "qwen21-trial" / base_name
    target_dir.mkdir(parents=True, exist_ok=True)
    output = ROOT / "results" / case_name
    output.mkdir(parents=True, exist_ok=True)
    if (output / "result.json").exists():
        raise RuntimeError("A result already exists; choose a new version instead of overwriting it")

    graph = {
        "1": node("UNETLoader", unet_name="qwen_image_2.1_turbo_int8_convrot.safetensors", weight_dtype="default"),
        "2": node("CLIPLoader", clip_name="qwen3vl_8b_int8_convrot.safetensors", type="qwen_image", device="cpu"),
        "3": node("VAELoader", vae_name="qwen_image_2.1_vae_bf16.safetensors"),
        "8": node("TextEncodeQwenImage21", clip=["2", 0], vae=["3", 0], prompt="", negative_prompt="", resolution=0),
        "9": node("QwenImage21Cache", model=["1", 0], device="cpu", dtype="default"),
        "10": node("CFGGuider", model=["9", 0], positive=["8", 0], negative=["8", 1], cfg=1),
        "11": node("RandomNoise", noise_seed=seed),
        "12": node("KSamplerSelect", sampler_name="euler"),
        "13": node("ManualSigmas", sigmas=SIGMAS),
        "14": node("SamplerCustomAdvanced", noise=["11", 0], guider=["10", 0], sampler=["12", 0], sigmas=["13", 0], latent_image=["8", 2]),
        "15": node("VAEDecode", samples=["14", 0], vae=["3", 0]),
        "16": node("SaveImage", images=["15", 0], filename_prefix="qwen21-trial/" + case_name),
    }
    source_hashes = {}
    used_inputs = []
    for index, entry in enumerate(case["images"]):
        image_record = entry["preserved_rgba"]
        image_path = Path(image_record["path"])
        if sha256(image_path) != image_record["sha256"]:
            raise RuntimeError("Input hash mismatch: " + str(image_path))
        with Image.open(image_path) as image:
            if image.mode != "RGBA" or image.size != (512, 768):
                raise RuntimeError("Expected preserved 512x768 RGBA input")
        shutil.copy2(image_path, target_dir / image_path.name)
        load_id, join_id = str(4 + index), str(6 + index)
        graph[load_id] = node("LoadImage", image=f"qwen21-trial/{base_name}/{image_path.name}")
        graph[join_id] = node("JoinImageWithAlpha", image=[load_id, 0], alpha=[load_id, 1])
        graph["8"]["inputs"][f"images.image_{index + 1}"] = [join_id, 0]
        original = entry["source_original"]
        if sha256(original["path"]) != original["sha256"]:
            raise RuntimeError("Original source changed before the trial")
        source_hashes[original["path"]] = original["sha256"]
        used_inputs.append({"role": entry["role"], **image_record})

    prompt_path = case["separate_geometry_prompt"] if case_name == "front-proportions" else case["first_prompt"]
    prompt = Path(prompt_path).read_text(encoding="utf-8").strip()
    prompt = prompt.replace("图1", "<image1>").replace("图2", "<image2>")
    graph["8"]["inputs"]["prompt"] = prompt
    (output / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    (output / "workflow-api.json").write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    stats = request("/system_stats")
    (output / "runtime-before.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    started_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    submission = request("/prompt", {"prompt": graph, "client_id": "qwen21-local-evaluation"})
    (output / "submission.json").write_text(json.dumps(submission, indent=2), encoding="utf-8")
    if submission.get("node_errors") or not submission.get("prompt_id"):
        raise RuntimeError("Graph rejected: " + str(submission))
    prompt_id = submission["prompt_id"]
    print(f"Queued actual local model job {case_name}: {prompt_id}", flush=True)
    next_report = started + 30
    while time.monotonic() - started < 3600:
        records = request("/history/" + prompt_id)
        if prompt_id in records:
            history = records[prompt_id]
            (output / "history.json").write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
            if history.get("status", {}).get("status_str") != "success":
                raise RuntimeError("Local inference failed; inspect " + str(output / "history.json"))
            images = history.get("outputs", {}).get("16", {}).get("images", [])
            if len(images) != 1:
                raise RuntimeError("Expected exactly one saved model image")
            item = images[0]
            model_path = COMFY / "output" / item.get("subfolder", "") / item["filename"]
            raw_output = output / "raw-model.png"
            shutil.copy2(model_path, raw_output)
            with Image.open(raw_output) as image:
                alpha_range = list(image.getchannel("A").getextrema()) if "A" in image.getbands() else None
                image_metadata = {"mode": image.mode, "size": list(image.size), "alpha_extrema": alpha_range}
            unchanged = all(sha256(path) == expected for path, expected in source_hashes.items())
            report = {
                "model": "Qwen-Image-2.1-Turbo INT8 convrot",
                "case": case_name, "prompt_id": prompt_id, "seed": seed,
                "started_utc": started_utc,
                "elapsed_seconds": round(time.monotonic() - started, 2),
                "new_model_inference": True, "local_endpoint": ENDPOINT,
                "cloud_inference": False, "proxy_used_for_inference": False,
                "postprocessing_applied": False, "steps": 8, "sampler": "euler", "cfg": 1,
                "text_encoder_device": "cpu", "kv_cache_device": "cpu", "kv_cache_dtype": "default",
                "inputs": used_inputs, "output": str(raw_output), "sha256": sha256(raw_output),
                **image_metadata, "source_originals_unchanged": unchanged,
                "production_modified": False, "visual_status": "awaiting review; execution success is not artwork acceptance",
                "comfyui_version": stats["system"]["comfyui_version"],
            }
            (output / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({key: report[key] for key in ["case", "prompt_id", "elapsed_seconds", "mode", "size", "alpha_extrema", "source_originals_unchanged", "output"]}, ensure_ascii=False), flush=True)
            return
        if time.monotonic() >= next_report:
            print(f"Local inference pending: {case_name}, {round(time.monotonic() - started)} s", flush=True)
            next_report += 30
        time.sleep(2)
    raise TimeoutError("Job still pending. Inspect the queue before resubmitting.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=["front-run", "back-sword", "front-proportions"], required=True)
    parser.add_argument("--seed", type=int, default=20261107)
    args = parser.parse_args()
    run(args.case, args.seed)
