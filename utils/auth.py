import datetime
import os
import sqlite3
from fastapi import Cookie, Header, Response
from nanoid import generate
import bcrypt
from utils.types import toResponse
import jwt
from pathlib import Path
from dotenv import load_dotenv, set_key

ALGORITHM = "HS256"
DB_DIR = Path("db")
DB_DIR.mkdir(exist_ok=True)
ENV_PATH = DB_DIR / ".env"

def get_or_create_secrets():
    if not ENV_PATH.exists():
        ENV_PATH.touch()

    load_dotenv(ENV_PATH)

    access_secret = os.getenv("ACCESS_SECRET")
    refresh_secret = os.getenv("REFRESH_SECRET")

    if not access_secret or not refresh_secret:
        access_secret = access_secret or generate()
        refresh_secret = refresh_secret or generate()
        
        set_key(str(ENV_PATH), "ACCESS_SECRET", access_secret)
        set_key(str(ENV_PATH), "REFRESH_SECRET", refresh_secret)
        print(f"✨ 密钥已初始化并存入 {ENV_PATH}")
    
    return access_secret, refresh_secret

class Auth:
    def __init__(self):
        self.access_secret, self.refresh_secret = get_or_create_secrets()
        
        self.db_path = 'db/database.db'
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    password TEXT
                )
            ''')
            conn.commit()

    def nouser(self):
        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM user')
        count = cursor.fetchone()[0]
        conn.close()
        return toResponse(True, count == 0)
    
    def register(self, username: str, password: str):
        if not username or not password:
            return toResponse(False, "用户名或密码不能为空")
        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM user')
        count = cursor.fetchone()[0]
        if count > 0:
            return toResponse(False, "用户已存在")
        
        userId = generate()
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with conn:
                conn.execute('''
                    INSERT INTO user (id, username, password) VALUES (?, ?, ?)
                ''', (userId, username, hashed.decode('utf-8')))
            return toResponse(True, userId)
        except sqlite3.Error as e:
            return toResponse(False, str(e))
        finally:
            conn.close()

    def login(self, username: str, password: str, response: Response):
        if not username or not password:
            return toResponse(False, "用户名或密码不能为空")

        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT password FROM user WHERE username = ?
        ''', (username, ))
        row = cursor.fetchone()

        conn.close()
        if not row:
            return toResponse(False, "用户不存在")
        if bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=180)
            data = {
                "username": username,
                "iat": datetime.datetime.now(datetime.timezone.utc),
                "exp": expire
            }
            refresh_token = jwt.encode(data, self.refresh_secret, algorithm=ALGORITHM)
            response.set_cookie(key="musicdl_refresh_token", value=refresh_token, httponly=True, path="/api/refresh")

            data["exp"] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
            access_token = jwt.encode(data, self.access_secret, algorithm=ALGORITHM)
            return toResponse(True, access_token)
        else:
            return toResponse(False, "密码错误")
    
    def check(self, token: str= Header(None)):
        if not token:
            return toResponse(False, "Token 不能为空")
        try:
            jwt.decode(token, self.access_secret, algorithms=[ALGORITHM])
            return toResponse(True, "")
        except jwt.exceptions.ExpiredSignatureError:
            return toResponse(False, "Token 已过期")
        except jwt.exceptions.DecodeError:
            return toResponse(False, "Token 解析错误")
    
    def refresh(self, musicdl_refresh_token: str = Cookie(None)):
        if not musicdl_refresh_token:
            return toResponse(False, "Refresh Token 不能为空")
        try:
            payload=jwt.decode(musicdl_refresh_token, self.refresh_secret, algorithms=[ALGORITHM])
            data={
                "username": payload["username"],
                "iat": datetime.datetime.now(datetime.timezone.utc),
                "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
            }
            access_token = jwt.encode(data, self.access_secret, algorithm=ALGORITHM)
            return toResponse(True, access_token)
        except jwt.exceptions.ExpiredSignatureError:
            return toResponse(False, "Token 已过期")
        except jwt.exceptions.DecodeError:
            return toResponse(False, "Token 解析错误")