# DivineMalfunction Automations
## Claude Code Project Context

**Repository:** `github.com/cultimedia/divinemalfunction`  
**Working directory:** `divinemalfunction_automations/`  
**Owner:** Keith Wilkins — HolyHell.io / DivineMalfunction.com  
**Purpose:** YouTube Shorts production pipeline for the DivineMalfunction channel

---

## Project Overview

This is a 6-phase automation pipeline for producing YouTube Shorts from scripted voiceover CSV files. Each phase is a standalone Python script. Phase 1 is the entry point — ElevenLabs audio generation.

### Pipeline Phases

| Phase | Script | Status | Description |
|-------|--------|--------|-------------|
| 1 | `phase1_audio_gen.py` | **Build first** | ElevenLabs TTS — generates 2 audio variations per script line |
| 2 | Human creative | Manual | Keith selects audio take, reviews MidJourney prompts, sources imagery |
| 3 | `phase3_combine.py` | Pending | Combines selected audio + visual assets |
| 4 | `phase4_captions.py` | Pending | Auto-captions and enhancement pass |
| 5 | `phase5_colorgrade.py` | Pending | Color grading |
| 6 | `phase6_upload.py` | Pending | YouTube upload via API |

Each phase script is **standalone** — no phase auto-triggers the next. Keith manually reviews outputs between phases.

---

## Repository Structure

```
divinemalfunction_automations/
├── CLAUDE.md                   # This file
├── config/
│   └── .env                    # API keys — NEVER commit this
├── scripts/
│   └── voiceover.csv           # Source CSV with script lines
├── audio/
│   └── raw/                    # Phase 1 output (gitignored)
│       ├── 001_A.mp3
│       ├── 001_B.mp3
│       └── ...
├── phase1_audio_gen.py
├── requirements.txt
└── .gitignore
```

---

## CSV Structure

The source CSV (`scripts/voiceover.csv`) has these columns:

| Column | Description |
|--------|-------------|
| `File_Number` | Integer — becomes the output filename prefix (zero-padded to 3 digits) |
| `Section` | Label for the segment (e.g., "Intro", "Act 1") |
| `Image_Name` | Reference name for the corresponding visual asset |
| `VoiceOver_Line` | The text to be spoken — **this is the TTS input** |
| `MidJourney_Prompt` | MidJourney prompt for the visual (used in Phase 2+) |
| `Cinematic_Variant` | Variant note for visual treatment |
| `Voice` | (Optional) Voice to use: `keith` or `spider` — defaults to `keith` if blank |

---

## Phase 1: Audio Generation

### What It Does

- Reads `VoiceOver_Line` and optional `Voice` column from each CSV row
- Selects voice per-row: Keith or Spider (defaults to Keith if blank)
- Calls ElevenLabs TTS API twice per line with different `voice_settings`
- Saves two audio files per line: `{file_num}_A.mp3` and `{file_num}_B.mp3`
- Keith auditions both takes and picks one during the human creative phase

### A/B Variation Strategy

The script supports **two voices**: Keith and Spider (Dr. Spider House persona). Voice selection is per-row via the `Voice` column in the CSV (defaults to Keith if blank).

For each line, the script generates **two takes (A and B)** using the same voice with different `voice_settings`:

- **Take A** — Higher stability (0.65) — more consistent, controlled delivery
- **Take B** — Lower stability (0.35) — more expressive, variable delivery

This produces genuinely different takes from the same voice. The variation is creative, not cosmetic.

### SDK — Current Protocol

Uses the **current ElevenLabs Python SDK** (v1.x+). Key patterns:

```python
from elevenlabs.client import ElevenLabs

client = ElevenLabs(api_key=api_key)

# List voices to find/verify voice ID
response = client.voices.search()
for voice in response.voices:
    print(voice.voice_id, voice.name)

# Voice-specific model selection
model_map = {
    "keith": "eleven_multilingual_v2",   # V2 for Keith (V3 causes nasally artifacts)
    "spider": "eleven_v3",                # V3 for Spider (better expressiveness)
}

# Generate audio
audio_bytes = client.text_to_speech.convert(
    voice_id="YOUR_VOICE_ID",
    text="Text to speak",
    model_id=model_map["keith"],  # Use appropriate model for the voice
    output_format="mp3_44100_128",
    voice_settings={
        "stability": 0.5,           # A take: ~0.65 / B take: ~0.35
        "similarity_boost": 0.80,
        "style": 0.25,
        "use_speaker_boost": True,
    }
)

with open("output.mp3", "wb") as f:
    for chunk in audio_bytes:
        f.write(chunk)
```

**Do NOT use:** `client.generate()`, `Voices()`, `Models()` as standalone objects — these are old SDK patterns from v0.x and will fail.

### Models Reference

| Model | Use case |
|-------|----------|
| `eleven_multilingual_v2` | Required for Keith voice — V3 produces nasally artifacts |
| `eleven_v3` | Required for Spider voice — better expressiveness for the Dr. Spider House persona |
| `eleven_flash_v2_5` | Fast/cheap, use for testing only |

**Voice-Specific Model Requirements:**

Both Keith and Spider were created using ElevenLabs' **Professional Voice Clone** method, but they respond differently to model versions:

- **Keith voice:** MUST use `eleven_multilingual_v2` — V3 produces unacceptable nasally artifacts
- **Spider voice:** MUST use `eleven_v3` — better audio quality and expressiveness for the diagnostician persona

The script automatically selects the correct model per voice via the `MODEL_MAP` configuration.

### Running Phase 1

```bash
# Full CSV
python phase1_audio_gen.py --csv scripts/voiceover.csv

# Test subset (rows 1-3 only)
python phase1_audio_gen.py --csv scripts/voiceover.csv --rows 1-3
```

### Output Naming Convention

```
audio/raw/001_A.mp3   ← File_Number 1, Take A (stable)
audio/raw/001_B.mp3   ← File_Number 1, Take B (expressive)
audio/raw/002_A.mp3
audio/raw/002_B.mp3
```

---

## Environment Setup

### Required API Keys

**`config/.env`** — create this file, never commit it:

```bash
# ElevenLabs
ELEVENLABS_API_KEY=your_key_here
VOICE_KEITH=your_keith_voice_id_here
VOICE_SPIDER=your_spider_voice_id_here

# Future phases (add as needed)
# YOUTUBE_CLIENT_ID=
# YOUTUBE_CLIENT_SECRET=
```

### Getting Your Voice IDs

1. Log into ElevenLabs dashboard
2. Go to **Voices** → find your cloned voices
3. Click each voice → voice ID appears in the URL or detail panel
4. Voice IDs look like: `JBFqnCBsd6RMkjVDRZzb`
5. Copy both Keith and Spider voice IDs into `config/.env`

### Getting a New ElevenLabs API Key

1. Log into ElevenLabs dashboard
2. Bottom-left → **Developers** → **API Keys** tab
3. Create new key, set a credit limit as a safety rail
4. Copy immediately — it won't be shown again

### Python Environment

```bash
# From divinemalfunction_automations/
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**`requirements.txt`:**
```
elevenlabs>=1.2.0
python-dotenv>=1.0.0
pandas>=2.0.0
```

---

## Key Behaviors to Preserve Across All Phase Scripts

- **Skip-if-exists:** Never regenerate a file that already exists — protects API credits on reruns
- **`--rows` flag:** Always support a row range argument for testing subsets before full runs
- **`config/.env` path:** All scripts load from `config/.env`, not root `.env`
- **Exit code 1 on failure:** Non-zero exit if any generation fails — allows downstream detection
- **Zero-padded file numbers:** File_Number → `zfill(3)` → `001`, `042`, `123`
- **Verbose console output:** Print what's happening — voice used, file saved, skip reason

---

## Content Context

**Channel:** DivineMalfunction — Sacred Technology media arm of HolyHell.io  
**Aesthetic:** Sacred Technology — ancient wisdom + AI automation + systems design. Mythic framing, forensic precision, cosmic humor. Not wellness content.  
**Voice persona:** Dr. Spider House 🩺🕷️ — diagnostician-journalist register  
**Audience bridge:** LinkedIn-first content repurposed for Shorts format

---

## What NOT to Do

- Don't use `client.generate()` — old API, deprecated
- Don't reference voices by name string in the new SDK — use `voice_id`
- Don't commit `config/.env` or anything in `audio/`
- Don't auto-chain phases — each phase is a manual handoff
- Don't add YouTube upload logic to early phase scripts
- Don't install packages globally — use the venv

---

## Reference

- ElevenLabs SDK: https://github.com/elevenlabs/elevenlabs-python
- ElevenLabs API docs: https://elevenlabs.io/docs/api-reference/introduction
- ElevenLabs voice library: https://elevenlabs.io/docs/api-reference/voices
