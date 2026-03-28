#!/usr/bin/env python3
"""Render highlight montage from scored segments JSON using ffmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input_video", type=Path)
    p.add_argument("segments_json", type=Path)
    p.add_argument("--output", type=Path, default=Path("highlight_mix.mp4"))
    p.add_argument("--max-clips", type=int, default=12)
    p.add_argument("--target-seconds", type=float, default=90.0)
    p.add_argument("--video-codec", default="libx264")
    p.add_argument("--audio-codec", default="aac")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required in PATH")

    data = json.loads(args.segments_json.read_text(encoding="utf-8"))
    segments = data.get("segments", [])
    if not segments:
        raise RuntimeError("No segments found in JSON")

    clips = []
    total = 0.0
    for seg in segments:
        start = float(seg["start"])
        end = float(seg["end"])
        dur = max(0.0, end - start)
        if dur <= 0.1:
            continue
        clips.append((start, dur))
        total += dur
        if len(clips) >= args.max_clips or total >= args.target_seconds:
            break

    if not clips:
        raise RuntimeError("No valid clips selected")

    with tempfile.TemporaryDirectory(prefix="hl_montage_") as td:
        td_path = Path(td)
        concat_file = td_path / "concat.txt"
        lines = []
        for i, (start, dur) in enumerate(clips):
            out_clip = td_path / f"clip_{i:03d}.mp4"
            run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-ss",
                    f"{start:.3f}",
                    "-i",
                    str(args.input_video),
                    "-t",
                    f"{dur:.3f}",
                    "-c:v",
                    args.video_codec,
                    "-preset",
                    "veryfast",
                    "-c:a",
                    args.audio_codec,
                    str(out_clip),
                ]
            )
            lines.append(f"file '{out_clip.as_posix()}'")

        concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_file),
                "-c",
                "copy",
                str(args.output),
            ]
        )

    print(f"Montage generated: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
