from datetime import timedelta

# 设置加密
JWT_SECRET_KEY = "asdsavefwdasddas"
# 设置access_token两分钟后过期
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=200)
# 设置refresh—_token七天后过期
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)