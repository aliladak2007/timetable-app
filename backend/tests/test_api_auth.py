from app.core.security import hash_password
from app.models import Teacher, User


def test_bootstrap_then_login_and_access_me(client) -> None:
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        json={"full_name": "Admin", "email": "admin@test.com", "password": "StrongPass!123"},
    )
    assert bootstrap.status_code == 201

    login = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "StrongPass!123"})
    assert login.status_code == 200

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


def test_linked_non_admin_login_and_access_me(client, db_session) -> None:
    teacher = Teacher(full_name="Teacher", email="teacher@test.com", subject_tags="Maths")
    db_session.add(teacher)
    db_session.flush()
    user = User(
        full_name="Scheduler",
        email="scheduler@test.com",
        password_hash=hash_password("StrongPass!123"),
        role="staff_scheduler",
        linked_teacher_id=teacher.id,
        active=True,
    )
    db_session.add(user)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "scheduler@test.com", "password": "StrongPass!123"})

    assert login.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    assert me.status_code == 200
    assert me.json()["linked_teacher_id"] == teacher.id


def test_unlinked_non_admin_login_returns_clear_error(client, db_session) -> None:
    user = User(
        full_name="Viewer",
        email="viewer@test.com",
        password_hash=hash_password("StrongPass!123"),
        role="viewer",
        active=True,
    )
    db_session.add(user)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "viewer@test.com", "password": "StrongPass!123"})

    assert login.status_code == 403
    assert login.json()["detail"] == "This account is not linked to a teacher."


def test_invalid_credentials_show_clear_error(client) -> None:
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        json={"full_name": "Admin", "email": "admin@test.com", "password": "StrongPass!123"},
    )
    assert bootstrap.status_code == 201

    login = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "WrongPassword!123"})

    assert login.status_code == 401
    assert login.json()["detail"] == "Invalid credentials"
