import os, tempfile
import numpy as np
import soundfile as sf
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter(prefix="/api/speech", tags=["speech"])

def rms_flags(y: np.ndarray, sr: int, frame_ms: int = 30, thresh_scale: float = 0.6):
    """Energy-threshold method: determine per frame whether it is 'speech' (True) or 'silence' (False)."""
    frame_len = max(1, int(sr * frame_ms / 1000))
    n_frames = len(y) // frame_len
    if n_frames == 0:
        return []
    y = y[: n_frames * frame_len]
    frames = y.reshape(n_frames, frame_len)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    thr = max(1e-12, float(np.median(rms) * thresh_scale))
    return (rms > thr).astype(bool).tolist()

@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    # 1) Save temporary file
    suffix = os.path.splitext(file.filename or "")[1] or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        path = tmp.name

    try:
        # 2) Read audio (keep original sample rate)
        y, sr = sf.read(path, dtype="float32", always_2d=False)
        if y is None or len(y) == 0:
            raise HTTPException(400, "Empty audio")
        if y.ndim > 1:
            y = y[:, 0]  # take mono channel

        # 3) Compute speech/silence frames
        flags = rms_flags(y, sr, frame_ms=30, thresh_scale=0.6)
        total_ms = len(flags) * 30

        # Collect silence segments
        pauses = []
        if flags:
            run = 1
            for i in range(1, len(flags)):
                if flags[i] == flags[i - 1]:
                    run += 1
                else:
                    if not flags[i - 1]:           # just finished a silence block
                        pauses.append(run * 30)    # ms
                    run = 1
            if not flags[-1]:
                pauses.append(run * 30)

        mean_pause = float(np.mean(pauses)) if pauses else 0.0
        long_pause_pct = int(100 * sum(p > 700 for p in pauses) / max(1, len(pauses)))
        pause_density = 60000.0 * len(pauses) / max(1, total_ms) if total_ms else 0.0

        return {
            "duration_s": round(total_ms / 1000.0, 1),
            "pause_density_per_min": round(pause_density, 1),
            "mean_pause_ms": int(mean_pause),
            "long_pause_pct": long_pause_pct,
            "fluency_hint": "Aim for shorter and more even pauses; practice with 1–2 short sentences and gradually extend.",
            "disclaimer": "For educational purposes only, not for medical diagnosis.",
        }
    finally:
        try:
            os.remove(path)
        except:
            pass
