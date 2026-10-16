Looking for an AI Image/Video/Audio Analysis Web App?  
Order on Fiverr: [AI Media Analysis Web App](https://www.fiverr.com/aftab_hussain_c)

# AI Media Detection Platform

A web platform that analyzes images, videos, and audio to determine whether they are AI-generated or authentic, combining statistical AI models, digital forensics, and cryptographic content-provenance verification.

---

## 1. Overview

This platform lets a user upload an image, video, or audio file and receive:

- An **AI probability score**, **human probability score**, **confidence score**, and **manipulation score**
- A **final recommendation** (Authentic / Suspicious / Confirmed AI Generated)
- A full **forensic breakdown**: metadata (EXIF), Error Level Analysis, sensor-noise analysis, JPEG double-compression analysis, face detection, and an explainable-AI heatmap
- **Cryptographic verification** via C2PA Content Credentials when the file was signed by its generator (OpenAI, Google, Adobe, etc.)
- A downloadable **PDF forensic report**
- A **persistent audit trail** of every scan performed

The target use case follows the original brief: a tool useful to media organizations, researchers, and the general public for verifying suspected AI-generated content, with the explicit understanding that **no detector is 100% accurate** and results should support — not replace — human judgment for high-stakes decisions.

---

## 2. Architecture

```
┌─────────────────────┐        HTTP/JSON         ┌──────────────────────────┐
│   React + Vite       │ ───────────────────────▶ │   FastAPI Backend         │
│   (Tailwind UI)       │ ◀─────────────────────── │   (Python)                 │
└─────────────────────┘                           └───────────┬──────────────┘
                                                                │
                     ┌──────────────────────────────────────────┼───────────────────────────────┐
                     │                          │                          │                     │
             ┌───────▼────────┐        ┌────────▼────────┐       ┌────────▼────────┐   ┌─────────▼─────────┐
             │  AI Detectors    │        │  Forensics Layer  │       │  C2PA Verifier    │   │  SQLite Database    │
             │  (image/video/    │        │  (EXIF, ELA,       │       │  (cryptographic    │   │  (scan history,     │
             │   audio models)   │        │   noise, DCT,       │       │   provenance)       │   │   full JSON record)  │
             └───────┬────────┘        │   face, heatmap)   │       └────────────────────┘   └─────────────────────┘
                     │                  └─────────────────────┘
             ┌───────▼────────┐
             │ PDF Report        │
             │ Generator          │
             └────────────────────┘
```

**Backend:** FastAPI (Python) &nbsp;|&nbsp; **Frontend:** React + Vite + Tailwind &nbsp;|&nbsp; **Database:** SQLite via SQLAlchemy &nbsp;|&nbsp; **AI runtime:** PyTorch + Hugging Face Transformers

---

## 3. Detection Pipeline

### 3.1 Image Analysis
| Module | Technique | Purpose |
|---|---|---|
| Metadata Analysis | EXIF extraction (Pillow) | Detects presence/absence of camera sensor metadata |
| AI Classification | `Organika/sdxl-detector` (Swin Transformer, Hugging Face) | Real vs. AI-generated (diffusion/GAN) probability |
| Error Level Analysis | JPEG re-compression differencing | Flags localized editing/tampering |
| Noise Analysis | Gaussian-residual block-variance (PRNU-inspired) | Flags unnaturally uniform noise across the frame |
| DCT Compression Analysis | 8×8 block DCT coefficient periodicity | Flags JPEG double-compression (edit/re-save) |
| Face Detection | OpenCV Haar Cascade | Detects faces; each face is independently re-scored by the AI classifier |
| Explainable AI | Occlusion Sensitivity Mapping | Heatmap showing which image regions most influenced the AI verdict |
| C2PA Verification | `c2pa-python` (Content Credentials) | Cryptographic proof of AI generation when the source platform signs it |

### 3.2 Video Analysis
- 12 frames sampled evenly across the full video duration (not just the first few seconds)
- Each frame is run through the same image AI-classifier
- Final score = weighted combination of average and peak frame scores (catches deepfakes that only show artifacts in some frames)
- Face presence tracked per sampled frame
- C2PA check applied to the video container file

### 3.3 Audio Analysis
- `MelodyMachine/Deepfake-audio-detection-V2` (Wav2Vec2-based) for synthetic-voice / voice-clone detection
- First 15 seconds analyzed (standard practice for audio classification; keeps latency low)
- C2PA check applied to the audio file

### 3.4 Score Fusion Logic
If a **valid C2PA manifest confirms AI generation**, that cryptographic proof overrides the statistical model output (score set to 99% confidence) — proof takes precedence over a probabilistic guess. Otherwise, the model's own probability drives the verdict, and noise/DCT analysis are surfaced as **supplementary, non-authoritative signals** in the report (each technique has known blind spots, so no single number is treated as final truth — consistent with the "ensemble + human review" principle in the original brief).

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, Tailwind CSS, lucide-react, axios |
| Backend | FastAPI, Uvicorn, Pydantic |
| AI / ML | PyTorch, Hugging Face Transformers |
| Computer Vision | OpenCV, Pillow, NumPy |
| Audio | librosa |
| Database | SQLite, SQLAlchemy ORM |
| Provenance | c2pa-python (C2PA Content Credentials) |
| Reporting | ReportLab (PDF generation) |

---

## 5. Project Structure

```
ai-media-detection/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entrypoint
│   │   ├── api/endpoints.py         # All API routes
│   │   ├── core/
│   │   │   ├── config.py            # Settings (paths, env)
│   │   │   └── database.py          # SQLAlchemy engine/session
│   │   ├── models/scan_history.py   # DB schema
│   │   └── services/
│   │       ├── ai_detector.py       # Image AI classifier
│   │       ├── video_detector.py    # Video frame sampling + classification
│   │       ├── audio_detector.py    # Audio deepfake classifier
│   │       ├── forensics.py         # EXIF, ELA, noise, DCT, C2PA
│   │       ├── face_detector.py     # Face detection + per-face scoring
│   │       ├── explainability.py    # Occlusion heatmap generation
│   │       └── report_generator.py  # PDF report builder
│   ├── uploads/                     # Uploaded files + generated ELA/heatmap images
│   ├── reports/                     # Generated PDF reports
│   ├── app_data.db                  # SQLite database (created on first run)
│   └── requirements.txt
└── frontend/
    └── src/App.jsx                  # Main dashboard UI
```

---

## 6. Setup & Running Locally

### Backend
```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs available at `http://127.0.0.1:8000/docs`.

> First request for each media type (image/video/audio) will download the relevant pretrained model from Hugging Face (a few hundred MB each) and may take a minute — subsequent requests are fast as models stay cached in memory and on disk.

### Frontend
```powershell
cd frontend
npm install
npm run dev
```
UI available at `http://localhost:5173`.

### Requirements
- Python 3.12
- Node.js
- CPU is sufficient (no GPU required); inference is slower on CPU-only machines but fully functional

---

## 7. API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/analyze/image` | Analyze an uploaded image |
| POST | `/api/v1/analyze/video` | Analyze an uploaded video |
| POST | `/api/v1/analyze/audio` | Analyze an uploaded audio file |
| GET | `/api/v1/scans/history` | List all past scans |
| GET | `/api/v1/scans/{id}` | Full stored result for one scan |
| GET | `/api/v1/scans/{id}/report` | Download the PDF forensic report for one scan |
| GET | `/media/{filename}` | Serves generated ELA/heatmap images |

---

## 8. Known Limitations

Being transparent about these matters more than hiding them, in line with the brief's own guidance that no detector is 100% accurate:

- **Generator coverage:** The image classifier (`Organika/sdxl-detector`) is strongest on SDXL/diffusion-style outputs. Newer generators (e.g. GPT-Image, some Midjourney versions) can be missed by the model alone — this is a known, published industry-wide problem, not specific to this project (published benchmarks show detector accuracy dropping to ~18–38% against 2024+ generators). C2PA verification substantially closes this gap for platforms that sign their output (OpenAI, Google, Adobe).
- **Non-photorealistic content:** Cartoons, illustrations, and stylized art can trigger false positives, since the model was trained to distinguish photorealistic camera images from photorealistic AI images — not art styles.
- **Audio scope:** The audio model is trained on spoken voice, not music; results on songs (singing, instrumentation, studio mastering) are not meaningful.
- **C2PA is not universal proof of authenticity:** Its *absence* does not prove a file is real — Content Credentials are frequently stripped when files are re-saved, screenshotted, or forwarded through messaging apps.
- **Noise/DCT analysis are heuristic signals**, not definitive forensic proof, and are surfaced as supplementary information rather than driving the final verdict.
- **CPU-only inference:** No GPU acceleration; per-file latency is higher than a GPU-backed deployment (especially for the heatmap, which runs 16 model passes per image).

---

## 9. Future Roadmap (Not Yet Implemented)

These items are explicitly part of the original brief's later phases and require resources beyond a single-developer, CPU-only build — listed here for transparency rather than attempted with placeholder/fake implementations:

| Item | Why it's a future phase |
|---|---|
| Custom-trained proprietary detection models | Requires large labeled datasets (FaceForensics++, DFDC, ASVspoof, etc.) and multi-GPU training infrastructure (A100/H100-class), consistent with the brief's own "Phase 4" and hardware requirements |
| Cloud deployment (AWS/Azure/GCP) | Infrastructure/DevOps scope beyond application development |
| Enterprise database (PostgreSQL/MongoDB/Redis) | SQLite is sufficient at current scale; a migration path exists via SQLAlchemy when multi-user concurrency is needed |
| Video-native temporal models (TimeSformer, ViViT, SlowFast) | Multi-GB models requiring GPU inference; current approach uses frame-sampled image classification as a practical proxy |
| Prosody / voice-cloning ensemble (Whisper + RawNet + Wav2Vec2) | Requires additional specialized models and validation datasets |
| Urdu language support | Separate localization/NLP scope |
| Batch processing, audit-log exports, on-premises packaging | Enterprise feature set for a later commercialization phase |

---

## 10. Disclaimer

This system is a decision-support tool, not a certifying authority. As stated in the generated PDF reports: results should be treated as one input among several for high-stakes decisions and reviewed by a qualified human analyst before being relied upon for legal, financial, or security purposes.
