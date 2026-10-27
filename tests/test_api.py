import pytest
import app as student_api


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give each test its own temporary database.
    test_database = tmp_path / "test.db"
    monkeypatch.setattr(student_api, "DATABASE", test_database)

    student_api.app.config["TESTING"] = True
    student_api.init_db()

    with student_api.app.test_client() as test_client:
        yield test_client


def create_student(client, email="arun@example.com"):
    return client.post(
        "/api/students",
        json={
            "name": "Arun Kumar",
            "email": email,
            "department": "CSE",
            "year": 2,
        },
    )


def create_course(client):
    return client.post(
        "/api/courses",
        json={
            "course_code": "PY101",
            "course_name": "Python Programming",
            "credits": 4,
        },
    )


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_create_and_read_student(client):
    response = create_student(client)

    assert response.status_code == 201
    student_id = response.json["id"]

    result = client.get(f"/api/students/{student_id}")

    assert result.status_code == 200
    assert result.json["name"] == "Arun Kumar"


def test_duplicate_student_email_is_rejected(client):
    first = create_student(client)
    second = create_student(client)

    assert first.status_code == 201
    assert second.status_code == 409


def test_invalid_student_year_is_rejected(client):
    response = client.post(
        "/api/students",
        json={
            "name": "Test Student",
            "email": "test@example.com",
            "department": "CSE",
            "year": 5,
        },
    )

    assert response.status_code == 400


def test_update_student(client):
    created = create_student(client)
    student_id = created.json["id"]

    response = client.put(
        f"/api/students/{student_id}",
        json={
            "name": "Arun Updated",
            "email": "arun@example.com",
            "department": "IT",
            "year": 3,
        },
    )

    assert response.status_code == 200
    assert response.json["name"] == "Arun Updated"
    assert response.json["year"] == 3


def test_delete_student(client):
    created = create_student(client)
    student_id = created.json["id"]

    deleted = client.delete(f"/api/students/{student_id}")
    result = client.get(f"/api/students/{student_id}")

    assert deleted.status_code == 200
    assert result.status_code == 404


def test_create_course(client):
    response = create_course(client)

    assert response.status_code == 201
    assert response.json["course_code"] == "PY101"


def test_enrollment_and_duplicate_protection(client):
    student = create_student(client)
    course = create_course(client)

    enrollment = {
        "student_id": student.json["id"],
        "course_id": course.json["id"],
    }

    first = client.post("/api/enrollments", json=enrollment)
    duplicate = client.post("/api/enrollments", json=enrollment)

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_student_search_and_pagination(client):
    create_student(client, "arun@example.com")
    create_student(client, "another@example.com")

    response = client.get(
        "/api/students?search=arun@example.com&page=1&limit=1"
    )

    assert response.status_code == 200
    assert len(response.json["data"]) == 1
    assert response.json["pagination"]["total_records"] == 1


def test_invalid_pagination_is_rejected(client):
    response = client.get("/api/students?page=0")

    assert response.status_code == 400