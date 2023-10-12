from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import os
import time

def time_func(a: int):
    time_left = a
    timeflush = 0.25
    while time_left > 0:
        # for i in range(time_left):
        #     print("#", end="", flush=True)
        for i in range(0, int(time_left/timeflush)):
            list = ["\\", "|", "/", "—"]
            index = i % 4
            print("\r程序正在运行 {}".format(list[index]), end="")
            time.sleep(timeflush)
        time.sleep(0.5)
        time_left = time_left - 1
    # print("")

app = FastAPI()

@app.on_event("startup")
async def check_sql():
    if os.path.exists("user.db") and os.path.isfile("url.db"):
        print("数据库已存在,正在连接...")
        time_func(2)
        print(" SQL已连接")
    else:
        print("数据库不存在,正在创建...")
        time_func(2)
        conn = sqlite3.connect("user.db")
        conn = sqlite3.connect("url.db")
        print(" SQL创建成功")
        conn.close()

    conn = sqlite3.connect("user.db", check_same_thread=False)
    conn.execute(
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL)"
)
    # cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    # tables = cursor.fetchall()
    # print(f"总共有 {len(tables)} 个表,表名分别为: {tables}")
    conn.close()
    return conn

@app.on_event("shutdown")
def shutdown_event():
    print("程序已关闭")

class User(BaseModel):
    status: str
    username: str
    new_username: str = None
    password: str
    new_password: str = None

conn = sqlite3.connect("user.db", check_same_thread=False)
connurl = sqlite3.connect("url.db", check_same_thread=False)

@app.post("/users/create")
async def create_user(user: User):
    if user.status == "create":
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
            conn.commit()
            return {"message": "User created successfully"}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Username already exists")
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

#curl -X POST -H "Content-Type: application/json" -d '{"status":"delete", "username":"john", "password":"password123"}' http://localhost:8000/users/delete
@app.post("/users/delete")
async def delete_user(user: User):
    if user.status == "delete":
        real_password = conn.execute("SELECT password FROM users WHERE username = ?", (user.username,))
        if user.password == real_password.fetchone()[0]:
            try:
                conn.execute("DELETE FROM users WHERE username = ?", (user.username,))
                conn.commit()
                return {"message": "User deleted successfully"}
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="Username not exists")
        else:
            raise HTTPException(status_code=400, detail="Invalid password")
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

@app.post("/users/update")
async def update_user(user: User):
    if user.status == "update" and user.new_password != None:
        real_password = conn.execute("SELECT password FROM users WHERE username = ?", (user.username,))
        if user.password == real_password.fetchone()[0]:
            try:
                conn.execute("UPDATE users SET password = ? WHERE username = ?", (user.new_password, user.username))
                conn.commit()
                return {"message": "User Password updated successfully"}
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="Username not exists")
        else:
            raise HTTPException(status_code=400, detail="Invalid password")
        
    elif user.status == "update" and user.new_username != None:
        real_password = conn.execute("SELECT password FROM users WHERE username = ?", (user.username,))
        if user.password == real_password.fetchone()[0]:
            try:
                conn.execute("UPDATE users SET username = ? WHERE username = ?", (user.new_username, user.username))
                conn.commit()
                return {"message": "User Password updated successfully"}
            except sqlite3.IntegrityError:
                raise HTTPException(status_code=400, detail="Username not exists")
        else:
            raise HTTPException(status_code=400, detail="Invalid password")
    else:
        raise HTTPException(status_code=400, detail="Invalid status")

@app.post("/login")
async def login(user: User):
    if user.status == "active":
        cursor = conn.execute("SELECT id, username, password FROM users WHERE username = ?", (user.username,))
        row = cursor.fetchone()
        if row and row[2] == user.password:
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    else:
        raise HTTPException(status_code=400, detail="Invalid status")