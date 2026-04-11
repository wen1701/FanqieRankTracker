# 🏆 Fanqie Rank Tracker

[![中文](https://img.shields.io/badge/lang-中文-red)](README.md)

> Daily automated tracking of Fanqie Novel's new book rankings with AI-powered trend analysis, deployed as a premium online dashboard.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🕷️ Auto Scraping | Daily automated scraping of Fanqie Novel's Top 30 new books across all categories |
| 📊 Trend Analysis | Automatic day-over-day comparison: new entries / dropped / rank changes / readership growth |
| 🤖 AI Summary | OpenAI-compatible API integration for per-category market trend analysis |
| 🖥️ Dashboard | Dark editorial-style dashboard with typewriter animation and waterfall book cards |
| 📱 Responsive | Full mobile support with slide-out sidebar menu |
| ⚡ Fully Automated | GitHub Actions + GitHub Pages, zero server maintenance |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Git**
- A GitHub account
- (Optional) An OpenAI-compatible API key for AI analysis

### Step 1: Fork the Repository

Click the **Fork** button on the top-right corner of the GitHub page to fork this repository to your own account.

### Step 2: Enable GitHub Pages

1. Go to your forked repo → **Settings** → **Pages**
2. Under Source, select **Deploy from a branch**
3. Select `main` branch and `/ (root)` directory
4. Click **Save**

After a few minutes, your dashboard will be live at: `https://<your-username>.github.io/FanqieRankTracker/`

### Step 3: Configure Secrets (Optional, for AI Analysis)

Go to repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**, and add the following three secrets:

| Secret Name | Description | Example |
|---|---|---|
| `API_BASE_URL` | OpenAI-compatible API endpoint | `https://api.openai.com/v1` |
| `API_KEY` | API key | `sk-xxxxxxxxxxxxx` |
| `API_MODEL` | Model name | `gpt-4o-mini` |

> **💡 Tip:** Any OpenAI-compatible API works (e.g., Moonshot / DeepSeek / self-hosted endpoints). If these secrets are not configured, the system will automatically fall back to rule-based summaries — **core functionality is unaffected**.

### Step 4: Trigger the First Run Manually

1. Go to repo → **Actions** → Select **Daily Fanqie Rank Scraper** on the left
2. Click **Run workflow** → **Run workflow** on the top-right
3. Wait for the workflow to complete (~3–5 minutes)

After a successful run, data files will be generated in the `data/` directory. Open the GitHub Pages link to view your dashboard.

### Step 5: Sit Back and Relax

GitHub Actions is configured to run automatically at **UTC 00:00 (08:00 Beijing Time)** every day. No further manual action is needed — data and dashboard will auto-update daily.

---

## 🔧 Local Development

```bash
# 1. Clone the repo
git clone https://github.com/<your-username>/FanqieRankTracker.git
cd FanqieRankTracker

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Run the scraper (Top 30 per category)
python scrape_fanqie_ranks.py

# 5. Build dashboard data (optional, set env vars for AI analysis)
pip install openai
export API_BASE_URL="https://your-api-endpoint/v1"
export API_KEY="your-api-key"
export API_MODEL="your-model-name"
python scripts/build_latest.py

# 6. Preview frontend locally
python -m http.server 8000
# Then open http://localhost:8000
```

---

## 📁 Project Structure

```
FanqieRankTracker/
├── .github/workflows/
│   └── scrape.yml              # GitHub Actions automation workflow
├── css/
│   └── style.css               # Dark editorial theme styles
├── js/
│   └── app.js                  # Frontend rendering (waterfall + typewriter animation)
├── scripts/
│   └── build_latest.py         # Trend comparison + AI analysis build script
├── data/
│   ├── fanqie_female_new_ranks_YYYYMMDD.json  # Daily raw snapshots
│   ├── latest_ranks.json       # Latest aggregated data (dashboard source)
│   └── trends/
│       └── YYYY-MM-DD.json     # Trend archives
├── index.html                  # Dashboard entry page
├── scrape_fanqie_ranks.py      # Fanqie Novel scraper (Playwright)
├── requirements.txt            # Python dependencies
└── README.md                   # Chinese documentation
```

---

## ⚙️ How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                GitHub Actions (Daily at 08:00 CST)          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Playwright   │───▶│  build_latest │───▶│  git commit  │  │
│  │  Scrape rank  │    │  Trend diff   │    │  Auto push   │  │
│  │  data         │    │  + AI summary │    │  to main     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                                                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    GitHub Pages auto-deploy
                    User visits dashboard 🌐
```

---

## 📝 FAQ

<details>
<summary><b>Q: What if the workflow fails?</b></summary>

Check the error message in the Actions log. Common causes:
- Fanqie Novel page structure changed → Update the scraper selectors
- Playwright installation timeout → Try re-running the workflow

</details>

<details>
<summary><b>Q: Can I use it without configuring AI secrets?</b></summary>

Yes! The system will automatically fall back to rule-based summaries (e.g., "3 new entries; Book X rose +5 ranks"). You just won't have the AI natural language analysis.

</details>

<details>
<summary><b>Q: Can I track other rankings (e.g., male-oriented)?</b></summary>

Yes, modify the `init_url` variable in `scrape_fanqie_ranks.py` to point to the desired ranking page URL.

</details>

---

## 📜 License

MIT

---

<p align="center">
  <sub>Made with ☕ and 🤖 — Data updates daily via automation, zero manual maintenance required</sub>
</p>
