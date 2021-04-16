from pydantic import BaseModel


class ShortURL(BaseModel):
    long: str
    token: str
