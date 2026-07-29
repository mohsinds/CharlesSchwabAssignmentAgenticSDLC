"""Minimal brownfield URL shortener seed."""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="URL Shortener Seed", version="0.0.1")
STORE: dict[str, dict[str, Any]] = {}


class ShortenRequest(BaseModel):
    url: HttpUrl


@app.post("/shorten")
def shorten(body: ShortenRequest) -> dict[str, str]:
    code = secrets.token_urlsafe(6)[:6]
    STORE[code] = {"target": str(body.url), "clicks": 0}
    return {"code": code}


@app.get("/{code}")
def redirect(code: str) -> RedirectResponse:
    item = STORE.get(code)
    if not item:
        raise HTTPException(404, "not found")
    item["clicks"] += 1
    return RedirectResponse(item["target"], status_code=302)
