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

| Page | What it shows |
|---|---|
| Overview | Players vs games by genre, treemap of where players are, biggest games |
| Title keywords | Common words and phrases in game names, with demand vs supply scoring (e.g. "steal a") and whether title tags and emoji matter |
| Market gaps | Opportunity ranking per genre or sub-genre, whether newcomers can break in, genre heatmap, release age cohorts |
| Engagement | Session length, like ratio, momentum, monetisation vs player rank, K-Means archetypes, correlations |

Games that appear in more than one Rotrends list are collapsed to one row before any analysis.

**Opportunity score** is the geometric mean of the demand index (share of players divided by share of games) and the typical index (median game in the segment vs the overall median), so one giant hit cannot make a crowded niche look empty.

The supply side is only the games in the scraped top lists, so a high score means under-served among top games, not across all of Roblox.

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
