# Skill Bridge — Comprehensive Project Report

## 1. Executive Summary

**Skill Bridge** is a peer-to-peer student skill exchange and earning platform. It enables college students to teach skills they possess to earn platform credits and spend those credits to learn new skills from their peers. The project addresses the lack of affordable, two-way interactive peer learning by providing a credit-based barter economy augmented by AI-driven tutor matching and session summaries.

---

## 2. Tech Stack Architecture

### Backend & Framework

- **Language**: Python 3.x
- **Framework**: Django 6.0+
- **Authentication**: `django-allauth`
  - Custom signup form (`SkillBridgeSignupForm`) requesting age and college details.
  - Social OAuth integration with **Google** and **GitHub** (`allauth.socialaccount`).
  - Custom Social Account Adapter (`CustomSocialAccountAdapter`) for seamless profile creation.
  - Password Reset workflow powered by **Resend SMTP API** (`smtp.resend.com`) with automated fallback to Django's console email backend.
- **Database**: SQLite3 (`db.sqlite3`) for local development; configured via Django ORM. (Production target: PostgreSQL).
- **Video**: Self-hosted **Jitsi Meet** via `docker-jitsi-meet` (4 containers: `web`/`prosody`/`jicofo`/`jvb` — no Jigasi/Jibri), embedded via `external_api.js` from `JITSI_BASE_URL`.
- **Audio Transcription**: `google-genai` + `GEMINI_API_KEY` (STT_PROVIDER=gemini) behind `transcribe(audio_path)->str` interface; `openai_whisper` stubbed for future swap. Async via **Celery + Redis** (with `CELERY_TASK_ALWAYS_EAGER` fallback for local dev without Redis).
- **Summarization**: `google-genai` `gemini-2.5-flash`/`gemini-flash-latest` — same `GEMINI_API_KEY` for transcription + summary.
- **Storage**: Django `FileField` via storage API — `MEDIA_ROOT` local (`STORAGE_BACKEND=local`) → `S3` later via `django-storages` + `boto3` when `STORAGE_BACKEND=s3`.
- **Config**: All env via `.env` + `settings.py` `os.environ.get` (no hardcoded hosts; `JITSI_BASE_URL`, `STT_PROVIDER`, `GEMINI_API_KEY`, `STORAGE_BACKEND`, `CELERY_BROKER_URL` all config-driven).

### Frontend & UI/UX Design System

- **Templates**: Django HTML Templates (`landing.html`, `dashboard.html`, `profile.html`, and customized `django-allauth` account templates).
- **Styling**: Modern custom CSS (`styles.css`) utilizing CSS variables, glassmorphism card designs, responsive grids, and micro-interactions.
- **Color Palette**: Deep Teal (`#0b2e2b`), Mid Teal (`#0d9488`), Amber Accent (`#d97706`), Cream (`#fcfbf4`), and Butter Yellow theme.
- **Typography**: Google Fonts — _Fraunces_ (display headings), _Space Grotesk_ (body), _Plus Jakarta Sans_, and _Fira Code_ (monospace code blocks).
- **Icons**: FontAwesome 6 icon library.
- **Static Prototype Workspace**: High-fidelity standalone HTML/CSS/JS prototype located in `uiuxprg1/`.

---

## 3. How to Run the Project

### Prerequisites

- Python 3.10+
- `pip` or `uv` package manager

### Setup Steps

1. **Navigate to the Project Root**:

   ```bash
   cd d:/rashaSB/skillbridge
   ```

2. **Activate the Virtual Environment**:
   - On Windows (PowerShell / CMD):
     ```powershell
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Configure Environment Variables (`.env`)**:
   Copy `.env.example` → `.env` in the project root. For the self-hosted Jitsi + transcript demo, set at minimum:

   ```env
   SECRET_KEY=your-django-secret-key
   RESEND_API_KEY=your-resend-api-key # Optional
   DEFAULT_FROM_EMAIL=onboarding@resend.dev
   GEMINI_API_KEY=your-gemini-key          # aistudio.google.com/apikey — used for BOTH transcription + summary
   JITSI_BASE_URL=http://localhost:8443       # local Docker; later https://meet.yourhost
   STT_PROVIDER=gemini                     # gemini | openai_whisper | local_whisper
   STORAGE_BACKEND=local                   # local | s3
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   # optional: CELERY_TASK_ALWAYS_EAGER=true  # run transcription sync without Redis (local dev fallback)
   # For S3 later:
   # AWS_ACCESS_KEY_ID= AWS_SECRET_ACCESS_KEY= AWS_STORAGE_BUCKET_NAME= AWS_S3_REGION_NAME=
   # For self-hosted Jitsi docker (docker/jitsi/.env is separate, generated via gen-passwords.sh):
   # see docker/jitsi/README.md — PUBLIC_URL must match JITSI_BASE_URL
   ```
   > All hosts/keys are config-driven. Moving from local demo to a real host is a `.env` change only — no code change.
   > **Jitsi LAN note:** set `DOCKER_HOST_ADDRESS` + `JVB_ADVERTISE_IPS` to the host LAN IP in `docker/jitsi/.env` and use HTTPS (cert required for mic on non-localhost). See `docker/jitsi/README.md`.

4. **Apply Database Migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create Admin Superuser (Optional)**:

   ```bash
   python manage.py createsuperuser
   ```

6. **Start Development Server**:
   ```bash
   python manage.py runserver 8000
   ```
   Access the app at **`http://localhost:8000/`** (or active port).

---

## 4. Features Implemented (Phase 1 MVP - Complete)

### 🔐 1. Authentication & Social Auth Flow

- **Dual Authentication**: Sign in via Email or Username.
- **OAuth 2.0 Integration**: One-click login with **Google** and **GitHub** (`SOCIALACCOUNT_LOGIN_ON_GET = True`).
- **Customized Authentication UI**:
  - Theme-matched Login Page (`templates/account/login.html`).
  - Signup Page (`templates/account/signup.html`) collecting student age & college.
  - Logout Confirmation (`templates/account/logout.html`).
  - Password Reset Request & Confirmation pages (`templates/account/password_reset*.html`).
- **Transactional Password Reset Email**: Integration with Resend SMTP API (`smtp.resend.com:587`).

### 👤 2. User Profiles & Credit System Foundation

- **Automatic Profile Signals**: Every registered user automatically receives a `UserProfile` instance via post-save signals.
- **Starting Credits**: All new students are credited **10 starting credits** upon account creation.
- **Profile Metadata**: Stores age, college, department, bio, credit balance, and avatar URL.
- **Profile View**: Dedicated user profile page (`/profile/`).

### 📚 3. Skill Listing & Management

- **Database Model (`Skill`)**: Supports skill categorization (_Programming_, _Design_, _Languages_, _Music_, _Academics_, _Business_, _Other_), skill intent (`TEACH` vs `LEARN`), proficiency (_Beginner_, _Intermediate_, _Advanced_), and peer rating metrics.
- **Add Skill Modal & Endpoint**: Interactive modal on the dashboard allowing logged-in students to add skills they want to teach or learn via `add_skill_view`.

### 🖥️ 4. Interactive Dashboard & Discovery Feed

- **Landing Page (`landing.html`)**: Dynamic hero landing page for unauthenticated visitors with call-to-actions to Sign Up or Login.
- **Student Dashboard (`dashboard.html`)**: Logged-in user dashboard featuring:
  - Personal welcome banner and credit counter.
  - Metric counters for skills actively taught vs. being learned.
  - Peer Skill Discovery feed displaying teachable skills offered by other students.
  - Dynamic client-side category filtering and search functionality.

### 🎨 5. Standalone UI Prototype (`uiuxprg1/`)

- Fully-functional static prototype containing complete UI mockups, interactive session cards, code snippet showcase, and sidebar navigation.

---

## 5. Features Implemented (updated)

### Phases A–E: Self-Hosted Jitsi + AI Transcript Summary (instructions/meet-transcription-plan.md)
- **Phase A — Self-hosted Jitsi (Docker):** vendored `docker-jitsi-meet` under `docker/jitsi/`, `gen-passwords.sh`, `HTTP_PORT=8001`/`HTTPS_PORT=8443`/`PUBLIC_URL=https://localhost:8443`/`DOCKER_HOST_ADDRESS`+`JVB_ADVERTISE_IPS`, 4 containers only (`web`/`prosody`/`jicofo`/`jvb`, no Jigasi/Jibri), `docker-compose.yml` (project root) for `redis`+`celery`.
- **Phase B — Embed Jitsi:** `Session.room_name` + `build_jitsi_url` (config-driven `JITSI_BASE_URL`), `GET /sessions/<pk>/room/` (participant-only, `accepted` only, creates `SessionRecording` for consent), `external_api.js` from `JITSI_BASE_URL` + `JitsiMeetExternalAPI`, leaving returns to `/sessions/`.
- **Phase C — Audio capture:** consent gate (notice + checkbox, `POST /sessions/<pk>/consent/` persists `consent_learner/teacher`, no silent recording), `MediaRecorder` (`audio/webm`) on local mic, `POST /sessions/<pk>/upload-audio/` (CSRF, participant-only, consent-gated) → `SessionRecording.audio_file` (`session_audio/`, via storage API) + `duration_seconds` + `status=uploaded` (`MEDIA_ROOT` now → S3 later; per-browser mic only, limitation documented).
- **Phase D — Transcription:** `editor/transcription.py` `transcribe(audio_path)->str` (STT_PROVIDER=gemini default; `gemini` reuses `google-genai` + `GEMINI_API_KEY` via `client.files.upload` + `generate_content`; `openai_whisper` wired-but-inert until `OPENAI_API_KEY` set; all return ""+log never raise), `skillbridge_project/celery.py` + `editor/tasks.py` `transcribe_recording` (`processing`→`done`/`failed`), `editor/management/commands/transcribe_pending.py` fallback, enqueued from upload (eager vs async, gracefully handled without broker).
- **Phase E — Transcript → Summary:** `editor/ai.py` prefers `recording.transcript` then `notes` (same prompt, same `ai_summary` field/UI), `generate_summary_view` allows transcript-without-notes, `sessions.html` shows `Generate AI summary from transcript` when transcript ready (still explicit button, no auto-generate), notes-only path unchanged, summary rendered via `markdownify` + butter-themed card.

### Other implemented
- Session Lifecycle & Credits (Phase 2), Ratings & Profile Privacy, AI Session Summary (notes-based) — see progress-tracker.

## 5b. Features Pending / Roadmap

| Phase | Module | Status | Next |
|-------|--------|--------|------|
| Phase F (done) | Deployability hardening | ✅ Done | S3 wiring, JWT notes, docs, no-hardcoded-hosts check |
| Future | AI Tutor Matching | 📋 Planned | Weighted scoring + embeddings |
| Future | Realtime Chat | 📋 Planned | Django Channels + WebSockets |
| Future | Production DB | 📋 Planned | SQLite → PostgreSQL, hosting |

---

## 6. Directory Structure & Key Files

```
skillbridge/
├── manage.py
├── skillbridge_project/
│   ├── settings.py              # All env via .env: JITSI_BASE_URL, STT_PROVIDER, GEMINI_API_KEY, STORAGE_BACKEND, CELERY_*
│   ├── celery.py                # Celery app (skillbridge_project)
│   └── urls.py                  # + MEDIA_URL serve in DEBUG
├── editor/
│   ├── models.py                # UserProfile, Skill, Session (room_name), SessionRecording (OneToOne, audio_file, transcript, status, consent_learner/teacher), CreditTransaction, Rating
│   ├── views.py                 # room_view, upload_consent, upload_audio, generate_summary (transcript-preferred), join→room redirect
│   ├── transcription.py         # STT_PROVIDER interface (gemini implemented, openai_whisper stub)
│   ├── tasks.py                 # transcribe_recording (Celery)
│   ├── ai.py                    # generate_session_summary (transcript > notes, same GEMINI_API_KEY)
│   ├── management/commands/transcribe_pending.py
│   ├── templatetags/md.py       # markdownify
│   ├── templates/editor/        # sessions.html, room.html (Jitsi embed + MediaRecorder + consent), etc.
│   ├── static/editor/           # styles.css (tokens), extras.css (summary card + room)
│   └── migrations/0007_add_recording_and_room.py  # one migration for Session.room_name + SessionRecording
├── docker/
│   ├── jitsi/                   # vendored docker-jitsi-meet (docker-compose.yml + .env via gen-passwords.sh) — 4 containers only
│   │   └── README.md            # bring-up + DOCKER_HOST_ADDRESS LAN note
│   └── docker-compose.yml       # project root: redis + celery (hostable path)
├── media/session_audio/         # uploaded audio (local, gitignored; S3 when STORAGE_BACKEND=s3)
├── templates/account/           # allauth overrides
├── instructions/
│   ├── meet-transcription-plan.md
│   └── progress-tracker.txt     # phase-by-phase log
└── requirements.txt             # Django, allauth, google-genai, Markdown, bleach, celery, redis, django-storages, boto3
```

## 7. Limitations (documented, not fixed)
- `MediaRecorder` captures each participant's own mic per browser; merged two-speaker transcript would need server-side mixing (Jibri/Jigasi) — out of scope.
- Same-machine two-tab demo is supported; LAN needs `DOCKER_HOST_ADDRESS`/`JVB_ADVERTISE_IPS` + HTTPS cert for mic access on non-localhost origins.
- Jitsi 4-container stack only; audio is client-side so no transcription plugins needed.

