import secrets
import httpx
from urllib.parse import urlencode

from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from fastapi import APIRouter, Depends, HTTPException, Request, status, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.ycode.schemas.auth import UserRegistrationSchema, UserLoginSchema
from src.ycode.db.session import get_async_session
from src.ycode.core.config import settings
from src.ycode.core.security import get_password_hash, verify_password, verify_token
from src.ycode.core.cookies import clear_auth_cookies, set_auth_cookies
from src.ycode.models.user import User, OAuthUser

auth_router = APIRouter()

def extract_yandex_userinfo(userinfo: dict) -> dict:
    user_id = userinfo.get("id")
    username = userinfo.get("login")
    email = userinfo.get("default_email") or userinfo.get("email")
    phone = userinfo.get("default_phone")
    if isinstance(phone, dict):
        phone = phone.get("number")

    missing = [ 
        name
        for name, value in {
            "id": user_id,
            "username": username,
            "email": email,
            "phone": phone,
        }.items()
        if not value
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing data from OAuth provider: {', '.join(missing)}."
        )

    return {
        "user_id": user_id,
        "username": username,
        "email": email,
        "phone": phone,
    }


async def get_unique_username(session: AsyncSession, base_username: str) -> str:
    base = base_username[:32]    

    result = await session.execute(
        select(User.username).where(User.username == base).limit(1)
    )
    if result.scalar_one_or_none() is None:
        return base
    
    pattern = f"{base}_%"

    result = await session.execute(
        select(User.username)
        .where(User.username.like(pattern))
        .limit(1000)
    )

    existing_usernames = {row[0] for row in result.all()}

    for i in range(1, 10000):
        new_username = f"{base}_{i}"
        if new_username not in existing_usernames:
            return new_username

    # Fallback в случае крайней необходимости
    while True:
        random_suffix = secrets.token_hex(4)
        new_username = f"{base}_{random_suffix}"
        if new_username not in existing_usernames:
            return new_username

@auth_router.post("/register")
async def register(user: UserRegistrationSchema, session: AsyncSession = Depends(get_async_session)):
    
    async with session.begin():    
        hashed_password = get_password_hash(user.password)
        new_user = User(
            username=user.username,
            email=user.email,
            phone=user.phone,
            hashed_password=hashed_password
        )

        session.add(new_user)      
        
        try:
            await session.flush()
        except IntegrityError:            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with given username, email, or phone already exists."
            )
        await session.refresh(new_user)

    return {"user_id": new_user.id, "username": new_user.username}           


@auth_router.post("/login")
async def login(
    user: UserLoginSchema,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
   ):    
    
    async with session.begin():
        result = await session.execute(
            select(User).where(User.username == user.username)
        )

        db_user = result.scalar_one_or_none()

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )        

        if not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password."
            )
        
        tokens = set_auth_cookies(response, db_user.id)

    return tokens


@auth_router.get("/oauth/login")
async def oauth_login():    
    state = secrets.token_urlsafe(16)    

    params = {
        "response_type": "code",
        "client_id": settings.YANDEX_CLIENT_ID,
        "redirect_uri": settings.YANDEX_REDIRECT_URI,
        "scope": " ".join(settings.YANDEX_SCOPES),
        "state": state,
    }

    url = settings.YANDEX_AUTH_URL + "?" + urlencode(params)

    redirect_response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    
    # TODO: Может ломаться при одновременных запросах с разных вкладок починить
    redirect_response.set_cookie(
        key="oauth_state",
        value=state,
        samesite="lax",
        secure=True,
        httponly=True,
        max_age=300,
        path="/"
    )

    return redirect_response

@auth_router.get("/oauth/callback")
async def oauth_callback(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
):

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    stored_state = request.cookies.get("oauth_state")

    if state != stored_state or not stored_state or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state."
        )

    response.delete_cookie("oauth_state", path="/")
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided."
        )
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": settings.YANDEX_CLIENT_ID,
        "client_secret": settings.YANDEX_CLIENT_SECRET,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        token_response = await client.post(
            settings.YANDEX_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
        
        if token_response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
             detail="Failed to obtain access token from OAuth provider."
            )
    
        token_pyload = token_response.json()    
        access_token = token_pyload.get("access_token")        
        refresh_token = token_pyload.get("refresh_token")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to obtain access token from OAuth provider."
            )
    
        userinfo_response = await client.get(
            settings.YANDEX_USERINFO_URL,
            headers={"Authorization": f"OAuth {access_token}"},
            )
    
    if userinfo_response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to obtain user info from OAuth provider."
        )
    
    userinfo = userinfo_response.json()

    provider_data = extract_yandex_userinfo(userinfo)
    provider = "yandex"
    user_id = provider_data["user_id"]
    username = provider_data["username"]
    email = provider_data["email"]
    phone = provider_data["phone"]    

    # ── Работа с базой ──
    async with session.begin():
        # Проверяем есть ли уже такой OAuth пользователь
        oauth_account = await session.execute(
            
            select(OAuthUser).where(
                OAuthUser.provider_user_id == user_id,
                OAuthUser.provider == provider
            )
        )

        oauth_account = oauth_account.scalar_one_or_none()

        # Если есть обновляем токены
        if oauth_account:
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            user = await session.get(User, oauth_account.user_id)
            user.last_login = func.now()

            # Изменим данные пользователя на актуальные из провайдера
            if email and user.email != email:
                user.email = email
            if phone and user.phone != phone:
                user.phone = phone    

        else:
            new_user = None
            
            # Проверяем есть ли пользователь с таким email или телефоном
            if email:
                new_user = await session.scalar(
                    select(User).where(User.email == email)
                )
            
            if not new_user and phone:
                new_user = await session.scalar(
                    select(User).where(User.phone == phone)
                )

            if not new_user:            
                base_username = username or f"{provider}_{user_id[:10]}"
                unique_username =  await get_unique_username(session, base_username)

                new_user = User(
                    username=unique_username,
                    email=email,
                    phone=phone,
                    is_profile_complete=False,
                )

                session.add(new_user)
                await session.flush()

            oauth_account = OAuthUser(
                user_id=new_user.id,
                provider=provider,
                provider_user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token
            )

            session.add(oauth_account)

            new_user.last_login = func.now()

            if new_user.password_hash and new_user.email and new_user.phone:
                new_user.is_profile_complete = True

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expire_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,   
            "user": {
                "id": new_user.id,
                "username": new_user.username or None,
                "email": new_user.email or None,
                "phone": new_user.phone or None,
                "is_profile_complete": new_user.is_profile_complete
            }
        }
        
@auth_router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    session: AsyncSession = Depends(get_async_session)
):
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing."
        )
    
    try:
        payload = verify_token(refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )    
    
    token_type: str = payload.get("type")
    user_id: int = payload.get("sub")
    if token_type != "refresh" or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )    
    
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )
    
    tokens = set_auth_cookies(response, db_user.id)
    return tokens

@auth_router.post("/logout")
async def logout(response: Response):
    
    clear_auth_cookies(response)
    return {"message": "Successfully logged out."}