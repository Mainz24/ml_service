from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Depends, Request, Form, status, Response, HTTPException
from typing import Optional
from datetime import timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates

from app.infrastructure.models.user import User
from app.infrastructure.auth.authenticate import get_current_user_optional, get_current_user_from_cookie
from database.database import get_session
from app.infrastructure.services.crud.ml_service import submit_prediction_task, get_prediction_task_history, get_prediction_result_history
from app.infrastructure.services.crud.transaction import get_transaction_history, deposit_credits, withdraw_credits
from app.infrastructure.auth.jwt_handler import create_access_token
from app.infrastructure.auth.hash_password import get_password_hash
from app.infrastructure.auth.authenticate import authenticate_user
from app.infrastructure.services.crud import user as UserService


logger = logging.getLogger(__name__)

html_router = APIRouter()

templates = Jinja2Templates(directory="/src/app/templates")

def set_auth_cookie(response: Response, user_email: str):
    """
    Устанавливает HTTP-only cookie с JWT токеном для аутентификации.

    Args:
        response: Объект Response FastAPI/Starlette, в который будут добавлены куки.
        user_email: Email пользователя, который будет использован как 'sub' в токене.
    """

    # 1. Создание токена (логика бэкенда)
    access_token_expires = timedelta(minutes=30)
    # Предполагается, что у вас есть функция create_access_token
    access_token = create_access_token(
        data={"sub": user_email},
        expires_delta=access_token_expires
    )

    # 2. Установка куки
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # Куки недоступны через JavaScript (защита от XSS)
        secure=False,  # Только по HTTPS (используйте True в продакшене, False для локальной разработки без HTTPS)
        samesite="lax",  # Защита от CSRF
        max_age=30 * 60, # Время жизни куки (30 минут в секундах)
        path="/"
    )


# --- Эндпоинт для отображения страницы регистрации (GET-запрос) ---
@html_router.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "error": None})

@html_router.post("/register", response_class=HTMLResponse)
async def handle_registration(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Валидация и обрезка пароля (как в вашем API-эндпоинте)
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
            password_clean = password_bytes.decode("utf-8", errors="ignore")
        else:
            password_clean = password

        hashed_pw = get_password_hash(password_clean)
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_pw,
            credits=0.0,
            is_active=True,
            is_superuser=False
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # УСТАНАВЛИВАЕМ КУКУ И ПЕРЕНАПРАВЛЯЕМ НА ГЛАВНУЮ
        redirect_resp = RedirectResponse(url="/", status_code=303)
        set_auth_cookie(redirect_resp, user.email)  # ← устанавливаем куку в redirect_resp
        return redirect_resp

    except ValueError as e:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": str(e)},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Ошибка при регистрации"},
            status_code=500
        )

@html_router.get("/signin", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@html_router.post("/signin")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    user = await authenticate_user(username, password, session)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный email или пароль"},
            status_code=401
        )

    # Устанавливаем куку
    access_token = create_access_token(data={"sub": user.email})

    redirect_resp = RedirectResponse(url="/", status_code=303)
    redirect_resp.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=1800
    )
    return redirect_resp


@html_router.get("/users", response_class=HTMLResponse) # URL для UI
async def list_users_admin_ui(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user_optional)
):
    """
    Display list of all users using Jinja2 template (Admin UI endpoint).
    """
    if not current_user.is_superuser:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    users = await UserService.get_all_users(session)
    # Возвращаем HTML-шаблон, передавая список пользователей в контексте Jinja2
    return templates.TemplateResponse("users_admin.html", {"request": request, "users": users})


@html_router.get("/", response_class=HTMLResponse)
async def index_ui(
        request: Request,
        current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user is None:
        return RedirectResponse(url="/signin", status_code=303)

    return templates.TemplateResponse("home.html", {"request": request, "user": current_user})


# --- Эндпоинт для отображения страницы ML-задач (GET-запрос) ---
@html_router.get("/tasks_ui", response_class=HTMLResponse)
async def tasks_page_ui(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    # Получаем историю задач и результатов для передачи в шаблон
    tasks = await get_prediction_task_history(current_user.id, session)
    results = await get_prediction_result_history(current_user.id, session)

    return templates.TemplateResponse(
        "ml_tasks.html",
        {"request": request,
         "user": current_user,
         "tasks": tasks,
         "results": results,
         "error": None,
         "message": None}
    )


# --- Эндпоинт для обработки отправки задачи из формы (POST-запрос) ---
@html_router.post("/predict_form", response_class=HTMLResponse) # Новый URL для обработки формы
async def request_prediction_form(
    request: Request,
    data: str = Form(...), # Читаем из формы, используем alias "data" для соответствия модели
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    try:
        await submit_prediction_task(
            user_id=current_user.id,
            input_data=data,
            session=session
        )
        # После успеха перенаправляем обратно на страницу задач
        response = RedirectResponse(url="/tasks_ui?message=Task submitted successfully", status_code=status.HTTP_303_SEE_OTHER)
        return response
    except ValueError as e:
        # В случае ошибки возвращаем страницу с сообщением об ошибке
        tasks = await get_prediction_task_history(current_user.id, session)
        results = await get_prediction_result_history(current_user.id, session)
        return templates.TemplateResponse("ml_tasks.html", {"request": request, "user": current_user, "tasks": tasks, "results": results, "error": str(e), "message": None})


# --- Эндпоинт для отображения страницы баланса/транзакций (GET-запрос) ---
@html_router.get("/balance_ui", response_class=HTMLResponse)
async def balance_page_ui(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    # Получаем текущий баланс и историю транзакций для передачи в шаблон
    balance = current_user.credits
    history = await get_transaction_history(current_user.id, session)

    return templates.TemplateResponse(
        "balance.html",
        {"request": request, "user": current_user, "balance": balance, "history": history, "error": None, "message": None}
    )


# --- Эндпоинт для обработки пополнения (POST-запрос из формы) ---
@html_router.post("/deposit_form", response_class=HTMLResponse) # Новый URL для обработки формы
async def deposit_credits_form(
    request: Request,
    amount: float = Form(...), # Читаем из формы
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    try:
        await deposit_credits(user_id=current_user.id, amount=amount, session=session)
        response = RedirectResponse(url="/balance_ui?message=Deposit successful", status_code=status.HTTP_303_SEE_OTHER)
        return response
    except ValueError as e:
        # В случае ошибки возвращаем страницу с сообщением об ошибке
        balance = current_user.credits
        history = await get_transaction_history(current_user.id, session)
        return templates.TemplateResponse("balance.html", {"request": request, "user": current_user, "balance": balance, "history": history, "error": str(e), "message": None})


# --- Эндпоинт для обработки списания (POST-запрос из формы) ---
@html_router.post("/withdraw_form", response_class=HTMLResponse) # Новый URL для обработки формы
async def withdraw_credits_form(
    request: Request,
    amount: float = Form(...), # Читаем из формы
    current_user: User = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    try:
        await withdraw_credits(user_id=current_user.id, amount=amount, session=session)
        response = RedirectResponse(url="/balance_ui?message=Withdrawal successful", status_code=status.HTTP_303_SEE_OTHER)
        return response
    except ValueError as e:
        balance = current_user.credits
        history = await get_transaction_history(current_user.id, session)
        return templates.TemplateResponse("balance.html", {"request": request, "user": current_user, "balance": balance, "history": history, "error": str(e), "message": None})


# --- Эндпоинт для отображения страницы входа (GET-запрос) ---
@html_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@html_router.get("/logout")
async def logout_endpoint(response: Response):
    # Удаляем куки, устанавливая срок их действия в прошлое
    response.delete_cookie("access_token")
    # Перенаправляем пользователя на страницу входа
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)