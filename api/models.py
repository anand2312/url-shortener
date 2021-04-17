from pydantic import BaseModel


class ShortURL(BaseModel):
    long_url: str
    token: str


class LoggedInResponse(BaseModel):
    api_token: str


class SuccessfulShortURLResponse(BaseModel):
    short_url: str
