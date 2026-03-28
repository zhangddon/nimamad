---
name: neural-highlight-montage
description: Detect exciting moments in video with neural-network-based scoring and automatically produce highlight montage edits. Use when users ask to identify highlight clips, generate exciting cutdowns, or automate sports/game/event recap editing from raw footage.
---

# Neural Highlight Montage

Build automatic highlight edits from source videos by combining neural scoring, segment ranking, and timeline rendering.

## Workflow

1. Normalize source files to a stable edit codec and frame rate.
2. Score short windows with a neural model and auxiliary signals.
3. Merge neighboring high-score windows into candidate highlight segments.
4. Select top segments under a target duration budget.
5. Render a montage with transitions, speed ramps (optional), and loudness normalization.

## Use the bundled scripts

- Run `scripts/score_highlights.py` to infer excitement scores and export ranked segments JSON.
- Run `scripts/build_montage.py` to cut and concatenate selected segments into the final highlight video.
- Run `scripts/score_highlights.py --help` and `scripts/build_montage.py --help` before first use to verify dependencies.

## Dependency checklist

Install required tools before running:

- Python 3.10+
- `torch`, `torchvision`, `opencv-python`, `numpy`
- FFmpeg executable in `PATH`

## Segment selection policy

Use these defaults unless the user specifies otherwise:

- Window size: 2.0s
- Hop size: 0.5s
- Highlight threshold: top 12% windows by score
- Minimum segment duration: 2.5s
- Maximum segment duration: 12s
- Target montage length: 45-120s

## Scoring strategy

Compute a composite excitement score per window:

- Neural action prior (3D CNN feature activation)
- Motion intensity (dense optical flow magnitude)
- Audio energy (RMS from audio track, if available)
- Shot-change boost (histogram delta peaks)

Fuse with weighted sum and z-score normalization before ranking.

## Quality controls

- Deduplicate near-identical segments by temporal overlap IoU.
- Keep temporal diversity by limiting picks per source minute.
- Preserve context by adding 0.3-0.8s handles around each selected peak.

## Output contract

The scorer must write JSON shaped like:

```json
{
  "source": "input.mp4",
  "fps": 30,
  "segments": [
    {"start": 12.3, "end": 18.1, "score": 2.41},
    {"start": 44.0, "end": 49.2, "score": 2.08}
  ]
}
```

The montage builder consumes this JSON and renders `highlight_mix.mp4` unless overridden.

## Troubleshooting

- If inference is slow, reduce `--sample-fps` or use `--device cpu` explicitly.
- If too many false positives appear, raise `--quantile` (for example `0.92` to `0.96`).
- If cuts feel abrupt, increase `--pad-seconds` and transition duration in the render step.
