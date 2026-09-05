# 🎙️ Audio Transcription & AI Summarization Platform

An end-to-end full-stack web platform for intelligent meeting audio processing, automatic speech recognition (ASR), speaker diarization, voice profile recognition, NLP text preprocessing, extractive/abstractive summarization, AI executive refinement via LLMs (GPT-4o), and automated PDF export.

---

## 🌟 Key Features

- **🎙️ High-Accuracy Speech-to-Text**: Powered by OpenAI's **Whisper** model with support for configurable models (`tiny`, `base`, `small`, `medium`, `large`).
- **👥 Advanced Speaker Diarization**: Multi-speaker identification and separation utilizing **SpeechBrain ECAPA-TDNN** deep speaker embeddings, MFCC extraction, and **Agglomerative/Spectral Clustering**.
- **🗣️ Voice Profile Management**: Pre-register speaker voice samples to automatically label and attribute spoken segments to real names during transcription.
- **🧹 Intelligent NLP Preprocessing**:
  - Automatic removal of filler words (*"um"*, *"uh"*, *"you know"*), timestamps, and duplicate phrases.
  - Sentence segmentation and contraction repair.
  - **Phonetic & Fuzzy Name Standardization**: Standardizes speaker names across transcripts using Levenshtein distance, Jellyfish, and Soundex matching.
- **🧩 Speaker-Aware Text Chunking**: Custom chunking algorithm that respects speaker turn boundaries to maintain contextual attribution during LLM processing.
- **🤖 AI Executive Refinement**: Refines raw transcripts and summaries using **GPT-4o** (via Azure/OpenAI inference) into structured meeting minutes:
  - **Meeting Agenda**
  - **Key Discussion Points** (grouped by topic with speaker attributions)
  - **Action Items** (assigned with owners)
  - **Required Follow-ups**
  - **Suggested Topics for Future Meetings**
- **📄 One-Click PDF Export**: Download professionally styled PDF reports generated dynamically via **ReportLab**.
- **💻 Modern Next.js Dashboard**: Sleek dark/light UI built with **Next.js 14**, **TypeScript**, **Tailwind CSS**, **Framer Motion** animations, and **Radix UI** primitives.

---

## 🏗️ System Architecture

```
                                    +-----------------------------------+
                                    |         Next.js Frontend          |
                                    |  (React, TS, Tailwind, Framer)    |
                                    +-----------------+-----------------+
                                                      |
                                                      | HTTP / REST API
                                                      v
                                    +-----------------------------------+
                                    |         Flask Backend API         |
                                    +-----------------+-----------------+
                                                      |
        +-------------------------+-------------------+-------------------------+
        |                         |                   |                         |
        v                         v                   v                         v
+---------------+       +------------------+  +---------------+       +-------------------+
| Audio Noise   |       | Whisper ASR &    |  | NLP Pipeline  |       | AI LLM Refinement |
| Reduction &   | ----> | Speaker Diarize  |->| & Text        | ----> | (GPT-4o via       |
| Filtering     |       | (ECAPA-TDNN)     |  | Chunker       |       | Azure/OpenAI API) |
+---------------+       +------------------+  +---------------+       +-------------------+
                                                                                |
                                                                                v
                                                                      +-------------------+
                                                                      | PDF Report        |
                                                                      | Generator         |
                                                                      +-------------------+
```

---

## 📁 Project Structure

```
.
├── backend/                        # Flask Backend Service
│   ├── app.py                      # Main Flask application & API routes
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Backend environment template
│   ├── models/                     # Core ML & NLP processing modules
│   │   ├── audio_processor.py      # Audio loading, spectral denoiser, Butterworth filter
│   │   ├── speaker_diarization.py  # Whisper transcription & speaker clustering
│   │   ├── voice_sample_manager.py # ECAPA-TDNN voice embeddings & speaker enrollment
│   │   ├── text_preprocessor.py    # Text cleaning, filler removal & fuzzy name matching
│   │   ├── speaker_aware_chunker.py# Context-preserving text chunker
│   │   ├── text_summarizer.py      # Topic grouping & extractive summarization
│   │   └── pdf_generator.py        # ReportLab PDF report generation
│   ├── sample/                     # Preloaded speaker voice samples
│   └── utils/                      # Helper scripts
│
├── frontend/                       # Next.js 14 Frontend Application
│   ├── app/                        # Next.js App Router (pages & global layouts)
│   ├── components/                 # React components
│   │   ├── audio-upload.tsx        # File drag-and-drop & configuration form
│   │   ├── processing-results.tsx  # Interactive summary & transcript renderer
│   │   ├── speaker-manager.tsx     # Active speaker selector panel
│   │   └── voice-sample-manager.tsx# Speaker voice enrollment component
│   ├── package.json                # Frontend Node dependencies
│   └── .env.example                # Frontend environment template
│
└── README.md                       # Project documentation
```

---

## 🚀 Tech Stack

### **Backend**
- **Framework**: Flask, Flask-CORS
- **ASR Model**: OpenAI Whisper (`openai-whisper`)
- **Diarization & Audio ML**: PyTorch, Torchaudio, SpeechBrain (`spkrec-ecapa-voxceleb`), Librosa, SoundFile, SciPy
- **NLP & Text Processing**: NLTK, spaCy, Jellyfish, Levenshtein
- **LLM Integration**: OpenAI SDK (Azure AI Inference / GPT-4o)
- **Document Generation**: ReportLab, fpdf2

### **Frontend**
- **Framework**: Next.js 14 (App Router), React 18, TypeScript
- **Styling**: Tailwind CSS, PostCSS, `next-themes`
- **UI & Animations**: Framer Motion, Radix UI, Lucide Icons, Tabler Icons

---

## 🛠️ Prerequisites & Requirements

Before setting up the project, ensure you have the following installed on your system:

1. **Python 3.9+** (64-bit)
2. **Node.js 18+** & `npm`
3. **FFmpeg**: Required by Whisper and Librosa for audio decoding.
   - **Windows**: Install via `winget install FFmpeg` or download from [ffmpeg.org](https://ffmpeg.org/) and add to system PATH.
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt update && sudo apt install ffmpeg`

---

## ⚙️ Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
# source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

# Create environment configuration file
cp .env.example .env
```

> **Note**: Open `backend/.env` and insert your `GITHUB_TOKEN` or Azure AI inference key if you wish to enable GPT-4o summary refinement.

```env
BASE_URL=https://models.inference.ai.azure.com
MODEL=gpt-4o
GITHUB_TOKEN=your_github_or_azure_token_here
```

**Start Backend Server:**
```bash
python app.py
```
The backend API server will start on `http://localhost:5328`.

---

### 3. Frontend Setup

Open a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Create environment configuration file
cp .env.example .env.local
```

Ensure `frontend/.env.local` points to your backend URL:
```env
NEXT_PUBLIC_API_URL=http://localhost:5328
```

**Start Frontend Development Server:**
```bash
npm run dev
```
Open your browser and navigate to **`http://localhost:3000`**.

---

## 📡 API Reference Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Returns server health, model initialization status, and AI refinement availability. |
| `/api/upload-audio` | `POST` | Uploads audio file (`multipart/form-data`) with settings for transcription, diarization, and summarization. |
| `/api/refine-summary` | `POST` | Refines existing summary content using GPT-4o AI post-processing. |
| `/api/upload-voice-sample` | `POST` | Enrolls a new speaker voice sample audio to create speaker embeddings. |
| `/api/speakers` | `GET` | Fetches list of preloaded, uploaded, and active enrolled speakers. |
| `/api/speakers/select` | `POST` | Updates active speakers for voice matching during diarization. |
| `/api/download-pdf` | `POST` | Generates and streams a downloadable PDF version of the meeting summary. |
| `/api/processing-config` | `GET`/`POST` | Fetches or updates text preprocessing configuration parameters. |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
