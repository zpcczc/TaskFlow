from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routers import user, auth, task, websocket, notifications

# 创建 FastAPI 应用实例
app = FastAPI(title="TaskFlow API")

# 获取当前文件所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 添加 CORS 中间件（必须放在所有路由之前）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 生产环境请替换为具体前端域名
    allow_credentials=True,
    allow_methods=["*"],           # 允许所有方法，包括 OPTIONS
    allow_headers=["*"],           # 允许所有请求头
)

# 包含 API 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/users", tags=["users"])
app.include_router(task.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(websocket.router)

# 挂载静态文件（使用绝对路径）
frontend_dir = os.path.join(BASE_DIR, "frontend")
# 调试，没问题可注释
if os.path.isdir(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
else:
    print("警告：frontend 目录不存在，请创建并放入前端文件")


@app.get("/health")
async def health():
    return {"status": "ok"}

