from datetime import datetime, timezone
from fastapi import FastAPI, Body, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String
from pydantic import HttpUrl
from asyncpg.exceptions import UniqueViolationError
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy
import databases
import psycopg2
import hashlib
import base64
import os


# DATABASE_URL = os.environ.get("DATABASE_URL")
DATABASE_URL = "postgresql://user:password@localhost:5432/db_name"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()


url_db = sqlalchemy.Table(
    "urls",
    metadata,
    sqlalchemy.Column("id", Integer, primary_key=True),
    sqlalchemy.Column("original_url", String),
    sqlalchemy.Column("short_link", String, unique=True, index=True),
)

engine = sqlalchemy.create_engine(DATABASE_URL)

metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


def create_short_link(original_url: str, timestamp: float):
    to_encode = f"{original_url}{timestamp}"

    b64_encoded_str = base64.urlsafe_b64encode(
        hashlib.sha256(to_encode.encode()).digest()
    ).decode()
    return b64_encoded_str[:7]


@app.post("/shorten")
async def shorten_url(url: HttpUrl = Body(..., embed=True)) -> None:
    timestamp = datetime.now().replace(tzinfo=timezone.utc).timestamp()
    shortened = create_short_link(url, timestamp)
    query = url_db.insert().values(original_url=url, short_link=shortened)
    try:
        await database.execute(query)
    except UniqueViolationError:
        pass
    return {"shortened_url": shortened}


@app.get("/{shortened}")
async def redirect(shortened: str) -> None:
    """
    shortened: Takes shortened as a param and redirects it.
    """
    query = url_db.select().where(url_db.c.short_link == shortened)
    url = await database.fetch_one(query)
    if url is None:
        raise HTTPException(status_code=404, detail="Link does not exist")
    return RedirectResponse(url=url["original_url"])

@app.get("/")
async def redirect_docs():
    return RedirectResponse("/docs")@app.get("/")
