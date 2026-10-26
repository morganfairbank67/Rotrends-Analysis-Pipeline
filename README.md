# Rotrends-Analysis-Pipeline
Using data form Rotrends to find current trends or a sub-genre with more players than the available games can handle

### Environment Setup:
```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  #Mac

# Install Python packages
pip install -r requirements.txt
```

### Install Playwright browsers
```bash
playwright install
```

### Run the pipeline
```bash
python -m Scraper.validate
```
Scrapes Rotrends, validates each row with Pydantic and upserts the result into Supabase. Needs `SUPABASE_URL`, `SUPABASE_KEY` and the Rotrends login in `.env`.

### Dashboard
Streamlit app that reads from Supabase and answers where player demand outstrips the games serving it.

```bash
streamlit run streamlit_app.py
```

| Page | Question it answers |
|---|---|
| Start here | Headline findings in plain English and a guide to the other pages |
| Market overview | Which genres hold more players than their number of games? |
| Market gaps | Which genres or sub-genres are under-served, and can newcomers break in? |
| Title keywords | Which words and patterns in game names, like "steal a", have players to spare? |
| Engagement | Do players stick, who is surging, who earns well, what do game types look like? |
| Trends | What changed since the last weekly snapshot? Needs two or more snapshots. |

Games that appear in more than one Rotrends list are collapsed to one row, and games are matched between weeks by cleaned title plus release date so renamed update titles still line up.

**Fair-share multiple** is a group's share of players divided by its share of games. 1x is fair, above 1x is under-served. The ranking also checks the typical game in the group so one giant hit cannot make a crowded niche look empty (shown as hit-driven).

The supply side is only the games in the scraped top lists, so a high score means under-served among top games, not across all of Roblox.

### Weekly scrape
Rotrends blocks the scraper when the browser runs headless, so the weekly run happens on a Mac with a visible browser window.

```bash
./scripts/install_schedule.sh
```

This installs a macOS launchd job that runs `python -m Scraper.validate` every Monday at 09:00 and appends output to `logs/scrape.log`. If the Mac is asleep at that time the job runs when it wakes. Remove it with `./scripts/install_schedule.sh uninstall`.

`.github/workflows/scrape.yml` is kept as a manual trigger only, for use if Rotrends ever allows headless access.

### Docker
```bash
docker compose up --build
```
Opens on http://localhost:8501. Credentials are read from `.env` at runtime and are never copied into the image.

### Tests and lint
```bash
pip install -r requirements-dev.txt
pytest
ruff check Analytics Dashboard tests streamlit_app.py
```
GitHub Actions runs both, plus a Docker build, on every push and pull request.
