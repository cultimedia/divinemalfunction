#!/usr/bin/env python3
"""
Phase 1: ElevenLabs A/B Audio Generation
DivineMalfunction Shorts Pipeline

Reads voiceover lines from CSV and generates two audio variations
per line. Voice is specified per-row in the CSV. A/B variation is
achieved through different stability settings on the same voice.

CSV columns expected:
  File_Number, Section, Image_Name, VoiceOver_Line,
  MidJourney_Prompt, Cinematic_Variant, Voice

  Voice column values: "keith" | "spider" | blank (defaults to keith)

Output structure:
  audio/raw/
    001_A.mp3   ← stable take
    001_B.mp3   ← expressive take
    002_A.mp3
    ...

Usage:
  python phase1_audio_gen.py --csv scripts/voiceover.csv
  python phase1_audio_gen.py --csv scripts/voiceover.csv --rows 1-5
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv("config/.env")

# ── Voice Configuration ────────────────────────────────────────────────────────

VOICE_MAP = {
    "keith": os.getenv("VOICE_KEITH"),
    "spider": os.getenv("VOICE_SPIDER"),
}

DEFAULT_VOICE = "keith"

# A/B variation via stability — same voice ID, different delivery character
VOICE_SETTINGS_A = {
    "stability": 0.65,          # Controlled, consistent — cleaner narration
    "similarity_boost": 0.80,
    "style": 0.20,
    "use_speaker_boost": True,
}

VOICE_SETTINGS_B = {
    "stability": 0.35,          # Expressive, variable — more dynamic delivery
    "similarity_boost": 0.80,
    "style": 0.35,
    "use_speaker_boost": True,
}

# Voice-specific model selection — both voices are Professional Voice Clone (PVC),
# but they respond differently to model versions after testing
MODEL_MAP = {
    "keith": "eleven_multilingual_v2",   # V2 required - V3 produces nasally artifacts
    "spider": "eleven_v3",                # V3 confirmed better - more expressive, cleaner audio
}

OUTPUT_FORMAT = "mp3_44100_128"
OUTPUT_DIR = Path("audio/raw")
RATE_LIMIT_DELAY = 0.75         # seconds between API calls


# ── Core ───────────────────────────────────────────────────────────────────────

def get_client() -> ElevenLabs:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ERROR: ELEVENLABS_API_KEY not set in config/.env")
    print(f"API key loaded: {'*' * 8}{api_key[-4:]}")

    # Validate voice IDs are present
    for label, voice_id in VOICE_MAP.items():
        if not voice_id:
            sys.exit(f"ERROR: VOICE_{label.upper()} not set in config/.env")

    return ElevenLabs(api_key=api_key)


def load_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]

    required = {"File_number", "VoiceOver_Line"}
    missing = required - set(df.columns)
    if missing:
        sys.exit(f"ERROR: CSV missing required columns: {missing}\nFound: {list(df.columns)}")

    # Add Voice column with default if not present
    if "Voice" not in df.columns:
        print("Note: No 'Voice' column found — defaulting all lines to 'keith'")
        df["Voice"] = DEFAULT_VOICE

    df = df.dropna(subset=["VoiceOver_Line"])
    df["VoiceOver_Line"] = df["VoiceOver_Line"].astype(str).str.strip()
    df = df[df["VoiceOver_Line"] != ""]

    # Normalize voice labels
    df["Voice"] = df["Voice"].fillna(DEFAULT_VOICE).astype(str).str.strip().str.lower()
    df["Voice"] = df["Voice"].apply(lambda v: v if v in VOICE_MAP else DEFAULT_VOICE)

    return df


def generate_audio(
    client: ElevenLabs,
    text: str,
    voice_id: str,
    model_id: str,
    voice_settings: dict,
    output_path: Path,
) -> bool:
    """Generate one audio file. Returns True on success."""
    if output_path.exists():
        print(f"  ↷ Skipping {output_path.name} (already exists)")
        return True
    try:
        audio_bytes = client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id=model_id,
            output_format=OUTPUT_FORMAT,
            voice_settings=voice_settings,
        )
        with open(output_path, "wb") as f:
            for chunk in audio_bytes:
                f.write(chunk)
        print(f"  ✓ {output_path.name}")
        return True
    except Exception as e:
        print(f"  ✗ {output_path.name} — {e}")
        return False


def run(csv_path: str, row_range: Optional[Tuple[int, int]] = None):
    client = get_client()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_csv(csv_path)

    if row_range:
        start, end = row_range
        df = df.iloc[start - 1 : end]
        print(f"Processing rows {start}–{end} ({len(df)} lines)\n")
    else:
        print(f"Processing {len(df)} lines from {csv_path}\n")

    print(f"Models: Keith → {MODEL_MAP['keith']} | Spider → {MODEL_MAP['spider']}")
    print(f"Output: {OUTPUT_DIR.resolve()}\n")

    successes, failures, skipped = 0, 0, 0

    for _, row in df.iterrows():
        # Extract numeric part from file number (handles "st1" → "1" → "001")
        raw_file_num = str(row["File_number"])
        numeric_part = ''.join(filter(str.isdigit, raw_file_num))
        if not numeric_part:
            print(f"⚠ Skipping row with invalid File_number: {raw_file_num}")
            continue
        file_num = numeric_part.zfill(3)

        text = row["VoiceOver_Line"]
        voice_label = row["Voice"]
        voice_id = VOICE_MAP[voice_label]
        model_id = MODEL_MAP[voice_label]
        section = row.get("Section", "")

        preview = text[:70] + "..." if len(text) > 70 else text
        print(f"[{file_num}] {section} | voice: {voice_label} | model: {model_id}")
        print(f"  \"{preview}\"")

        for take_label, settings in [("A", VOICE_SETTINGS_A), ("B", VOICE_SETTINGS_B)]:
            path = OUTPUT_DIR / f"{file_num}_{take_label}.mp3"
            was_existing = path.exists()
            ok = generate_audio(client, text, voice_id, model_id, settings, path)
            if ok and was_existing:
                skipped += 1
            elif ok:
                successes += 1
            else:
                failures += 1
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n── Phase 1 complete ──")
    print(f"   Generated : {successes}")
    print(f"   Skipped   : {skipped}  (already existed)")
    print(f"   Failed    : {failures}")
    print(f"   Output    : {OUTPUT_DIR.resolve()}")

    if failures:
        sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────────────

def parse_range(s: str) -> Tuple[int, int]:
    try:
        start, end = s.split("-")
        return int(start.strip()), int(end.strip())
    except Exception:
        raise argparse.ArgumentTypeError("Range must be START-END, e.g. 1-5")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Phase 1: Generate A/B audio variations from voiceover CSV"
    )
    parser.add_argument("--csv", required=True, help="Path to voiceover CSV")
    parser.add_argument("--rows", type=parse_range, help="Row subset, e.g. --rows 1-3")
    args = parser.parse_args()
    run(args.csv, args.rows)
