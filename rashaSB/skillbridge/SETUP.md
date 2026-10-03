# Running Skill Bridge on a new machine

This project can run in two tiers. **Tier 1** gets the whole app working (profiles,
discovery, recommendations, sessions, AI summaries). **Tier 2** adds the self-hosted
Jitsi video room and audio transcription.

## What the project uses
- **Python 3.10+**, Django 6, **SQLite** (no database server to install).
- **Gemini API key** — powers AI summaries *and* transcription.
- **Docker** — only if you want the self-hosted video room + recording.
- **Redis** — only if you want real async transcription (there is a no-Redis fallback).

## Prerequisites to install
1. **Git** — to clone the repo.
2. **Python 3.10 or newer** — from python.org (tick "Add Python to PATH" on Windows).
3. *(Tier 2 only)* **Docker Desktop** — for the Jitsi containers.

---

## Tier 1 — Core app (no video)

**1. Clone and enter the project**
```
git clone https://github.com/Vipulr232005/SkillB_phase1.git
cd SkillB_phase1/rashaSB/skillbridge
```

**2. Create a virtual environment and install dependencies**

Windows (PowerShell):
```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS / Linux:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Create your `.env`** (copy the template, then fill it in)
```
cp .env.example .env     # Windows: copy .env.example .env
```
For Tier 1 the only value that matters is:
```
GEMINI_API_KEY=your_key_from_aistudio.google.com/apikey
```
> Do not put inline `# comments` on the same line as a value — put comments on their
> own line. Without `GEMINI_API_KEY` the app still runs; only AI summaries are skipped.

**4. Set up the database**
```
python manage.py migrate
```

**5. (Recommended) Load demo teachers so Discover isn't empty**
```
python manage.py seed_demo
```
This creates 16 demo teachers across many fields. They all share the password
`skillbridge123`. Re-run with `--fresh` to reset them.

**6. (Optional) Create your own admin account**
```
python manage.py createsuperuser
```

**7. Run it**
```
python manage.py runserver
```
Open http://localhost:8000/. Sign up with email, or log in as a demo teacher
(e.g. `sofia_romero` / `skillbridge123`).

That is the whole app working. AI summaries work from typed session notes.

---

## Tier 2 — Add the video room + transcription

Do Tier 1 first, then:

**1. Start the self-hosted Jitsi** (Docker must be running). One-time setup inside
`docker/jitsi/` — follow `docker/jitsi/README.md` (generate its passwords, set
`DOCKER_HOST_ADDRESS`), then:
```
docker compose -f docker/jitsi/docker-compose.yml up -d
```

**2. Trust the certificate once.** Open https://localhost:8443 in your browser and
click through the "not secure" warning. The embedded room will not load (and the mic
will not work) until you do this.

**3. Point the app at it** — in `.env`:
```
JITSI_BASE_URL=https://localhost:8443
```

**4. Choose how transcription runs** — in `.env`, pick one:
- Simplest (no Redis):
  ```
  CELERY_TASK_ALWAYS_EAGER=true
  ```
  Transcription runs inline right after an upload.
- Real async (needs Redis + a worker): leave the line above blank, start Redis
  (`docker compose up -d` from the project root), and in a separate terminal run:
  ```
  celery -A skillbridge_project worker -l info
  ```

**5. Restart `runserver`**, then test: accept a session -> Join room -> consent ->
record -> stop -> mark complete -> the transcript appears on Sessions.

> Demo tip: run both participants as two tabs on the same machine (two different
> logins). That avoids cross-device certificate and networking hassle.

---

## Optional extras (all safe to skip)

| Feature | What you need | If skipped |
|---|---|---|
| Google / GitHub login | OAuth keys in `.env` (callback URLs are in `.env.example`) | Email signup still works; social buttons just error |
| Password-reset emails | `RESEND_API_KEY` | Emails print to the server console instead |
| Audio storage in S3 | `STORAGE_BACKEND=s3` + AWS keys | Audio saves to a local `media/` folder |
| OpenAI Whisper instead of Gemini | `OPENAI_API_KEY` + `STT_PROVIDER=openai_whisper` | Gemini handles transcription |

## Quick troubleshooting
- **`ModuleNotFoundError`** -> your venv isn't activated, or
  `pip install -r requirements.txt` didn't finish.
- **Jitsi room shows "could not load"** -> you haven't trusted the cert at
  https://localhost:8443, or `JITSI_BASE_URL` has a stray inline comment.
- **Discover is empty** -> run `python manage.py seed_demo`.
- **Confirm it's healthy** -> `python manage.py test editor` should report 19 tests OK.
