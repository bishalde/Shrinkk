# Shrinkk revamp: bio pages, link management, analytics, new UI

Date: 2026-09-27 · Status: approved in chat ("u decide and implement")

## Goals
- Modernize the whole UI after the "Shortie" references (bold uppercase display type,
  blue `#1662FF` primary, slate `#3A3F47` dark sections, sidebar dashboard).
- Linktree-style public profile per user at `/@username`.
- Richer link management, account-wide analytics, account settings.
- Deploy on Vercel (Flask as a Python serverless function, MongoDB Atlas).

## Stack decisions
| Concern | Decision |
|---|---|
| Rendering | Flask + Jinja, server-rendered |
| CSS | Tailwind v4 compiled by `@tailwindcss/cli` at build time (Vercel `buildCommand`) |
| Interactivity | Alpine.js, SortableJS, Chart.js (pinned, jsDelivr) |
| Icons | Same-origin SVG sprite built from `lucide-static` + `simple-icons` (only icons used) |
| Uploads | Avatars in MongoDB GridFS, 2 MB max, center-cropped to 400px WebP |
| Geolocation | Vercel `x-vercel-ip-country` / `x-vercel-ip-city` headers |
| Rate limits | Flask-Limiter with MongoDB storage in prod (memory in dev/tests) |
| CSRF | Flask-WTF `CSRFProtect` (forms + `X-CSRFToken` header for fetch) |
| Static | Served from `public/` by Vercel's CDN; Flask serves the same folder locally |

## URL map
`/` landing · `/login` `/signup` `/onboarding` · `/dashboard` (+ `/links`, `/links/<id>`,
`/bio`, `/analytics`, `/settings`) · `/@<username>` public bio page ·
`/@<username>/qr.<png|svg>` · `/qr/<code>.<png|svg>` · `/media/avatar/<id>` · `/<code>` redirect.
App paths are reserved words for aliases and usernames.

## Data model
- `users`: `email`, `password`, `username` (unique, `[a-z0-9_.]{3,30}`), `display_name`,
  `bio` (≤160), `avatar_id`, `socials{}`, `appearance{theme, bg, button_color, button_style,
  radius, font}`, `created_at`.
- `links`: existing fields + `title`, `tags[]`, `is_active`, `on_profile`, `profile_order`,
  `qr{fg,bg}`, `updated_at`. A bio-page button *is* a short link (`on_profile=true`), so
  profile clicks get analytics for free.
- `analytics` (events): `type` (`click`|`profile_view`), `user_id` (owner), `link_id`,
  `source` (`direct`|`bio`|`qr`, from `?src=`), `timestamp`, `country`, `city`, `device`,
  `browser`, `os`, `referrer` (domain). Raw IPs are no longer stored. Bots and owners'
  own profile visits are not counted. `scripts/init_db.py` creates indexes and backfills
  `user_id`/`type` on old events.

## Features
- **Landing**: nav, hero with QR/custom-link cards + phone mock, slanted marquee, working
  "shorten now" (logged-out → signup with URL carried over), 5-step "how we work",
  real cached stats, CTA, footer. No fake logos/reviews/newsletter.
- **Auth**: split layout; username chosen at signup (live availability check);
  `/onboarding` for legacy users without a username; safe `next` redirects.
- **Dashboard home**: KPI tiles (clicks, links, profile views, bio CTR), 7/30/90-day chart,
  quick create, top links.
- **Links**: search, tag filter, active toggle, bulk delete/tag/activate/deactivate,
  create/edit modal (URL, alias, title, tags, expiry, add-to-bio, UTM builder).
- **Link detail**: charts by date/country/device/browser/referrer/source; QR studio
  (colors, PNG/SVG download); edit.
- **Bio editor**: drag-reorder links, add new/existing, profile (avatar/name/bio), socials,
  appearance (6 presets + background, button color/style, radius, font) with live phone preview.
- **Public bio page**: themed, OG/Twitter meta, share + QR, "Made with Shrinkk".
- **Analytics**: account-wide clicks + views over time, top links, country/device/referrer.
- **Settings**: username, email, password (needs current), delete account (type username;
  removes links, events, avatar).

## Out of scope
Dashboard dark mode, profile section headers, custom domains, teams, newsletter.

## Testing
pytest + mongomock (with GridFS integration): model logic, validators, auth flows, link
CRUD/ownership, redirect + event logging, profile rendering, settings, avatar upload.
