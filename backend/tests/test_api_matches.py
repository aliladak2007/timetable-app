from datetime import date

from app.models import AvailabilitySlot, Student, StudentBlockedTime, StudentPreference, Teacher


def auth_header(client) -> dict[str, str]:
    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        json={"full_name": "Admin User", "email": "admin@test.com", "password": "StrongPass!123"},
    )
    assert bootstrap.status_code == 201

    login_response = client.post("/api/auth/login", json={"email": "admin@test.com", "password": "StrongPass!123"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_match_suggestions_endpoint_returns_ranked_slots(client, db_session) -> None:
    teacher = Teacher(full_name="Aisha Khan", email="api-aisha@test.com", subject_tags="Maths")
    student = Student(full_name="Mia Scott", parent_name="Parent", contact_email="mia@test.com")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add_all(
        [
            AvailabilitySlot(teacher_id=teacher.id, weekday=0, start_minute=900, end_minute=1020),
            StudentPreference(student_id=student.id, weekday=0, start_minute=900, end_minute=1020, priority=1),
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/matches/suggest",
        json={
            "teacher_id": teacher.id,
            "student_id": student.id,
            "duration_minutes": 60,
            "start_date": date(2026, 2, 1).isoformat(),
        },
        headers=auth_header(client),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["suggestions"]
    assert payload["suggestions"][0]["start_minute"] == 900
    assert "score_breakdown" in payload["suggestions"][0]


def test_create_session_rejects_student_blocked_time(client, db_session) -> None:
    teacher = Teacher(full_name="Blocked Teacher", email="blocked-teacher@test.com", subject_tags="Maths")
    student = Student(full_name="Blocked Student", parent_name="Parent", contact_email="blocked@test.com")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add_all(
        [
            AvailabilitySlot(teacher_id=teacher.id, weekday=0, start_minute=900, end_minute=1020),
            StudentBlockedTime(student_id=student.id, weekday=0, start_minute=930, end_minute=990, reason="Club"),
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/sessions",
        json={
            "teacher_id": teacher.id,
            "student_id": student.id,
            "weekday": 0,
            "start_minute": 930,
            "end_minute": 990,
            "duration_minutes": 60,
            "subject": "Maths",
            "status": "active",
            "start_date": date(2026, 2, 1).isoformat(),
        },
        headers=auth_header(client),
    )

    assert response.status_code == 400
    assert "blocked" in " ".join(response.json()["detail"]).lower()
