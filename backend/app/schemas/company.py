from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    description: str | None = None


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: AnyHttpUrl | None = None
    description: str | None = None


class CompanyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    website: AnyHttpUrl | None
    description: str | None
    created_at: datetime
    updated_at: datetime
