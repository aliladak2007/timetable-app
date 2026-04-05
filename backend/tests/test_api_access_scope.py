from datetime import date

from app.core.security import create_access_token, hash_password
from app.models import AuditLog, Session as SessionModel, Student, Teacher, User


PASSWORD = "StrongPass!123"


def login_header(client, email: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_user(
    db_session,
    *,
    full_name: str,
    email: str,
    role: str,
    linked_teacher_id: int | None = None,
) -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=hash_password(PASSWORD),
        role=role,
        linked_teacher_id=linked_teacher_id,
        active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


def seed_scope_data(db_session):
    teacher_one = Teacher(full_name="Teacher One", email="teacher-one@test.com", subject_tags="Maths")
    teacher_two = Teacher(full_name="Teacher Two", email="teacher-two@test.com", subject_tags="Science")
    student_one = Student(full_name="Student One", parent_name="Parent One", contact_email="student-one@test.com")
    student_two = Student(full_name="Student Two", parent_name="Parent Two", contact_email="student-two@test.com")
    db_session.add_all([teacher_one, teacher_two, student_one, student_two])
    db_session.flush()

    session_one = SessionModel(
        teacher_id=teacher_one.id,
        student_id=student_one.id,
        weekday=0,
        start_minute=900,
        end_minute=960,
        duration_minutes=60,
        subject="Maths",
        status="active",
        start_date=date(2026, 1, 5),
    )
    session_two = SessionModel(
        teacher_id=teacher_two.id,
        student_id=student_two.id,
        weekday=1,
        start_minute=960,
        end_minute=1020,
        duration_minutes=60,
        subject="Science",
        status="active",
        start_date=date(2026, 1, 6),
    )
    db_session.add_all([session_one, session_two])
    db_session.flush()
    return teacher_one, teacher_two, student_one, student_two, session_one, session_two


def test_admin_can_assign_user_to_teacher_via_api(client, db_session) -> None:
    teacher = Teacher(full_name="Assigned Teacher", email="assigned-teacher@test.com", subject_tags="English")
    db_session.add(teacher)
    db_session.commit()

    bootstrap = client.post(
        "/api/auth/bootstrap-admin",
        json={"full_name": "Admin", "email": "admin@test.com", "password": PASSWORD},
    )
    assert bootstrap.status_code == 201
    admin_headers = login_header(client, "admin@test.com")

    response = client.post(
        "/api/auth/users",
        json={
            "full_name": "Scoped Scheduler",
            "email": "scoped@test.com",
            "password": PASSWORD,
            "role": "staff_scheduler",
            "linked_teacher_id": teacher.id,
            "active": True,
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    assert response.json()["linked_teacher_id"] == teacher.id


def test_admin_sees_all_data(client, db_session) -> None:
    teacher_one, teacher_two, student_one, student_two, _, _ = seed_scope_data(db_session)
    create_user(db_session, full_name="Admin", email="admin@test.com", role="admin")
    db_session.commit()

    headers = login_header(client, "admin@test.com")

    sessions_response = client.get("/api/sessions", headers=headers)
    students_response = client.get("/api/students", headers=headers)
    teachers_response = client.get("/api/teachers", headers=headers)
    dashboard_response = client.get("/api/dashboard/summary", headers=headers)

    assert sessions_response.status_code == 200
    assert len(sessions_response.json()) == 2
    assert students_response.status_code == 200
    assert {item["id"] for item in students_response.json()} == {student_one.id, student_two.id}
    assert teachers_response.status_code == 200
    assert {item["id"] for item in teachers_response.json()} == {teacher_one.id, teacher_two.id}
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["student_count"] == 2


def test_scoped_user_only_sees_own_data(client, db_session) -> None:
    teacher_one, teacher_two, student_one, student_two, session_one, _ = seed_scope_data(db_session)
    create_user(db_session, full_name="Scoped User", email="scoped@test.com", role="staff_scheduler", linked_teacher_id=teacher_one.id)
    db_session.commit()

    headers = login_header(client, "scoped@test.com")

    sessions_response = client.get("/api/sessions", headers=headers)
    students_response = client.get("/api/students", headers=headers)
    teachers_response = client.get("/api/teachers", headers=headers)
    dashboard_response = client.get("/api/dashboard/summary", headers=headers)

    assert sessions_response.status_code == 200
    assert [item["id"] for item in sessions_response.json()] == [session_one.id]
    assert students_response.status_code == 200
    assert [item["id"] for item in students_response.json()] == [student_one.id]
    assert teachers_response.status_code == 200
    assert [item["id"] for item in teachers_response.json()] == [teacher_one.id]
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["teacher_count"] == 1
    assert dashboard_response.json()["student_count"] == 1
    assert dashboard_response.json()["recurring_session_count"] == 1
    assert dashboard_response.json()["unassigned_students"] == []
    assert dashboard_response.json()["closures"] == []


def test_scoped_user_cannot_access_other_teacher_records_by_id(client, db_session) -> None:
    teacher_one, teacher_two, _, student_two, _, _ = seed_scope_data(db_session)
    create_user(db_session, full_name="Scoped User", email="scoped@test.com", role="staff_scheduler", linked_teacher_id=teacher_one.id)
    db_session.commit()

    headers = login_header(client, "scoped@test.com")

    assert client.get(f"/api/teachers/{teacher_two.id}", headers=headers).status_code == 404
    assert client.get(f"/api/students/{student_two.id}", headers=headers).status_code == 404
    assert client.get(f"/api/exports/calendar/teacher/{teacher_two.id}.ics", headers=headers).status_code == 404


def test_scoped_user_cannot_access_global_endpoints(client, db_session) -> None:
    teacher_one, _, _, _, _, _ = seed_scope_data(db_session)
    create_user(db_session, full_name="Scoped User", email="scoped@test.com", role="viewer", linked_teacher_id=teacher_one.id)
    db_session.add(AuditLog(action="test", entity_type="test", entity_id="1", outcome="success", summary="log", details={}, actor_email="system"))
    db_session.commit()

    headers = login_header(client, "scoped@test.com")

    assert client.get("/api/schedule/closures", headers=headers).status_code == 403
    assert client.get("/api/audit-logs", headers=headers).status_code == 403
    assert client.get("/api/exports/calendar/centre/1.ics", headers=headers).status_code == 403


def test_scoped_exports_and_occurrences_are_filtered(client, db_session) -> None:
    teacher_one, teacher_two, _, _, session_one, _ = seed_scope_data(db_session)
    create_user(db_session, full_name="Scoped User", email="scoped@test.com", role="staff_scheduler", linked_teacher_id=teacher_one.id)
    db_session.commit()

    headers = login_header(client, "scoped@test.com")

    csv_response = client.get("/api/exports/sessions.csv", headers=headers)
    occurrences_response = client.post(
        "/api/schedule/occurrences/query",
        json={"date_from": "2026-01-01", "date_to": "2026-01-31"},
        headers=headers,
    )
    forbidden_occurrence_response = client.post(
        "/api/schedule/occurrences/query",
        json={"date_from": "2026-01-01", "date_to": "2026-01-31", "teacher_id": teacher_two.id},
        headers=headers,
    )

    assert csv_response.status_code == 200
    assert str(session_one.id) in csv_response.text
    assert f",{teacher_two.id}," not in csv_response.text
    assert occurrences_response.status_code == 200
    assert {item["teacher_id"] for item in occurrences_response.json()} == {teacher_one.id}
    assert forbidden_occurrence_response.status_code == 404


def test_role_escalation_attempt_with_tampered_role_claim_fails(client, db_session) -> None:
    teacher = Teacher(full_name="Teacher One", email="teacher-one@test.com", subject_tags="Maths")
    db_session.add(teacher)
    db_session.flush()
    user = create_user(db_session, full_name="Viewer", email="viewer@test.com", role="viewer", linked_teacher_id=teacher.id)
    db_session.commit()

    token, _ = create_access_token(
        user_id=user.id,
        email=user.email,
        role="admin",
        session_version=user.session_version,
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/auth/users", headers=headers)

    assert response.status_code == 403


def test_unlinked_non_admin_is_denied_scoped_endpoints(client, db_session) -> None:
    create_user(db_session, full_name="Unlinked Viewer", email="viewer@test.com", role="viewer")
    db_session.commit()

    response = client.post("/api/auth/login", json={"email": "viewer@test.com", "password": PASSWORD})

    assert response.status_code == 403
    assert response.json()["detail"] == "This account is not linked to a teacher."
