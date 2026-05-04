import datetime
import sqlite3
from fastapi import Response
from nanoid import generate
import bcrypt
from utils.types import toResponse
import jwt

ALGORITHM = "HS256"

class Auth:
    def __init__(self):
        self.refresh_secret = generate()
        self.access_secret = generate()
        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id TEXT PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        ''')
        conn.close()
    
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
                "exp": expire
            }
            refresh_token = jwt.encode(data, self.refresh_secret, algorithm=ALGORITHM)
            response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, path="/api/refresh")

            data["exp"] = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30)
            access_token = jwt.encode(data, self.access_secret, algorithm=ALGORITHM)
            return toResponse(True, access_token)
        else:
            return toResponse(False, "密码错误")
    
    def check(self, token: str):
        try:
            data = jwt.decode(token, self.access_secret, algorithms=[ALGORITHM])
            return toResponse(True, "")
        except jwt.exceptions.DecodeError:
            return toResponse(False, "Token 解析错误")
        except jwt.exceptions.ExpiredSignatureError:
            return toResponse(False, "Token 已过期")