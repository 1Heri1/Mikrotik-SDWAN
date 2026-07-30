from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Msg(BaseModel):
    detail: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
