from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.config import (
    DEFAULT_DESKTOP_CORS_ORIGINS,
    DEFAULT_DEV_CORS_ORIGINS,
    Settings,
)


def build_cors_test_client(origins: list[str]) -> TestClient:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.post("/api/auth/login")
    def login() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/auth/bootstrap-status")
    def bootstrap_status() -> dict[str, bool]:
        return {"needs_bootstrap": False}

    return TestClient(app)


def test_desktop_settings_include_packaged_and_localhost_origins() -> None:
    settings = Settings(app_env="desktop")

    assert settings.resolved_cors_origins == [
        *DEFAULT_DESKTOP_CORS_ORIGINS,
        *DEFAULT_DEV_CORS_ORIGINS,
    ]


def test_desktop_preflight_accepts_tauri_localhost_origin() -> None:
    client = build_cors_test_client(Settings(app_env="desktop").resolved_cors_origins)

    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://tauri.localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://tauri.localhost"


def test_desktop_preflight_accepts_null_origin() -> None:
    client = build_cors_test_client(Settings(app_env="desktop").resolved_cors_origins)

    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "null",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "null"


def test_desktop_preflight_accepts_https_tauri_localhost_origin() -> None:
    client = build_cors_test_client(Settings(app_env="desktop").resolved_cors_origins)

    response = client.options(
        "/api/auth/bootstrap-status",
        headers={
            "Origin": "https://tauri.localhost",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://tauri.localhost"


def test_preflight_keeps_localhost_dev_origin_working() -> None:
    client = build_cors_test_client(Settings(app_env="desktop").resolved_cors_origins)

    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
