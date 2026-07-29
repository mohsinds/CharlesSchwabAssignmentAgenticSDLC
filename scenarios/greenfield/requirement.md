# Greenfield: URL Shortener

Build a URL shortener service from scratch with:

- `POST /shorten` — accept a long URL, return a short code
- `GET /{code}` — 302 redirect to the original URL
- `GET /stats/{code}` — click analytics
- `GET /health` — liveness
- Unit tests and a README

Reliability: handle unknown codes with 404; avoid predictable codes.
