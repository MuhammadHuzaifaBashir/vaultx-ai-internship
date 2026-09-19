"""
SightAssist backend — FastAPI service that takes a photo + a mode,
sends it to Gemini's vision model with a mode-specific prompt, and
returns a short spoken-style description.

Modes:
  - scene   : general environment description
  - object  : close-up handheld object identification
  - text    : reads visible text verbatim (labels, signs, dates, prices)
  - hazard  : safety-only description (obstacles, moving things, drop-offs)

Reliability features:
  - Retry with exponential backoff on transient API failures (rate limits, timeouts)
  - Client-side-adjacent image compression before sending to the model (faster
    upload, smaller payload, lower latency)
  - Every request/response is logged to logs/requests.jsonl (timestamp, mode,
    description, latency, success/failure) — this log doubles as real
    evaluation data, no manual tracking needed

Run with:
    uvicorn app_api:app --reload --port 8000 --host 0.0.0.0
"""

import os
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from PIL import Image
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI(title="SightAssist API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1  # seconds; doubles each retry (1s, 2s, 4s) — trimmed down for speed
MAX_IMAGE_DIMENSION = 768  # px, longest side — smaller payload = faster upload + faster model response
JPEG_QUALITY = 72

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "requests.jsonl"

# Store the last successful description per session-less client, keyed simply
# since this is a single-user local app. Good enough for a "repeat" feature
# without needing real session management.
_last_description = {"mode": None, "text": None}

PROMPTS = {
    "scene": (
        "Describe this scene in 1-2 short sentences for a blind person, as if speaking "
        "naturally and directly to them right now. Mention only what's genuinely useful "
        "to know about their immediate surroundings. Avoid listing minor details. "
        "If there are many similar items (like icons on a screen, products on a shelf, "
        "or objects in a group), summarize them naturally instead of listing every single "
        "one — e.g. 'a phone home screen with several apps' rather than naming all of them. "
        "If a person is visible, include their visible facial expression, body language, "
        "or reaction if it's clear and relevant (e.g. 'a person smiling and waving at you', "
        "'someone looking down at their phone', 'a person appears upset'). Describe what "
        "you can see, don't guess or assume things you can't actually observe. Do not "
        "attempt to identify who a specific person is — only describe what they look like "
        "doing right now. Keep it under 40 words."
    ),
    "object": (
        "The person is holding an object close to the camera and wants to know exactly "
        "what it is. Identify the object specifically (not just its general category) — "
        "for example say 'a red apple with a small bruise on one side' rather than just "
        "'a fruit', or 'a Phillips-head screwdriver' rather than just 'a tool'. "
        "Mention distinguishing details: color, size, condition (new/damaged/full/empty), "
        "and brand if visible. If you genuinely cannot identify the object with confidence, "
        "say so honestly rather than guessing. Keep it under 35 words."
    ),
    "text": (
        "Find and read aloud any visible text in this image (labels, signs, dates, "
        "prices, packaging, screens). Read it exactly as written, word for word, "
        "nothing added or paraphrased. If there is no readable text in the image, "
        "say exactly: 'No text found.' Do not describe anything else in the image."
    ),
    "hazard": (
        "You are a safety spotter for a blind person walking or moving through this "
        "space. Only mention: moving vehicles, obstacles directly in their path, "
        "stairs, curbs, drop-offs, or anything that could cause a collision or a fall. "
        "State direction (left / right / straight ahead) and approximate distance if "
        "you can tell. If nothing hazardous is present, say exactly: "
        "'No immediate hazards detected.' Keep it under 25 words."
    ),
    "navigate": (
        "You are giving a blind person a quick, real-time walking update as they move "
        "forward. In ONE short sentence, under 15 words, state ONLY: the clearest safe "
        "direction to continue (straight / slightly left / slightly right / stop), and "
        "any single most important obstacle or hazard within their next few steps if one "
        "exists. Do not describe the general scene, colors, or anything not directly "
        "relevant to walking safely right now. If the path ahead is clear, say exactly: "
        "'Path clear, continue straight.' Be fast and precise, not descriptive."
    ),
}


def compress_image(image_bytes: bytes) -> bytes:
    """Resize and re-encode the image to keep upload/API payload small and fast."""
    img = Image.open(io.BytesIO(image_bytes))
    img = img.convert("RGB")  # drop alpha channel if present, JPEG doesn't support it

    img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION))  # keeps aspect ratio

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=JPEG_QUALITY)
    return out.getvalue()


def describe_image_with_retry(image_bytes: bytes, mode: str) -> tuple[str, int]:
    """Calls Gemini with retry + exponential backoff. Returns (description, attempts_used)."""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    PROMPTS[mode],
                ],
            )
            return response.text.strip(), attempt

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES:
                wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                time.sleep(wait)

    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {last_error}")


def log_request(mode: str, description: str, latency_ms: int, success: bool, error: str = None):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "description": description,
        "latency_ms": latency_ms,
        "success": success,
        "error": error,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@app.post("/describe")
async def describe(
    image: UploadFile = File(...),
    mode: str = Form(...),
):
    if mode not in PROMPTS:
        raise HTTPException(status_code=400, detail=f"Invalid mode '{mode}'. Must be one of: {list(PROMPTS.keys())}")

    start = time.time()
    raw_bytes = await image.read()

    try:
        compressed = compress_image(raw_bytes)
        description, attempts = describe_image_with_retry(compressed, mode)
        latency_ms = int((time.time() - start) * 1000)

        _last_description["mode"] = mode
        _last_description["text"] = description

        log_request(mode, description, latency_ms, success=True)

        return {
            "mode": mode,
            "description": description,
            "latency_ms": latency_ms,
            "attempts": attempts,
        }

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        log_request(mode, None, latency_ms, success=False, error=str(e))
        # Never fail silently — the frontend needs something to speak aloud even on error
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribes a short voice command recording to text using Gemini's audio
    understanding. This is a per-press, on-demand call (not continuous), so
    it costs one API request per command — same cost as tapping a button.

    This exists because the browser's built-in speech recognition (Web Speech
    API) is unsupported on iOS Safari and unreliable across browsers in
    general. Recording audio and transcribing it server-side works
    identically on any phone.
    """
    audio_bytes = await audio.read()

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm"),
                "Transcribe exactly what is said in this short audio clip. "
                "Return ONLY the transcribed words, nothing else — no punctuation "
                "commentary, no quotation marks, just the plain transcribed text.",
            ],
        )
        transcript = response.text.strip()
        return {"transcript": transcript}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transcribe audio: {str(e)}")


@app.post("/describe-detailed")
async def describe_detailed(
    image: UploadFile = File(...),
    mode: str = Form("scene"),
):
    """
    Re-analyzes the same photo with a much more thorough description —
    triggered by the voice command "more detail" (or a future button),
    without requiring a new photo to be captured.
    """
    start = time.time()
    raw_bytes = await image.read()

    detailed_prompt = (
        "Give a thorough, detailed description of this entire image for a "
        "blind person who wants to understand it fully, not just a quick "
        "summary. Describe: what's in the scene, any people and their "
        "visible expressions or actions, objects and their positions "
        "relative to each other (left/right/center/background), any "
        "visible text, and colors where relevant. Be specific and "
        "thorough, but stay factual — describe what's actually visible, "
        "don't guess at things you can't see. Aim for 3-5 sentences, "
        "spoken naturally as if explaining it to someone right now."
    )

    try:
        compressed = compress_image(raw_bytes)

        last_error = None
        description = None
        attempts = 0
        for attempt in range(1, MAX_RETRIES + 1):
            attempts = attempt
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=[
                        types.Part.from_bytes(data=compressed, mime_type="image/jpeg"),
                        detailed_prompt,
                    ],
                )
                description = response.text.strip()
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))

        if description is None:
            raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {last_error}")

        latency_ms = int((time.time() - start) * 1000)
        log_request(f"{mode}_detailed", description, latency_ms, success=True)

        return {"description": description, "latency_ms": latency_ms, "attempts": attempts}

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        log_request(f"{mode}_detailed", None, latency_ms, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze image in detail: {str(e)}")


@app.post("/describe-region")
async def describe_region(
    image: UploadFile = File(...),
):
    """
    Analyzes a cropped region of a previously captured photo, when the user
    taps a specific spot for more detail. Always uses a detailed, zoomed-in
    style prompt regardless of the original mode.
    """
    start = time.time()
    raw_bytes = await image.read()

    region_prompt = (
        "This is a cropped close-up region from a photo the user tapped on to "
        "get more detail. Describe specifically what is in this cropped area "
        "in 1-2 sentences, with as much relevant detail as you can genuinely "
        "see (what it is, color, text if any, condition). If the crop is too "
        "blurry, too small, or ambiguous to identify confidently, say so "
        "honestly rather than guessing. Keep it under 40 words."
    )

    try:
        compressed = compress_image(raw_bytes)

        last_error = None
        description = None
        attempts = 0
        for attempt in range(1, MAX_RETRIES + 1):
            attempts = attempt
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=[
                        types.Part.from_bytes(data=compressed, mime_type="image/jpeg"),
                        region_prompt,
                    ],
                )
                description = response.text.strip()
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BASE_DELAY * (2 ** (attempt - 1)))

        if description is None:
            raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: {last_error}")

        latency_ms = int((time.time() - start) * 1000)
        log_request("region_detail", description, latency_ms, success=True)

        return {"description": description, "latency_ms": latency_ms, "attempts": attempts}

    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        log_request("region_detail", None, latency_ms, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to analyze region: {str(e)}")


@app.get("/repeat")
async def repeat_last():
    """Returns the last successful description without calling the model again —
    saves an API call when the user just wants to hear it again."""
    if _last_description["text"] is None:
        raise HTTPException(status_code=404, detail="No description yet. Capture something first.")
    return {"mode": _last_description["mode"], "description": _last_description["text"]}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/stats")
async def stats():
    """Quick summary of logged requests — useful for the evaluation writeup."""
    if not LOG_FILE.exists():
        return {"total_requests": 0}

    entries = [json.loads(line) for line in open(LOG_FILE, encoding="utf-8") if line.strip()]
    successes = [e for e in entries if e["success"]]
    failures = [e for e in entries if not e["success"]]
    avg_latency = sum(e["latency_ms"] for e in successes) / len(successes) if successes else 0

    by_mode = {}
    for e in entries:
        by_mode.setdefault(e["mode"], {"total": 0, "success": 0})
        by_mode[e["mode"]]["total"] += 1
        if e["success"]:
            by_mode[e["mode"]]["success"] += 1

    return {
        "total_requests": len(entries),
        "successes": len(successes),
        "failures": len(failures),
        "avg_latency_ms": round(avg_latency),
        "by_mode": by_mode,
    }


# Serve the frontend (index.html + any assets) directly from this same server,
# so the phone only needs to hit one URL.
app.mount("/", StaticFiles(directory="static", html=True), name="static")