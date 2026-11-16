"""Assemble and measure the audio direction studies, without changing game assets.

Inputs are original offline renders listed in study-inputs.json. NumPy/SciPy and
the installed FFmpeg are authoring tools only; no runtime dependency is added.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

REPO = Path(__file__).resolve().parents[4]
STUDY = REPO / "source-art/audio/direction-studies-v2"
RATE = 44100


def run(argv):
    result = subprocess.run([str(item) for item in argv], capture_output=True,
                            encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result


def read_wav(path):
    rate, pcm = wavfile.read(path)
    if np.issubdtype(pcm.dtype, np.integer):
        divisor = float(2 ** (np.iinfo(pcm.dtype).bits - 1))
        signal = pcm.astype(np.float32) / divisor
    else:
        signal = pcm.astype(np.float32)
    if signal.ndim == 1:
        signal = np.repeat(signal[:, None], 2, axis=1)
    if signal.shape[1] != 2 or not np.isfinite(signal).all():
        raise ValueError(f"Invalid stereo audio: {path}")
    if rate != RATE:
        factor = math.gcd(rate, RATE)
        signal = resample_poly(signal, RATE // factor, rate // factor).astype(np.float32)
    return signal


def write_wav(path, signal):
    peak = float(np.max(np.abs(signal)))
    if peak >= 1 or not np.isfinite(signal).all():
        raise ValueError(f"Refusing clipped or non-finite master: {path}, peak={peak}")
    wavfile.write(path, RATE, np.round(signal * 32767).astype(np.int16))


def loudness(ffmpeg, path, target=-20):
    result = run([ffmpeg, "-hide_banner", "-nostdin", "-i", path, "-af",
                  f"loudnorm=I={target}:TP=-2:LRA=9:print_format=json", "-f", "null", "-"])
    start = result.stderr.rfind("{")
    return json.JSONDecoder().raw_decode(result.stderr[start:])[0]


def matched(ffmpeg, source, target, scratch):
    """Use measured two-pass gain for fair comparisons; retain exact PCM duration."""
    values = loudness(ffmpeg, source, target)
    normalizer = (f"loudnorm=I={target}:TP=-2:LRA=9:linear=true"
                  f":measured_I={values['input_i']}:measured_TP={values['input_tp']}"
                  f":measured_LRA={values['input_lra']}:measured_thresh={values['input_thresh']}"
                  f":offset={values['target_offset']}")
    run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-i", source, "-af", normalizer,
         "-ar", RATE, "-ac", 2, "-c:a", "pcm_s24le", scratch])
    result = read_wav(scratch)
    source_frames = len(read_wav(source))
    if len(result) != source_frames:
        raise ValueError(f"Loudness matching changed duration: {source}")
    return result


def concatenate(parts, gap=2):
    silence = np.zeros((round(gap * RATE), 2), np.float32)
    sequence = []
    markers = []
    cursor = 0
    for index, (item, signal) in enumerate(parts):
        if index:
            sequence.append(silence)
            cursor += len(silence)
        markers.append(dict(id=item["id"], title=item["title"],
                            start=round(cursor / RATE, 4),
                            end=round((cursor + len(signal)) / RATE, 4),
                            source=item["path"]))
        sequence.append(signal)
        cursor += len(signal)
    return np.concatenate(sequence), markers


def db(value):
    return round(20 * math.log10(max(value, 1e-12)), 4)


def inspect(signal):
    mono = signal.mean(axis=1)
    stereo_rms = float(np.sqrt(np.mean(signal.astype(np.float64) ** 2)))
    mono_rms = float(np.sqrt(np.mean(mono.astype(np.float64) ** 2)))
    return dict(durationSeconds=round(len(signal) / RATE, 6), sampleRate=RATE,
                channels=2, samplePeakDbfs=db(float(np.max(np.abs(signal)))),
                clippingSamples=int(np.count_nonzero(np.abs(signal) >= 1)),
                monoFoldDownRmsDeltaDb=db(mono_rms / max(stereo_rms, 1e-12)),
                maxAdjacentSampleStep=float(np.max(np.abs(np.diff(signal, axis=0)))),
                openingSamplePeak=float(np.max(np.abs(signal[0]))),
                closingSamplePeak=float(np.max(np.abs(signal[-1]))))


def emit(ffmpeg, folder, name, title, signal, scratch):
    wav = folder / (name + ".wav")
    mp3 = folder / (name + ".mp3")
    write_wav(wav, signal)
    encoded = scratch / (name + "-encoded.mp3")
    encoders = run([ffmpeg, "-hide_banner", "-encoders"]).stdout
    codec = "libmp3lame" if "libmp3lame" in encoders else "mp3_mf"
    run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-i", wav, "-c:a", codec,
         "-b:a", "192k", "-ar", RATE, "-metadata", "title=" + title, encoded])
    # mp3_mf groups multiple frames per packet; reparsing fixes the Xing duration.
    run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-i", encoded,
         "-c:a", "copy", mp3])
    decoded_path = scratch / (name + "-decoded.wav")
    run([ffmpeg, "-hide_banner", "-nostdin", "-y", "-i", mp3, decoded_path])
    master_report = inspect(read_wav(wav))
    decoded_report = inspect(read_wav(decoded_path))
    measured = loudness(ffmpeg, mp3)
    decoded_report.update(integratedLufs=float(measured["input_i"]),
                          truePeakDbtp=float(measured["input_tp"]),
                          durationDeltaFromMasterSeconds=round(
                              decoded_report["durationSeconds"] - master_report["durationSeconds"], 6))
    if abs(decoded_report["durationSeconds"] - master_report["durationSeconds"]) > .15:
        raise ValueError(f"MP3 duration mismatch: {name}")
    if decoded_report["clippingSamples"] or decoded_report["truePeakDbtp"] > -1:
        raise ValueError(f"Unsafe encoded preview peak: {name}")
    if decoded_report["monoFoldDownRmsDeltaDb"] < -4:
        raise ValueError(f"Excessive mono cancellation: {name}")
    return dict(id=name, title=title, wav=str(wav.relative_to(STUDY)).replace("\\", "/"),
                mp3=str(mp3.relative_to(STUDY)).replace("\\", "/"),
                master=master_report, preview=decoded_report,
                wavSha256=hashlib.sha256(wav.read_bytes()).hexdigest(),
                mp3Sha256=hashlib.sha256(mp3.read_bytes()).hexdigest(),
                mp3Bytes=mp3.stat().st_size, encoder=codec)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--inputs", type=Path, default=STUDY / "study-inputs.json")
    args = parser.parse_args()
    config = json.loads(args.inputs.read_text(encoding="utf-8-sig"))
    destination = STUDY / "audition"
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    source_reports = []
    with tempfile.TemporaryDirectory(prefix="sword-fire-audio-studies-") as temporary:
        scratch = Path(temporary)
        for group, duration, target, name, title in [
            ("music", 30, -20, "music-abc", "剑与火 · 三种音乐方向"),
            ("sfx", 15, -20, "four-classes", "剑与火 · 四职业声音对照"),
        ]:
            parts = []
            for index, item in enumerate(config[group]):
                source = STUDY / item["path"]
                signal = matched(args.ffmpeg, source, target, scratch / f"{group}-{index}.wav")
                if len(signal) != duration * RATE:
                    raise ValueError(f"Unexpected {group} study duration: {source}")
                measure = loudness(args.ffmpeg, scratch / f"{group}-{index}.wav")
                source_reports.append(dict(id=item["id"], source=item["path"],
                                           matchedIntegratedLufs=float(measure["input_i"]),
                                           matchedTruePeakDbtp=float(measure["input_tp"])))
                parts.append((item, signal))
            signal, markers = concatenate(parts)
            result = emit(args.ffmpeg, destination, name, title, signal, scratch)
            result["markers"] = markers
            results.append(result)

        journey = config["journey"]
        music = matched(args.ffmpeg, STUDY / journey["path"], -23, scratch / "journey.wav")
        battle = read_wav(STUDY / journey["battleLayer"])
        if len(music) != 45 * RATE or len(battle) != 15 * RATE:
            raise ValueError("Journey and battle layer must be 45 and 15 seconds")
        battle_gain = float(journey.get("battleGain", .6))
        music[15 * RATE:30 * RATE] += battle * battle_gain
        gain = min(1., .77 / max(float(np.max(np.abs(music))), 1e-9))
        result = emit(args.ffmpeg, destination, "journey-mixed",
                      "剑与火 · 探索、交战与战后", music * gain, scratch)
        result.update(markers=journey["markers"], battleLayerGain=battle_gain,
                      finalCommonGain=gain,
                      gameplayCapture=False,
                      description="离线排布的音乐与职业音效混音示范，非运行时录屏或已接入证明。")
        results.append(result)

    report = dict(schemaVersion=1, date="2026-11-16", scope="offline-audition-studies",
                  production="Original score and deterministic acoustic-inspired synthesis; no AI model inference or third-party samples.",
                  gameAssetsChanged=False, listeningAcceptance="pending-user-audition",
                  taptapDeviceAcceptance="not-performed", matchedSources=source_reports,
                  outputs=results)
    (STUDY / "audio-validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(outputs=[dict(id=item["id"], wav=item["wav"], mp3=item["mp3"],
                                      seconds=item["master"]["durationSeconds"],
                                      lufs=item["preview"]["integratedLufs"],
                                      truePeakDbtp=item["preview"]["truePeakDbtp"])
                                  for item in results]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
