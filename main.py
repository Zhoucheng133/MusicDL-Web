from fastapi import APIRouter, Body, FastAPI, Response, Depends
from utils.auth import Auth

app=FastAPI()
api=APIRouter(prefix="/api")
auth=Auth()

@api.get("/test")
def read_root(check=Depends(auth.check)):
    if not check.get("ok"):
        return check
    return {"Hello": "World"}

@api.get("/refresh")
def refresh(check=Depends(auth.refresh)):
    return check

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