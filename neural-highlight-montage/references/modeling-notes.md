# Modeling Notes for Excitement Detection

## Recommended architecture options

- 3D CNN baseline: `torchvision.models.video.r3d_18`
- Stronger option: Video Swin / TimeSformer fine-tuned on domain highlights
- Lightweight fallback: 2D CNN frame embeddings + temporal Conv1D head

## Feature signals to combine

1. Visual action activation (neural model logits/features)
2. Motion magnitude (optical flow)
3. Shot boundary confidence
4. Audio energy and crowd-reaction bursts

## Practical training recipe

- Label clips as `highlight` / `non-highlight`
- Use 2-5 second clips and temporal jitter augmentation
- Handle class imbalance with weighted BCE or focal loss
- Track precision@k and recall@k for editorial usefulness

## Inference heuristics

- Smooth frame/window scores with moving average
- Detect peaks and expand with temporal handles
- Enforce diversity constraints to avoid repetitive scenes
