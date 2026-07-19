import re

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from typing import Any, Optional
from datetime import datetime
import uuid

from extract import main

class ScrapedGameData(BaseModel):
    game_id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), description="Unique identifier for the game")
    game_name: str = Field(...,alias="Games", description="Name of the game")
    category: str = Field(...,alias="Category", description="Category of the game")
    global_rank: Optional[int] = Field(None,alias="Global Rank", description="Global rank of the game")
    global_rank_shift_1d: Optional[int] = Field(None,alias="Global Rank Shift (1d)", description="Global rank shift in the last 1 day")
    global_rank_shift_1w: Optional[int] = Field(None,alias="Global Rank Shift (1w)", description="Global rank shift in the last 1 week")
    global_rank_shift_1m: Optional[int] = Field(None,alias="Global Rank Shift (1m)", description="Global rank shift in the last 1 month")
    avg_ccu_rank_7d: Optional[int] = Field(None,alias="Avg CCU Rank (7d)", description="Average CCU rank over the last 7 days")
    avg_ccu_rank_14d: Optional[int] = Field(None,alias="Avg CCU Rank (14d)", description="Average CCU rank over the last 14 days")
    avg_ccu_rank_shift_1d: Optional[int] = Field(None,alias="Avg CCU Rank Shift (1d)", description="Average CCU rank shift in the last day")
    earning_rank: Optional[int] = Field(None,alias="Earning Rank", description="Earning rank of the game")
    genre: Optional[str] = Field(None,alias="Genre", description="Genre of the game")
    sub_genre: Optional[str] = Field(None,alias="Sub Genre", description="Sub-genre of the game")
    visits: Optional[int] = Field(None,alias="Visits", description="Number of visits")
    players_ccu: int = Field(None,alias="Players (CCU)", description="Current Concurrent Users (CCU)")
    platform_share: float = Field(None,alias="Platform Share", description="Platform share percentage")
    avg_ccu_1d: Optional[int] = Field(None,alias="Avg CCU (1d)", description="Average CCU over the last 1 day")
    avg_ccu_7d: Optional[int] = Field(None,alias="Avg CCU (7d)", description="Average CCU over the last 7 days")
    avg_ccu_14d: Optional[int] = Field(None,alias="Avg CCU (14d)", description="Average CCU over the last 14 days")
    momentum_1d: Optional[str] = Field(None,alias="Momentum (1d)", description="Momentum over the last 1 day")
    momentum_1w: Optional[str] = Field(None,alias="Momentum (1w)", description="Momentum over the last 1 week")
    momentum_1m: Optional[str] = Field(None,alias="Momentum (1m)", description="Momentum over the last 1 month")
    avg_session: Optional[str] = Field(None,alias="Avg Session", description="Average session duration")
    favorites: Optional[int] = Field(None,alias="Favorites", description="Number of favorites")
    rating: Optional[float] = Field(None,alias="Rating", description="Rating of the game")
    up_votes: Optional[int] = Field(None,alias="Up Votes", description="Number of up votes")
    down_votes: Optional[int] = Field(None,alias="Down Votes", description="Number of down votes")
    created: Optional[datetime] = Field(None,alias="Created", description="Creation date of the game")
    extract_date: datetime = Field(None,alias="Date Extracted", description="Date when the data was extracted")

    @model_validator(mode="before")
    @classmethod
    def change_dashes(cls, values: Any) -> Any:
        if isinstance(values, dict):
            for key, value in values.items():
                if isinstance(value, str):
                    cleaned_val = value.strip()
                    if cleaned_val in ("-", "--", ""):
                        values[key] = None
        return values
    
    @field_validator(
        'global_rank', 'global_rank_shift_1d', 'global_rank_shift_1w', 'global_rank_shift_1m',
        'avg_ccu_rank_7d', 'avg_ccu_rank_14d', 'avg_ccu_rank_shift_1d', 'earning_rank', mode='before'
    )
    @classmethod
    def parse_ranks(cls, value: Any) -> Any:
        if value is None: return value
        if isinstance(value, str):
            # Remove commas, plus signs, and hashtags
            val = value.replace(',', '').replace('+', '').replace('#', '').strip()
            if '\n' in val:
                val = val.split('\n')[0]
            try:
                return int(val)
            except ValueError:
                return None
        return value
    
    @field_validator(
        'visits', 'favorites', 'up_votes', 'down_votes', 'players_ccu', 
        'avg_ccu_1d', 'avg_ccu_7d', 'avg_ccu_14d', mode='before'
    )
    @classmethod
    def parse_large_numbers(cls, value: Any) -> Any:
        if value is None: return value
        if isinstance(value, str):
            val = value.replace(',', '').replace('+', '').strip().upper()
            try:
                if val.endswith('B'): return int(float(val[:-1]) * 1_000_000_000)
                if val.endswith('M'): return int(float(val[:-1]) * 1_000_000)
                if val.endswith('K'): return int(float(val[:-1]) * 1_000)
                return int(float(val))
            except ValueError:
                return None
        return value
    
    @field_validator('platform_share', 'rating', mode='before')
    @classmethod
    def parse_percentages(cls, value: Any) -> Any:
        if value is None: return value
        if isinstance(value, str):
            val = value.replace('%', '').replace('+', '').strip()
            try:
                return float(val) / 100.0 if '%' in value else float(val)
            except ValueError:
                return None
        return value
    
    @field_validator('created', 'extract_date', mode='before')
    @classmethod
    def parse_dates(cls, value: Any) -> Any:
        if value is None: return value
        if isinstance(value, str):
             try:
                 if re.match(r'\d{2}/\d{2}/\d{4}', value):
                     return datetime.strptime(value, "%m/%d/%Y")
             except ValueError:
                 pass
        return value

if __name__ == "__main__":
    print("Running Scraper...")
    raw_data = main()

    successCount = 0
    for row in raw_data:
        try:
            validated = ScrapedGameData(**row)
            successCount += 1
        except ValidationError as e:
            print(f"Validation error: {e}")
    
    print(f"Scraped {len(raw_data)} games, {successCount} games validated.")
