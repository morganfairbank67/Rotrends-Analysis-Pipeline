### Goal:
An automated data and machine learning pipeline to identify market gaps within Roblox.
### Achieve this through:
- Continously scraping data from rotrends by monitering high-performing games
- Validating the extracted data with Pydantic
- Store data into a PostgreSQL database (Supabase)
- Using game descriptions to generate embeddings through Sentence-Transformers
    - Clustering(K-Means): grouping games into mechanical sub-genres
    - Scoring: Calculating an opportunity score (Total CCU / Number of Competing games)
- Presenting said data on dashboard using Streamlit to visualise historical trends and market saturation on interactive charts
- Notifications on summaries: Using something like a discord webhook to automatically push summaries to a private server