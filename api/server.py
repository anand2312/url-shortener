"""A simple URL shortener app, built with FastAPI."""
import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI, HTTPException
from starlette.responses import Response, RedirectResponse
from starlette_discord import DiscordOAuthClient

from api.database import Database
from api.models import ShortURL
from api.utils import authenticate_token, create_short_url, create_user

load_dotenv(find_dotenv())

API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
REDIRECT = API_BASE + "/callback"


app = FastAPI(title="URL Shortener", docs_url=None, redoc_url="/docs")
db = Database(os.environ.get("DB_URI", "sqlite:///data.db"))
discord = DiscordOAuthClient(CLIENT_ID, CLIENT_SECRET, REDIRECT, scopes=("identify",))


@app.on_event("startup")
async def startup() -> None:
    await db.connect()
    await db.initialize_tables()


@app.on_event("shutdown")
async def shutdown() -> None:
    await db.disconnect()


@app.get("/discord")
async def login():
    return discord.redirect()


@app.get("/callback")
async def finish_login(code: str):
    user = await discord.login(code)
    token = await create_user(db, user["id"])
    return {"api-token": token}


@app.post("/urls/new")
async def new_short_url(body: ShortURL) -> Response:
    if not authenticate_token(db, body.token):
        raise HTTPException(status_code=401, detail="Invalid token.")

    short = await create_short_url(db, token=body.token, long=body.long)

    return {"short_url": short}


@app.get("/{short_url}")
async def redirect_elsewhere(short_url: str) -> Response:
    data = await db.fetchrow(
        "SELECT long FROM urls WHERE short = :short", short=short_url
    )

    if not data:
        raise HTTPException(
            status_code=404, detail=f"Requested URL {short_url} was not found."
        )

    return RedirectResponse(url=data["long"])
