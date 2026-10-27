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

| Page | Contents |
|---|---|
| Overview | Headline signals, player share vs game share by genre, treemap, largest games |
| Market gaps | Fair-share ranking, entry openness, genre map and release-age mix |
| Title keywords | Phrase frequency, demand relative to supply, per-phrase detail, title features |
| Engagement | Retention, momentum, monetisation, game segments and drivers |
| Trends | Change between weekly snapshots. Needs two or more snapshots. |

The theme follows the system setting and can be switched to light or dark from the menu in the top right.

Games that appear in more than one Rotrends list are collapsed to one row, and games are matched between weeks by cleaned title plus release date so renamed update titles still line up.

**Fair-share multiple** is a group's share of players divided by its share of games. 1x is fair, above 1x is under-served. The ranking also checks the typical game in the group so one giant hit cannot make a crowded niche look empty (shown as hit-driven).

The supply side is only the games in the scraped top lists, so a high score means under-served among top games, not across all of Roblox.

### Weekly scrape
`.github/workflows/scrape.yml` runs every Monday at 06:00 UTC and can also be started from the Actions tab. It scrapes the Rotrends lists headless, validates the rows and upserts them into Supabase.

Add two repository secrets under Settings, Secrets and variables, Actions: `SUPABASE_URL` and `SUPABASE_KEY`.

Locally the browser window stays visible unless `HEADLESS=true` is set. `scripts/install_schedule.sh` installs an equivalent macOS launchd job for running the scrape on a Mac instead.

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
