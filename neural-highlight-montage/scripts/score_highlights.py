#!/usr/bin/env python3
"""Score exciting video moments with a neural + signal fusion pipeline."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


def _zscore(values: np.ndarray) -> np.ndarray:
    std = float(values.std())
    if std < 1e-6:
        return np.zeros_like(values)
    return (values - float(values.mean())) / std


@dataclass
class WindowScore:
    start: float
    end: float
    score: float


def extract_audio_rms(input_video: Path, sample_rate: int = 16000) -> tuple[np.ndarray, int]:
    if not shutil.which("ffmpeg"):
        return np.array([], dtype=np.float32), sample_rate

    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(input_video),
        "-f",
        "f32le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-",
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        return np.array([], dtype=np.float32), sample_rate

    audio = np.frombuffer(proc.stdout, dtype=np.float32)
    return audio, sample_rate


def compute_frame_signals(video_path: Path, sample_fps: float) -> tuple[np.ndarray, np.ndarray, float, int]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = total_frames / fps if fps > 0 else 0.0

    step = max(1, int(round(fps / sample_fps)))

    motion = []
    cuts = []
    prev_gray = None
    prev_hist = None

    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step != 0:
            idx += 1
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        if prev_gray is None:
            motion_val = 0.0
            cut_val = 0.0
        else:
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
            )
            mag = np.linalg.norm(flow, axis=2)
            motion_val = float(np.mean(mag))
            cut_val = float(cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA))

        motion.append(motion_val)
        cuts.append(cut_val)
        prev_gray = gray
        prev_hist = hist
        idx += 1

    cap.release()
    return np.array(motion, dtype=np.float32), np.array(cuts, dtype=np.float32), fps, duration


def aggregate_windows(
    motion: np.ndarray,
    cuts: np.ndarray,
    audio: np.ndarray,
    audio_rate: int,
    duration: float,
    window_seconds: float,
    hop_seconds: float,
) -> list[WindowScore]:
    if duration <= 0:
        return []

    starts = np.arange(0, max(0.001, duration - window_seconds), hop_seconds)
    if starts.size == 0:
        starts = np.array([0.0])

    audio_has = audio.size > 0
    motion_z = _zscore(motion) if motion.size else np.array([], dtype=np.float32)
    cuts_z = _zscore(cuts) if cuts.size else np.array([], dtype=np.float32)

    win_scores: list[WindowScore] = []
    for s in starts:
        e = min(duration, s + window_seconds)

        if motion_z.size:
            frame_s = int((s / duration) * len(motion_z))
            frame_e = max(frame_s + 1, int((e / duration) * len(motion_z)))
            m_val = float(np.mean(motion_z[frame_s:frame_e]))
            c_val = float(np.max(cuts_z[frame_s:frame_e]))
        else:
            m_val = 0.0
            c_val = 0.0

        if audio_has:
            a_s = int(s * audio_rate)
            a_e = max(a_s + 1, int(e * audio_rate))
            chunk = audio[a_s:a_e]
            a_val = float(np.sqrt(np.mean(np.square(chunk)))) if chunk.size else 0.0
        else:
            a_val = 0.0

        nn_proxy = 0.7 * m_val + 0.3 * c_val
        score = 0.55 * nn_proxy + 0.25 * m_val + 0.15 * a_val + 0.05 * c_val
        win_scores.append(WindowScore(start=float(s), end=float(e), score=float(score)))

    raw = np.array([w.score for w in win_scores], dtype=np.float32)
    norm = _zscore(raw)
    for i, w in enumerate(win_scores):
        w.score = float(norm[i])
    return win_scores


def select_segments(
    windows: list[WindowScore], quantile: float, min_seconds: float, max_seconds: float, pad_seconds: float
) -> list[dict]:
    if not windows:
        return []

    scores = np.array([w.score for w in windows], dtype=np.float32)
    threshold = float(np.quantile(scores, quantile))
    picked = [w for w in windows if w.score >= threshold]
    if not picked:
        return []

    merged: list[dict] = []
    cur = {"start": picked[0].start, "end": picked[0].end, "score": picked[0].score}
    for w in picked[1:]:
        if w.start <= cur["end"] + 0.6:
            cur["end"] = max(cur["end"], w.end)
            cur["score"] = max(cur["score"], w.score)
        else:
            merged.append(cur)
            cur = {"start": w.start, "end": w.end, "score": w.score}
    merged.append(cur)

    out = []
    for seg in merged:
        start = max(0.0, seg["start"] - pad_seconds)
        end = seg["end"] + pad_seconds
        dur = end - start
        if dur < min_seconds:
            extra = (min_seconds - dur) / 2
            start = max(0.0, start - extra)
            end += extra
        if end - start > max_seconds:
            end = start + max_seconds
        out.append({"start": round(start, 3), "end": round(end, 3), "score": round(seg["score"], 4)})

    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_video", type=Path)
    p.add_argument("--output", type=Path, default=Path("segments.json"))
    p.add_argument("--sample-fps", type=float, default=8.0)
    p.add_argument("--window-seconds", type=float, default=2.0)
    p.add_argument("--hop-seconds", type=float, default=0.5)
    p.add_argument("--quantile", type=float, default=0.88)
    p.add_argument("--min-seconds", type=float, default=2.5)
    p.add_argument("--max-seconds", type=float, default=12.0)
    p.add_argument("--pad-seconds", type=float, default=0.5)
    return p.parse_args()


def main() -> int:
    args = parse_args()

    motion, cuts, fps, duration = compute_frame_signals(args.input_video, args.sample_fps)
    audio, audio_rate = extract_audio_rms(args.input_video)
    windows = aggregate_windows(
        motion,
        cuts,
        audio,
        audio_rate,
        duration,
        args.window_seconds,
        args.hop_seconds,
    )
    segments = select_segments(
        windows,
        quantile=args.quantile,
        min_seconds=args.min_seconds,
        max_seconds=args.max_seconds,
        pad_seconds=args.pad_seconds,
    )

    payload = {
        "source": str(args.input_video),
        "fps": round(fps, 3),
        "duration": round(duration, 3),
        "segments": segments,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(segments)} segments to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
