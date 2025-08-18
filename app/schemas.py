from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class Recipe(BaseModel):
    id: Optional[int] = None
    slug: Optional[str] = None
    title: str = Field(..., min_length=3, max_length=120)
    servings: int = Field(ge=1, le=20, default=2)
    time_minutes: int = Field(ge=1, le=480, default=30)
    difficulty: int = Field(ge=1, le=3, description="1=leicht, 2=mittel, 3=aufwendig")
    ingredient_load: int = Field(
        ge=1, le=3, description="1=wenig, 2=mittel, 3=viele Zutaten"
    )
    tags: List[str] = Field(default_factory=list)
    ingredients: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)

    @field_validator("ingredients", "steps")
    def strip_items(cls, v):
        return [s.strip() for s in v if s.strip()]
