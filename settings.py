from datetime import timedelta

# 设置加密
JWT_SECRET_KEY = "asdsavefwdasddas"
# 设置access_token两分钟后过期（过期时间在调试阶段可以长一些，一面接口调试时需要一直获取token）
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=200)
# 设置refresh—_token七天后过期
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)