from fastapi import APIRouter, Body, FastAPI, Response
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
    response: Response,
    username: str = Body(""),
    password: str = Body(""),
):
    return auth.login(username, password, response)

app.include_router(api)