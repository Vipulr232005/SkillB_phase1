# Self-hosted Jitsi (docker-jitsi-meet)

Vendored from https://github.com/jitsi/docker-jitsi-meet under `docker/jitsi/`.

## Bring-up (local demo)

```bash
# from docker/jitsi
cp env.example .env          # already done, passwords generated
bash gen-passwords.sh        # regenerates JICOFO/JVB passwords into .env
# edit .env:
#   CONFIG=./jitsi-cfg          (when running from this dir)
#   or absolute: C:/.../docker/jitsi/jitsi-cfg when running from repo root
#   HTTP_PORT=8001              # avoid clash with Django :8000
#   HTTPS_PORT=8443
#   PUBLIC_URL=https://localhost:8443
#   DOCKER_HOST_ADDRESS=127.0.0.1
#   JVB_ADVERTISE_IPS=127.0.0.1

docker compose up -d          # starts web, prosody, jicofo, jvb (4 containers only — no Jigasi/Jibri)
docker compose ps
docker compose logs -f web
```

Then open **https://localhost:8443** (accept self-signed cert) → create a room → join from **two browser tabs** → confirm two-way audio/video.

Core services only: `web`, `prosody`, `jicofo`, `jvb`. No `jigasi`, no `jibri` — audio is captured client-side via `MediaRecorder` (keeps the stack to 4 containers).

## LAN / real host

Change `.env` and the app's `JITSI_BASE_URL`:

- Set `DOCKER_HOST_ADDRESS` and `JVB_ADVERTISE_IPS` to the host's LAN IP (e.g. `192.168.1.10`) — required for LAN; see https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker#running-behind-nat-or-on-a-lan-environment
- Set `PUBLIC_URL=https://meet.yourhost` and expose the same value as `JITSI_BASE_URL` in the Django `.env`
- On non-localhost origins the browser requires **HTTPS** (or `localhost`) for mic access — provide a cert (Let's Encrypt via `ENABLE_LETSENCRYPT=1`) or run behind a reverse proxy.

Moving from local demo to a real host is a `.env` change only — no code change.

## Ports

- `HTTP_PORT=8001` → 8000 in container (redirects to HTTPS)
- `HTTPS_PORT=8443` → 8443 in container (the `JITSI_BASE_URL` default)
- Django still runs on `8000`; no port clash.

## JWT auth (optional, for public host)

- Set `JITSI_APP_ID` + `JITSI_JWT_SECRET` in both `docker/jitsi/.env` and the Django `.env` (`JITSI_JWT_SECRET`). When `JWT` auth is enabled in Jitsi (`ENABLE_JWT_AUTH=1` in prosody config), the app can mint JWTs with `JITSI_APP_ID`/`JITSI_JWT_SECRET` for `external_api.js` (`jwt` option). Leave blank for local demo (no auth).

## Notes

- `jitsi-cfg/` is created on first `up` (volumes `${CONFIG}/web`, `prosody`, `jicofo`, `jvb`). It is gitignored.
- To reset: `docker compose down -v` and delete `jitsi-cfg/`.
- Audio is client-side `MediaRecorder` → no Jigasi/Jibri needed; Jitsi stays at 4 containers.
