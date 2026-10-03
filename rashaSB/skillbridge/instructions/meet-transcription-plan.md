# Skill Bridge — Self-Hosted Jitsi + AI Transcript Summary: Architecture & Build Plan

> Handoff spec for the implementing agent. **Read this whole file before coding.**
> Scope: self-host Jitsi via Docker (local now, hostable later), embed it in the Django
> app, capture session audio in-browser, transcribe with OpenAI Whisper, and summarize
> the transcript with the existing Gemini helper.

---

## 0. Guiding principles (do not violate)

1. **Config-driven, not hardcoded.** Every environment-specific value (Jitsi URL, STT
   provider + key, storage backend, broker URL) comes from environment variables loaded
   from `.env`, exactly like the existing `GOOGLE_CLIENT_ID` / `GEMINI_API_KEY` pattern.
   The goal: moving from "localhost demo" to "a real host" is a `.env` edit, never a
   code change. No `localhost`/`127.0.0.1` string literals in app code.
2. **Swap points stay behind interfaces.** Three things must be swappable by config:
   - **STT provider** (Gemini audio now → OpenAI Whisper or self-hosted `faster-whisper`
     later) behind a `transcribe(audio_path) -> str` interface. We use **Gemini for
     transcription now** because the existing `GEMINI_API_KEY` already covers it — no
     separate OpenAI account needed. A Gemini/Google key CANNOT call Whisper (different
     provider); Whisper is a future swap set up when an OpenAI key is added.
   - **File storage** (local `MEDIA_ROOT` now → S3 later) via Django's storage backend
     (`django-storages`), never direct filesystem paths.
   - **Jitsi base URL** (local Docker now → hosted Jitsi later) via `JITSI_BASE_URL`.
3. **Don't break what works.** The credit/rating logic, the existing Gemini summary
   button, and all 7 passing tests must keep working. Transcription is additive.
4. **Scale is low (one laptop, 1–2 participants, demo).** Do not over-engineer, but DO
   keep the deployability seams above so hosting is possible later.
5. **Consent is required.** Audio is recorded. Both participants must see a clear notice
   and the recording only starts after in-app consent. No silent recording.

---

## 1. Target architecture (end state)

```
                    ┌────────────────────────────────────────────┐
                    │  Docker: self-hosted Jitsi (docker-jitsi-meet)│
                    │   web · prosody · jicofo · jvb               │
                    └───────────────▲──────────────────────────────┘
                                    │ embeds via external_api.js (iframe API)
┌──────────────┐   room page   ┌────┴─────────────┐   audio blob   ┌──────────────┐
│  Browser     │──────────────▶│  Django app      │───────────────▶│ Storage      │
│  (2 tabs)    │  MediaRecorder│  /sessions/<id>/ │  (FileField →  │ local → S3   │
│              │  captures mic │     room/        │   storage API) │              │
└──────────────┘               └────┬─────────────┘                └──────────────┘
                                    │ enqueue transcription task
                                    ▼
                         ┌──────────────────────┐   transcript    ┌──────────────┐
                         │ Celery worker + Redis │────────────────▶│ Whisper API  │
                         │ (async, dockerized)   │                 │ (STT iface)  │
                         └──────────┬───────────┘                 └──────────────┘
                                    │ transcript saved → reuse Gemini
                                    ▼
                         ┌──────────────────────┐
                         │ editor/ai.py (Gemini) │──▶ Session.ai_summary (existing UI)
                         └──────────────────────┘
```

**Why Celery + Redis:** Whisper transcription of a multi-minute clip takes too long for a
single HTTP request (it would time out). An async task queue is the "hostable" answer and
is itself dockerized. For a short (<1 min) demo clip a synchronous fallback is acceptable
as a stopgap (see Phase D notes), but the task-queue path is the intended design.

---

## 2. Data model changes (`editor/models.py`)

Add a **`SessionRecording`** model (keep `Session` lean; recordings are a separable
concern and this leaves room for S3/auditing later):

```
SessionRecording
  session            OneToOneField(Session, related_name="recording")
  audio_file         FileField(upload_to="session_audio/", storage=<default>, null=True)
  transcript         TextField(blank=True, default="")
  status             CharField  # "idle" | "uploaded" | "processing" | "done" | "failed"
  consent_learner    BooleanField(default=False)
  consent_teacher    BooleanField(default=False)
  duration_seconds   PositiveIntegerField(null=True, blank=True)
  error              CharField(max_length=300, blank=True, default="")
  created_at / updated_at
```

- `Session.room_name` — add a stable, unique Jitsi room slug (e.g. `skillbridge-<uuid>`)
  generated on accept. Keep the existing `meet_url` but derive it from `JITSI_BASE_URL`
  + `room_name` instead of the hardcoded `meet.jit.si`.
- Keep `Session.ai_summary` / `summary_generated_at` as-is — the transcript feeds the
  **same** summary field and UI.
- One migration for all of the above.

---

## 3. Configuration (`.env` / settings)

Add to `.env.example` (and read in `settings.py` via the existing env pattern):

```
# --- Jitsi (self-hosted) ---
JITSI_BASE_URL=http://localhost:8443        # local Docker; later -> https://meet.yourhost
JITSI_APP_ID=skillbridge                    # for JWT auth if enabled later
JITSI_JWT_SECRET=                           # optional, phase F / hosting

# --- Transcription ---
STT_PROVIDER=gemini                         # swap point: gemini | openai_whisper | local_whisper
GEMINI_API_KEY=                             # already present; used for BOTH transcription + summary
# OpenAI Whisper is a FUTURE swap — leave blank until an OpenAI account is set up:
OPENAI_API_KEY=
WHISPER_MODEL=whisper-1

# --- Storage ---
STORAGE_BACKEND=local                       # swap point: local | s3
AWS_ACCESS_KEY_ID=                          # only when STORAGE_BACKEND=s3
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=

# --- Async task queue ---
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

`settings.py`: configure `MEDIA_ROOT`/`MEDIA_URL`, conditionally wire `django-storages`
S3 backend when `STORAGE_BACKEND=s3`, and Celery app config. Everything defaults to the
local-demo values so a fresh clone runs with no cloud account.

---

## 4. Docker layout

Keep **two compose files**, clearly separated, so Jitsi infra and the app are decoupled:

- `docker/jitsi/` — vendored `docker-jitsi-meet` `docker-compose.yml` + its `.env`
  (generated via their `gen-passwords.sh`). Set `HTTP_PORT`/`HTTPS_PORT`,
  `PUBLIC_URL`, and — **critical for LAN** — `DOCKER_HOST_ADDRESS` to the host's IP.
  Core services only: `web`, `prosody`, `jicofo`, `jvb`. **No Jigasi, no Jibri.**
- `docker-compose.yml` (project root, optional for app) — `redis`, `celery` worker, and
  (optionally) the Django `web` + an eventual `db`. For local dev the agent may run
  Django + Celery on the host and only containerize Redis + Jitsi; either is fine as long
  as it's documented.

**Deployability note:** because audio is captured client-side (`MediaRecorder`), Jitsi
needs no transcription plugins — this keeps the self-hosted stack to the 4 standard
containers and makes a future real deploy straightforward.

---

## 5. Phase-by-phase build plan

Each phase is independently verifiable. **Do not start a phase until the previous one's
acceptance criteria pass.** Update `instructions/progress-tracker.txt` after each phase.

### Phase A — Stand up self-hosted Jitsi (Docker)
- Vendor `docker-jitsi-meet` under `docker/jitsi/`, generate its `.env`, set ports +
  `DOCKER_HOST_ADDRESS`.
- Bring up `web/prosody/jicofo/jvb`.
- **Acceptance:** open the Jitsi web UI directly (e.g. `http://localhost:8443`), create a
  room, join from **two browser tabs** on the same machine, confirm two-way audio/video.
  Document the exact URL/ports in the plan tracker.

### Phase B — Embed Jitsi in the Django app (own the room page)
- New route `sessions/<pk>/room/` → `room_view` (participant-only, session must be
  `accepted`). Replace the current "redirect to meet.jit.si" join behavior with this page.
- Template loads Jitsi **`external_api.js`** from `JITSI_BASE_URL` and instantiates
  `JitsiMeetExternalAPI` with the session's `room_name`. Build `room_name` + `meet_url`
  from `JITSI_BASE_URL` (no hardcoded host).
- **Acceptance:** both participants join the call **through the app's room page** (not the
  raw Jitsi UI), call works, leaving returns to the sessions page.

### Phase C — Capture audio in-browser + upload
- Add a **consent gate** on the room page: a clear "This session will be recorded for an
  AI summary" notice; recording starts only after the user accepts. Persist
  `consent_learner` / `consent_teacher`.
- Use `MediaRecorder` on the local mic stream to record audio (e.g. `audio/webm`). On
  "End & summarize", stop recording and POST the blob to
  `sessions/<pk>/upload-audio/` (CSRF-protected, participant-only).
- Save via the storage abstraction into `SessionRecording.audio_file`; set
  `status="uploaded"`, capture `duration_seconds`.
- **Acceptance:** after a call, an audio file exists in `MEDIA_ROOT/session_audio/` and
  the `SessionRecording` row is `uploaded`. (Recording only the **local** participant's
  mic per browser is acceptable for the demo — note this clearly.)

### Phase D — Transcription service (Whisper, async)
- `editor/transcription.py`: a provider interface `transcribe(audio_path) -> str`,
  selected by `STT_PROVIDER`. Implement the **`gemini`** provider now (reuse
  `google-genai` + `GEMINI_API_KEY`; Gemini accepts an uploaded audio file and returns a
  transcript). Stub/document an **`openai_whisper`** provider (reads `OPENAI_API_KEY`,
  `WHISPER_MODEL`) as the future swap — wired but inert until a key is set. Every provider
  must return `""` + log on error, never raise into the worker.
- Wire **Celery + Redis**. A task `transcribe_recording(recording_id)`: set
  `processing` → call provider → save `transcript` → set `done` (or `failed` + `error`).
  Enqueue it from the upload endpoint.
- Provide a management command `transcribe_pending` as a no-broker fallback for debugging.
- **Acceptance:** uploading audio results (asynchronously) in a populated
  `transcript` and `status="done"`; a forced provider error yields `status="failed"`
  without crashing.

### Phase E — Transcript → Gemini summary (reuse existing)
- Extend `editor/ai.py` `generate_session_summary(session)` to prefer
  `session.recording.transcript` when present, else fall back to `session.notes` (current
  behavior). Same prompt shape, same `ai_summary` field, **same existing UI**.
- After transcription completes, surface the existing **"Generate AI summary" button**
  once a transcript exists — do NOT auto-generate. The user keeps the summary an explicit,
  button-triggered action (same UX as today); the only change is the button now summarizes
  the transcript when one is present, else the notes.
- **Acceptance:** a completed session with a transcript produces an `ai_summary` rendered
  in the already-styled summary card; the notes-only path still works unchanged.

### Phase F — Deployability hardening + docs (do last)
- Confirm **no hardcoded hosts** anywhere in app code (grep for `localhost`/`meet.jit.si`).
- Wire the `s3` storage branch behind `STORAGE_BACKEND=s3` (django-storages) — leave it
  **off** by default; this is the future "store audio in S3 for auditing" seam.
- Optional Jitsi **JWT auth** (`JITSI_JWT_SECRET`) notes for when the instance is public.
- Update `.env.example`, `requirements.txt`, `README.md`, and `instructions/
  progress-tracker.txt`. Write a short `docker/jitsi/README.md` with bring-up steps and
  the `DOCKER_HOST_ADDRESS` note for LAN.
- **Acceptance:** a fresh clone runs the full flow locally with only `.env` values filled;
  the plan explains exactly which `.env` values change to host it.

---

## 6. New dependencies (add to `requirements.txt`)
- `google-genai` — ALREADY present; reused for Gemini audio transcription (no new dep for
  the active STT path).
- `openai` — add only when the Whisper swap is actually set up later; not needed now.
- `celery` + `redis`.
- `django-storages` + `boto3` (installed but inert until `STORAGE_BACKEND=s3`).

---

## 7. Testing requirements
- **Mock all external calls** (Whisper, Gemini) in tests — CI must pass with no keys and
  no network, exactly like the current summary tests.
- New tests: upload endpoint is participant-only + consent-gated; transcription task sets
  `done`/`failed` correctly (provider mocked); summary prefers transcript over notes.
- Keep the existing 7 tests green.

## 8. Scope fence
- Touch: `editor/` (models, views, urls, templates, ai.py, new transcription.py, tasks,
  templatetags as needed, migrations, tests), `skillbridge_project/settings.py`,
  `requirements.txt`, `.env.example`, `docker/`, `README.md`, `instructions/`.
- **Do not** change credit or rating logic. Do not remove the notes-only summary path.
- One migration for the model changes.

## 9. Known limitations to document (not fix)
- `MediaRecorder` captures each participant's **own** mic per browser; a true merged
  two-speaker transcript would need server-side mixing (Jibri/Jigasi) — explicitly out of
  scope now.
- Same-machine two-tab demo is the supported path; LAN needs `DOCKER_HOST_ADDRESS` + a
  cert for mic access on non-localhost origins.
