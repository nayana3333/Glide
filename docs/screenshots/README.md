# Screenshots needed here

The main README references the files below. I couldn't capture these myself — the
browser tooling in my environment can't composite/render frames to take a real
screenshot, so rather than fake one, here's exactly what to capture instead.

## How (takes about 5 minutes)

1. Start the backend: `cd backend && python -m uvicorn app.main:app --reload --port 8000`
2. Start the frontend: `cd frontend && npm run dev`
3. Open `http://localhost:5174`, register with a **demo worker ID** between 1 and
   200 (seeds real earnings history so pages aren't empty)
4. Resize your browser to a normal desktop width (~1440px) for consistent framing
5. Screenshot each page below and save with the exact filename listed
6. For dark mode, toggle the moon/sun icon in the navbar before capturing `dashboard-dark.png`

| Filename | Page | What to show |
|---|---|---|
| `login.png` | `/login` | The register tab, with the worker-type/platform selects visible |
| `dashboard.png` | `/dashboard` | Buffer balance, next-week forecast badge, and the earnings chart all visible |
| `forecast.png` | `/forecast` | The confidence-band chart plus the SHAP explanation panel below it |
| `buffer.png` | `/buffer` | Balance, deposit/withdraw form, and a few rows of transaction history |
| `insights.png` | `/insights` | Financial health score and the monthly trend chart |
| `mobile-nav.png` | any page, mobile width (375px) | The hamburger menu open, showing the drawer |
| `dashboard-dark.png` | `/dashboard` | Same as dashboard.png but in dark mode |

## Demo GIF / video (optional but recommended)

A 15–30 second screen recording clicking through register → dashboard → forecast →
buffer beats any number of static screenshots. On Windows, `Win+G` (Xbox Game Bar)
or the free [ScreenToGif](https://www.screentogif.com/) tool both work well.

- Save as `demo.gif` in this folder if under ~10MB (GitHub renders GIFs inline in
  the README automatically)
- For a full video, drag-and-drop the `.mp4` directly into a GitHub PR/issue/README
  edit box on github.com — GitHub hosts it and gives you an embeddable link that
  renders as a playable video, which you can then paste into `README.md`

Once these exist, the broken-image icons in the main README will resolve on their own —
nothing else needs to change.
