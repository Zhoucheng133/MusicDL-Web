from fastapi import APIRouter, Body, FastAPI
from utils.auth import Auth

app=FastAPI()
api=APIRouter(prefix="/api")
auth=Auth()

@api.get("/test")
def read_root():
    return {"Hello": "World"}

@api.post("/register")
def register(
    username: str = Body(""),
    password: str = Body("")
):
    return auth.register(username, password)

@api.post("/login")
def login(
    username: str = Body(""),
    password: str = Body("")
):
    return auth.login(username, password)

app.include_router(api)