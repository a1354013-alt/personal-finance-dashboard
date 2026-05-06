from __future__ import annotations

from fastapi import Query

from models.month import MONTH_PATTERN


def month_query(required: bool = False):
    default = ... if required else None
    return Query(default, pattern=MONTH_PATTERN)
