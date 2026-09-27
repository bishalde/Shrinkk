# Shrinkk

Short links, QR codes and a link-in-bio page, with click and profile analytics.

Live at **https://shrinkk.vercel.app**

- **Short links**: custom aliases, tags, expiry, pause/resume, bulk actions, UTM builder.
- **Bio page** at `/@username`: avatar, bio, social icons, drag-to-reorder buttons, six themes plus custom colours, fonts and button styles.
- **Analytics**: clicks and profile views over time, countries, devices, browsers, referrers and traffic source (direct / bio / QR).
- **QR codes** for every link and bio page, PNG or SVG, with custom colours.

Stack: Flask 3, MongoDB (GridFS for avatars), Jinja + Tailwind v4 + Alpine.js, deployed on Vercel.

## Quick start (no database needed)

```bash
uv venv && uv pip install -r requirements-dev.txt   # or: python -m venv .venv && pip install -r requirements-dev.txt
npm install && npm run build                        # builds CSS and the icon sprite
.venv/bin/python scripts/demo.py                    # http://localhost:8080
```

The demo runs on an in-memory database seeded with sample data. Log in as `demo@shrinkk.app` / `demo12345` (Bishal's account). Sample bio pages: `/@bishal`, `/@sima`, `/@basak`. Data is lost when the server stops.

## Running against MongoDB

```bash
cp .env.example .env             # set MONGO_URI (local or Atlas) and SECRET_KEY
.venv/bin/python scripts/init_db.py   # creates indexes, migrates events from older versions
.venv/bin/flask --app app run --debug --port 8080
npm run dev:css                  # optional: rebuild CSS on template changes
```

Users created before the revamp have no username; they're asked to pick one on their next login.

## Environment variables

| Variable     | Default                     | Notes                                          |
|--------------|-----------------------------|------------------------------------------------|
| `MONGO_URI`  | `mongodb://localhost:27017` | `mongomock://` gives an in-memory database     |
| `MONGO_DB`   | `shrinkk`                   |                                                |
| `SECRET_KEY` | dev placeholder             | **Required** in production; the app refuses to start without it |
| `BASE_URL`   | `http://localhost:8080`     | Public origin used in short links and QR codes. On Vercel it falls back to the production domain |

## Deploying to Vercel

1. Import the repo in Vercel. `vercel.json` already sets the build command (`npm run build`), serves `public/` from the CDN and routes everything else to the Flask function in `api/index.py`.
2. Add `MONGO_URI`, `MONGO_DB` and `SECRET_KEY` in Project → Settings → Environment Variables. Set `BASE_URL=https://shrinkk.vercel.app` (or your custom domain); if omitted, Vercel's production domain is used.
3. In MongoDB Atlas, allow access from Vercel (Network Access → `0.0.0.0/0`, or Vercel's static IPs on paid plans).
4. Run `scripts/init_db.py` once against the production database.

Visitor country and city come from Vercel's geo headers, so they're empty when running locally.

## Docker

```bash
docker build -t shrinkk . && docker run -p 8080:8080 --env-file .env shrinkk
```

## Tests

```bash
.venv/bin/python -m pytest
```

Tests use mongomock, so no database is required.
