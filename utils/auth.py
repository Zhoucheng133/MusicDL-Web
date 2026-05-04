import datetime
import sqlite3
from nanoid import generate
import bcrypt
from utils.types import toResponse
import jwt

ALGORITHM = "HS256"

class Auth:
    def __init__(self):
        self.jwt_secret = generate()
        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                id TEXT PRIMARY KEY,
                username TEXT,
                password TEXT
            )
        ''')
    
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

    def login(self, username: str, password: str):
        if not username or not password:
            return toResponse(False, "用户名或密码不能为空")

        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT password FROM user WHERE username = ?
        ''', (username, ))

        row = cursor.fetchone()
        if not row:
            return toResponse(False, "用户不存在")
        if bcrypt.checkpw(password.encode('utf-8'), row[0].encode('utf-8')):
            expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)
            data = {
                "username": username,
                "exp": expire
            }
            encoded_jwt = jwt.encode(data, self.jwt_secret, algorithm=ALGORITHM)
            return toResponse(True, encoded_jwt)
        else:
            return toResponse(False, "密码错误")