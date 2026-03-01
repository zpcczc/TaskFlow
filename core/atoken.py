import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from datetime import datetime
from enum import Enum
import settings
from config.single import SingletonMeta
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


class TokenTypeEnum(Enum):
    ACCESS_TOKEN = 1
    REFRESH_TOKEN = 2


class AuthHandler(metaclass=SingletonMeta):
    security = HTTPBearer()
    secret = settings.JWT_SECRET_KEY

    def _encode_token(self, user_id: int, type: TokenTypeEnum):
        payload = dict(
            iss=str(user_id),  # 用户ID转为字符串
            sub=str(type.value),  # ✅ 关键：Token类型转为字符串
            # iat=datetime.utcnow(),  # 添加签发时间（可选）
        )
        to_encode = payload.copy()
        if type == TokenTypeEnum.ACCESS_TOKEN:
            # 更新过期时间
            to_encode.update({"exp": datetime.utcnow() + settings.JWT_ACCESS_TOKEN_EXPIRES})
        else:
            to_encode.update({"exp": datetime.utcnow() + settings.JWT_REFRESH_TOKEN_EXPIRES})

        return jwt.encode(to_encode, self.secret, algorithm='HS256')

    def encode_login_token(self, user_id: int):
        access_token = self._encode_token(user_id, TokenTypeEnum.ACCESS_TOKEN)
        refresh_token = self._encode_token(user_id, TokenTypeEnum.REFRESH_TOKEN)
        login_token = dict(
            access_token=f"{access_token}",
            refresh_token=f"{refresh_token}"
        )
        return login_token

    def encode_update_token(self, user_id):
        access_token = self._encode_token(user_id, TokenTypeEnum.ACCESS_TOKEN)
        update_token = dict(
            access_token=f"{access_token}"
        )
        return update_token

    def decode_access_token(self, token):
        # ACCESS TOKEN：不可用（过期，或有问题），都用403错误
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            # ✅ 现在 sub 是字符串，比较也要用字符串
            if payload['sub'] != str(TokenTypeEnum.ACCESS_TOKEN.value):
                raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Token类型错误！')
            # 返回时转换为整数
            return int(payload['iss'])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Access Token已过期！')
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='Access Token不可用！')
        except ValueError:
            # 处理 iss 无法转换为整数的情况
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail='无效的用户ID格式！')

    def decode_refresh_token(self, token):
        # REFRESH TOKEN：不可用（过期，或有问题），都用401错误
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            if payload['sub'] != str(TokenTypeEnum.REFRESH_TOKEN.value):
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Token类型错误！')
            return int(payload['iss'])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Refresh Token已过期！')
        except jwt.InvalidTokenError as e:
            print(f"Token解码错误: {e}")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='Refresh Token不可用！')
        except ValueError:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail='无效的用户ID格式！')

    def auth_access_dependency(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_access_token(auth.credentials)

    def auth_refresh_dependency(self, auth: HTTPAuthorizationCredentials = Security(security)):
        return self.decode_refresh_token(auth.credentials)

    # 添加一个辅助方法用于刷新令牌
    def refresh_access_token(self, refresh_token: str):
        """
        使用 refresh token 获取新的 access token
        """
        # 验证 refresh token
        user_id = self.decode_refresh_token(refresh_token)

        # 生成新的 access token
        new_access_token = self._encode_token(user_id, TokenTypeEnum.ACCESS_TOKEN)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": int(settings.JWT_ACCESS_TOKEN_EXPIRES.total_seconds())
        }