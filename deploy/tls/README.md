# TLS deployment

Raptorscope's bearer tokens and credentials travel in the request, so run it
behind HTTPS for anything beyond localhost. `docker-compose.tls.yml` adds an
nginx reverse proxy that terminates TLS in front of the `web` service.

## Certificate

**Testing** — generate a self-signed cert (also available as `make certs`):

```sh
mkdir -p deploy/tls/certs
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout deploy/tls/certs/raptorscope.key \
  -out    deploy/tls/certs/raptorscope.crt \
  -subj "/CN=raptorscope.local"
```

**Production** — drop a real certificate + key at
`deploy/tls/certs/raptorscope.{crt,key}` (Let's Encrypt / your CA). The `certs/`
directory is gitignored so keys are never committed.

## Run

```sh
docker compose -f docker-compose.yml -f docker-compose.tls.yml \
  --profile app --profile tls up
```

The SPA is then served on `https://<host>/` and the API under `https://<host>/api`.
HTTP (:80) redirects to HTTPS; HSTS and related security headers are set, and AI
SSE streams pass through unbuffered.
