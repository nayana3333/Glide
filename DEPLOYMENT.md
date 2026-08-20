# Deploying Glide

Everything in this repo is ready to deploy — this is the manual click-through you do
once the config files (`render.yaml`, `frontend/vercel.json`) are in place. Creating
accounts and clicking "Deploy" has to be done by you; it's not something that can be
automated on your behalf.

Two services, deployed separately: the **backend** (FastAPI + Postgres) on Render,
the **frontend** (React) on Vercel. Do the backend first — the frontend needs its URL.

## 1. Backend on Render

1. Go to [render.com](https://render.com) and sign up (free tier is enough to try this).
2. **New → Blueprint**, connect your GitHub account, select the `Glide` repo.
3. Render reads [`render.yaml`](render.yaml) automatically and shows two resources to
   create: a `glide-backend` web service and a `glide-db` Postgres database. Click
   **Apply**.
4. Wait for the build. **This step is genuinely slow** — the backend installs Prophet
   and SHAP, which pull in a compiled forecasting library and JIT compiler
   (numba/llvmlite). Expect several minutes on the free tier, and if the build times
   out or runs out of memory, that's why — Render's paid Starter tier gives more
   build resources if you hit this.
5. Once live, copy the backend URL Render gives you, something like
   `https://glide-backend-xxxx.onrender.com`. Confirm it works by opening
   `https://glide-backend-xxxx.onrender.com/docs` — you should see the Swagger UI.

`SECRET_KEY` and `DATABASE_URL` are generated/wired automatically by the blueprint.
Leave `FRONTEND_URL` blank for now — you'll set it in step 3.

## 2. Frontend on Vercel

1. Go to [vercel.com](https://vercel.com) and sign up.
2. **Add New → Project**, import the same `Glide` repo from GitHub.
3. Vercel will ask for the **Root Directory** — set it to `frontend`. It auto-detects
   Vite and reads [`frontend/vercel.json`](frontend/vercel.json) for the rest.
4. Before deploying, add an environment variable:
   `VITE_API_URL` = the Render backend URL from step 1
   (e.g. `https://glide-backend-xxxx.onrender.com`)
5. Click **Deploy**. You'll get a URL like `https://glide-yourname.vercel.app`.

## 3. Connect them (CORS)

Your backend only accepts requests from origins it explicitly trusts. Go back to the
Render dashboard → your `glide-backend` service → **Environment**, and set:

`FRONTEND_URL` = your Vercel URL (e.g. `https://glide-yourname.vercel.app`)

Render will redeploy automatically. Once that finishes, open your Vercel URL, register
an account (with a demo worker ID, 1–200, to seed real data), and confirm the full
app works end to end against the live backend.

## Notes

- **Free-tier sleep**: Render's free web services spin down after inactivity and take
  ~30–60 seconds to wake on the first request. That's normal, not a bug — if you're
  demoing live, open the app a minute before you need it.
- **Free Postgres expiry**: Render's free databases are time-limited (check their
  current terms) — fine for a portfolio demo, not for anything long-running. Upgrade
  the plan if you need it to persist indefinitely.
- **Updating the deployment**: both Render and Vercel auto-redeploy on every push to
  `main` by default — once connected, you don't need to repeat these steps.
