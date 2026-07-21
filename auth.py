import httpx

import logger_conf as logger

log = logger.log

access_token = None
refresh_token = None
_api_base = None

async def login(app_key, app_secret, api_base):
    global access_token, refresh_token, _api_base
    _api_base = str(api_base).rstrip("/")
    log.info("开始登录大模型服务平台 api_base=%s ak=%s", _api_base, logger.mask(app_key))
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{_api_base}/token/auth/login",
            json={"appKey": app_key, "appSecret": app_secret},
        )
        log.debug("登录响应 status=%s", r.status_code)
        r.raise_for_status()
        data = r.json()
    code = data.get("code")
    if code not in (0, None):
        log.error("登录失败: %s (code=%s)", data.get("msg"), code)
        raise Exception(f"登录失败: {data.get('msg')} (code={code})")
    d = data.get("data") or {}
    access_token = d.get("accessToken")
    refresh_token = d.get("refreshToken")
    if not access_token:
        log.error("登录返回中缺少 accessToken")
        raise Exception("登录返回中缺少 accessToken")
    log.info("登录成功 accessToken=%s", logger.mask(access_token))
    return data

async def refresh():
    global access_token
    if not refresh_token:
        log.warning("无 refreshToken, 跳过刷新")
        return
    log.info("刷新 token ...")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{_api_base}/token/auth/refresh",
            json={"refreshToken": refresh_token},
        )
        r.raise_for_status()
        data = r.json()
    d = data.get("data") or {}
    if d.get("accessToken"):
        access_token = d.get("accessToken")
        log.info("token 刷新成功 accessToken=%s", logger.mask(access_token))
    else:
        log.warning("刷新返回中无新 accessToken")

async def logout():
    global access_token
    if not access_token:
        return
    log.info("退出登录 ...")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            await c.post(
                f"{_api_base}/token/auth/logout",
                json={"accessToken": access_token},
            )
        log.info("已退出登录")
    except Exception as e:
        log.warning("退出登录异常: %s", e)

def get_token():
    return access_token
