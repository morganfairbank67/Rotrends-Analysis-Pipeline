import re

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Optional
from datetime import datetime
import uuid

class ScrapedGameData(BaseModel):
    game_id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4(), description="Unique identifier for the game")
    game_name: str = Field(..., description="Name of the game")
    category: str = Field(..., description="Category of the game")
    global_rank: int = Field(None, description="Global rank of the game")
    global_rank_shift_1d: int = Field(None, description="Global rank shift in the last 1 day")
    global_rank_shift_1w: int = Field(None, description="Global rank shift in the last 1 week")
    global_rank_shift_1m: int = Field(None, description="Global rank shift in the last 1 month")
    avg_ccu_rank_7d: int = Field(None, description="Average CCU rank over the last 7 days")
    avg_ccu_rank_14d: int = Field(None, description="Average CCU rank over the last 14 days")
    avg_ccu_rank_shift_1d: int = Field(None, description="Average CCU rank shift in the last day")
    earning_rank: Optional[int] = Field(None, description="Earning rank of the game")
    genre: str = Field(None, description="Genre of the game")
    sub_genre: Optional[str] = Field(None, description="Sub-genre of the game")
    visits: Optional[int] = Field(None, description="Number of visits")
    players_ccu: int = Field(None, description="Current Concurrent Users (CCU)")
    platform_share: float = Field(None, description="Platform share percentage")
    avg_ccu_1d: int = Field(None, description="Average CCU over the last 1 day")
    avg_ccu_7d: int = Field(None, description="Average CCU over the last 7 days")
    avg_ccu_14d: int = Field(None, description="Average CCU over the last 14 days")
    momentum_1d: Optional[str] = Field(None, description="Momentum over the last 1 day")
    momentum_1w: Optional[str] = Field(None, description="Momentum over the last 1 week")
    momentum_1m: Optional[str] = Field(None, description="Momentum over the last 1 month")
    avg_session: str = Field(None, description="Average session duration")
    favorites: int = Field(None, description="Number of favorites")
    rating: float = Field(None, description="Rating of the game")
    up_votes: int = Field(None, description="Number of up votes")
    down_votes: int = Field(None, description="Number of down votes")
    created: datetime = Field(None, description="Creation date of the game")
    extract_date: datetime = Field(None, description="Date when the data was extracted")

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
        'avg_ccu_rank_7d', 'avg_ccu_rank_14d', 'avg_ccu_rank_shift_1m', 'earning_rank', mode='before'
    )
    @classmethod
    def parse_ranks(cls, value: Any) -> Any:
        if value is None: return value
        if isinstance(value, str):
            # Remove commas, plus signs, and hashtags
            val = value.replace(',', '').replace('+', '').replace('#', '').strip()
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