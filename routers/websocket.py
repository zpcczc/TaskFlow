from fastapi import APIRouter, Query
from starlette.websockets import WebSocket, WebSocketDisconnect
from WebSocket.manager import manager
from core.atoken import AuthHandler


router = APIRouter()

auth_handler = AuthHandler()

@router.websocket("/ws/notifications")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(...),
):
    # 1.验证token 获取用户id
    try:
        user_id = auth_handler.decode_access_token(token)
    except Exception:
        await websocket.close(code=1008)
        return
    # 2.连接管理器注册
    await manager.connect(user_id,websocket)
    try:
        # 3.保持连接，接收客户端消息
        while True:
            await websocket.receive_text()  # 可以接受消息，保持简单连接
    except WebSocketDisconnect:
        # 4.客户端断开连接时清理
        manager.disconnect(user_id)
