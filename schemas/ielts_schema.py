from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

IeltsModule = Literal["reading", "listening", "writing", "speaking"]
IeltsTrack = Literal["academic", "general"]


class IeltsSectionInput(BaseModel):
    module: IeltsModule
    title: str = Field(min_length=2, max_length=160)
    instructions: Optional[str] = ""
    duration_minutes: int = Field(default=30, ge=1, le=180)
    content: Dict[str, Any] = Field(default_factory=dict)
    answer_key: List[str] = Field(default_factory=list)
    order_index: int = Field(default=1, ge=1, le=50)


class IeltsTestCreate(BaseModel):
    title: str = Field(min_length=4, max_length=160)
    description: Optional[str] = ""
    exam_track: IeltsTrack = "academic"
    level: str = Field(default="Band 5-7", max_length=40)
    duration_minutes: int = Field(default=165, ge=30, le=300)
    is_published: bool = False
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    sections: List[IeltsSectionInput] = Field(default_factory=list, min_length=1)

    @field_validator("sections")
    @classmethod
    def ensure_unique_modules(cls, value: List[IeltsSectionInput]) -> List[IeltsSectionInput]:
        seen = set()
        for section in value:
            if section.module in seen:
                raise ValueError("Each module can only appear once per IELTS test")
            seen.add(section.module)
        return value


class IeltsTestUpdate(BaseModel):
    title: str = Field(min_length=4, max_length=160)
    description: Optional[str] = ""
    exam_track: IeltsTrack = "academic"
    level: str = Field(default="Band 5-7", max_length=40)
    duration_minutes: int = Field(default=165, ge=30, le=300)
    is_published: bool = False
    tags: List[str] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    sections: List[IeltsSectionInput] = Field(default_factory=list, min_length=1)


class IeltsSubmissionCreate(BaseModel):
    answers: List[str] = Field(default_factory=list)
    time_spent_seconds: int = Field(default=0, ge=0, le=21600)
    ai_feedback: Dict[str, Any] = Field(default_factory=dict)


class IeltsSubmissionOut(BaseModel):
    id: int
    user_id: int
    test_id: int
    module: IeltsModule
    score: Optional[int] = None
    max_score: Optional[int] = None
    band: Optional[str] = None
    feedback: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class IeltsModuleResult(BaseModel):
    score: Optional[int] = None
    max_score: Optional[int] = None
    band: Optional[str] = None
    feedback: Dict[str, Any] = Field(default_factory=dict)
    submission_id: int


class IeltsOverview(BaseModel):
    published_tests: int
    total_submissions: int
    latest_band: Optional[str] = None
    modules_available: List[IeltsModule]
