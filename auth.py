import httpx

access_token = None
refresh_token = None
_api_base = None

async def login(app_key, app_secret, api_base):
    global access_token, refresh_token, _api_base
    _api_base = str(api_base).rstrip("/")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(
            f"{_api_base}/token/auth/login",
            json={"appKey": app_key, "appSecret": app_secret},
        )
        r.raise_for_status()
        data = r.json()
    code = data.get("code")
    if code not in (0, None):
        raise Exception(f"登录失败: {data.get('msg')} (code={code})")
    d = data.get("data") or {}
    access_token = d.get("accessToken")
    refresh_token = d.get("refreshToken")
    if not access_token:
        raise Exception("登录返回中缺少 accessToken")
    return data

async def refresh():
    global access_token
    if not refresh_token:
        return
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

async def logout():
    global access_token
    if not access_token:
        return
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            await c.post(
                f"{_api_base}/token/auth/logout",
                json={"accessToken": access_token},
            )
    except Exception:
        pass

def get_token():
    return access_token
