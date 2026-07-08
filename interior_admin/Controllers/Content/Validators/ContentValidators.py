from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BlogCreateSchema(BaseValidator):
    title: str
    author: Optional[str] = Field(default='')
    slug: Optional[str] = Field(default=None)
    body: Optional[str] = Field(default='')          # rich-text HTML from the editor
    coverImageUrl: Optional[str] = Field(default='')
    authorImageUrl: Optional[str] = Field(default='')
    metaTitle: Optional[str] = Field(default='')
    metaDescription: Optional[str] = Field(default='')
    focusKeyword: Optional[str] = Field(default='')
    status: Optional[str] = Field(default='draft')
    featuredOrder: Optional[int] = Field(default=None)
    isFeatured: Optional[bool] = Field(default=None)


class BlogUpdateSchema(BaseValidator):
    title: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    slug: Optional[str] = Field(default=None)
    body: Optional[str] = Field(default=None)
    coverImageUrl: Optional[str] = Field(default=None)
    authorImageUrl: Optional[str] = Field(default=None)
    metaTitle: Optional[str] = Field(default=None)
    metaDescription: Optional[str] = Field(default=None)
    focusKeyword: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    featuredOrder: Optional[int] = Field(default=None)
    isFeatured: Optional[bool] = Field(default=None)
