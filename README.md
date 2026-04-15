# DivineMalfunction Automations

YouTube Shorts production pipeline for the [DivineMalfunction](https://youtube.com/@divinemalfunction) channel — Sacred Technology media from [HolyHell.io](https://holyhell.io).

## Overview

6-phase automation pipeline for producing YouTube Shorts from scripted voiceover CSV files. Each phase is standalone — no auto-chaining. Manual review between phases.

### Pipeline

| Phase | Script | Status | Description |
|-------|--------|--------|-------------|
| 1 | `phase1_audio_gen.py` | ✅ Complete | ElevenLabs TTS — generates 2 audio variations per script line |
| 2 | Human creative | Manual | Select audio take, review MidJourney prompts, source imagery |
| 3 | `phase3_combine.py` | Pending | Combine selected audio + visual assets |
| 4 | `phase4_captions.py` | Pending | Auto-captions and enhancement |
| 5 | `phase5_colorgrade.py` | Pending | Color grading |
| 6 | `phase6_upload.py` | Pending | YouTube upload via API |

## Quick Start

### 1. Environment Setup

```bash
# Clone repo
git clone https://github.com/cultimedia/divinemalfunction.git
cd divinemalfunction_automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create `config/.env` (never commit this file):

```bash
# ElevenLabs
ELEVENLABS_API_KEY=your_api_key_here
VOICE_KEITH=your_keith_voice_id_here
VOICE_SPIDER=your_spider_voice_id_here
```

**Getting ElevenLabs credentials:**
1. Log into [ElevenLabs dashboard](https://elevenlabs.io)
2. **API Key**: Bottom-left → Developers → API Keys
3. **Voice IDs**: Voices → select voice → ID appears in URL/detail panel

### 3. Run Phase 1

```bash
# Test on subset (rows 1-3)
python phase1_audio_gen.py --csv scripts/voiceover.csv --rows 1-3

# Full CSV
python phase1_audio_gen.py --csv scripts/voiceover.csv
```

Output: `audio/raw/001_A.mp3`, `001_B.mp3`, etc.

## CSV Structure

Source file: `scripts/voiceover.csv`

| Column | Description |
|--------|-------------|
| `File number` | Becomes output filename (e.g., `st1` → `001`) |
| `Section` | Segment label (Intro, Act 1, etc.) |
| `Image Name` | Visual asset reference |
| `VoiceOver Line` | Text to be spoken (TTS input) |
| `MidJourney Prompt` | Image generation prompt |
| `Cinematic Variant` | Visual treatment note |
| `Voice` | `keith` or `spider` (defaults to `keith`) |

## Phase 1 Details

### Dual-Voice System

- **Keith voice**: Primary narrator
- **Spider voice**: Dr. Spider House persona (diagnostician-journalist register)

Voice selection is per-row via the `Voice` column.

### A/B Variation

Each script line generates **two audio takes** using the same voice:

- **Take A** (stability 0.65): Controlled, consistent delivery
- **Take B** (stability 0.35): Expressive, dynamic delivery

Output: `{file_num}_A.mp3` and `{file_num}_B.mp3`

### Features

- **Skip-if-exists**: Won't regenerate existing files (protects API credits)
- **Row range testing**: `--rows 1-5` for subset testing
- **ElevenLabs v3 model**: Most expressive for scripted narration
- **Rate limiting**: 0.75s delay between API calls

## Project Structure

```
divinemalfunction_automations/
├── README.md                   # This file
├── CLAUDE.md                   # Claude Code project context
├── phase1_audio_gen.py         # Phase 1: Audio generation
├── requirements.txt            # Python dependencies
├── .gitignore
├── config/
│   └── .env                    # API keys (DO NOT COMMIT)
├── scripts/
│   └── voiceover.csv           # Source CSV with script lines
└── audio/
    └── raw/                    # Phase 1 output (gitignored)
        ├── 001_A.mp3
        ├── 001_B.mp3
        └── ...
```

## Content Context

**Channel**: DivineMalfunction — Sacred Technology media
**Aesthetic**: Ancient wisdom + AI automation + systems design
**Voice Persona**: Dr. Spider House 🩺🕷️
**Format**: LinkedIn-first content repurposed for Shorts

Mythic framing, forensic precision, cosmic humor. Not wellness content.

## Development

See `CLAUDE.md` for complete project context, SDK usage patterns, and phase scripting guidelines.

## License

© HolyHell.io / DivineMalfunction.com
