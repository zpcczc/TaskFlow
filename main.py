from fastapi import FastAPI
from routers import user,auth
app = FastAPI()
app.include_router(user.router) # 添加路由
app.include_router(auth.router) # 添加路由


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
