# Student Record Management API

A beginner-friendly REST API built with Python, Flask, and SQLite to manage student records, courses, and student enrollments.

## Features

- Create, retrieve, update, and delete student records
- Create and retrieve courses
- Enroll students in courses
- View and delete enrollments
- Search students by name, email, or department
- Filter students by department and year
- Sort and paginate student and course results
- Validate input and handle duplicate records
- Store data persistently using SQLite

## Technology Stack

- Python
- Flask
- SQLite
- REST API and JSON
- pytest for automated testing
- Git and GitHub for version control

## Project Structure

```text
student-record-api/
├── app.py
├── database.db
├── requirements.txt
├── README.md
├── .gitignore
├── tests/
│   └── test_api.py
└── .venv/
```

The virtual environment and local database are not committed to GitHub.

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd student-record-api
```

Replace the placeholder with your actual repository URL.

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Start the application

```powershell
python app.py
```

The development server runs at:

`http://127.0.0.1:5000`

The SQLite database is initialized automatically when the application starts.

## API Endpoints

### Students

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/students` | Create a student |
| GET | `/api/students` | List students |
| GET | `/api/students/<id>` | Retrieve one student |
| PUT | `/api/students/<id>` | Update a student |
| DELETE | `/api/students/<id>` | Delete a student |

Student fields: `name`, `email`, `department`, `year`.

### Courses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/courses` | Create a course |
| GET | `/api/courses` | List courses |
| GET | `/api/courses/<id>` | Retrieve one course |

Course fields: `course_code`, `course_name`, `credits`.

### Enrollments

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/enrollments` | Enroll a student in a course |
| GET | `/api/enrollments` | List enrollments |
| DELETE | `/api/enrollments/<id>` | Delete an enrollment |

Enrollment creation requires `student_id` and `course_id`. Duplicate enrollments are rejected.

## Example Requests

### Create a student

`POST /api/students`

```json
{
  "name": "Arun Kumar",
  "email": "arun@example.com",
  "department": "CSE",
  "year": 2
}
```

### Create a course

`POST /api/courses`

```json
{
  "course_code": "PY101",
  "course_name": "Python Programming",
  "credits": 4
}
```

### Enroll a student

`POST /api/enrollments`

```json
{
  "student_id": 1,
  "course_id": 1
}
```

Use IDs that actually exist in your database.

## Search, Filtering, Sorting, and Pagination

Student listing supports these query parameters:

- `search`: search name, email, or department
- `department`: filter by department
- `year`: filter by academic year
- `sort_by`: `id`, `name`, `email`, `department`, or `year`
- `order`: `asc` or `desc`
- `page`: page number, starting at 1
- `limit`: records per page, from 1 to 100

Example:

`GET /api/students?search=Arun&department=CSE&year=2&sort_by=name&order=asc&page=1&limit=5`

Courses support `search`, `credits`, `sort_by`, `order`, `page`, and `limit`.

List endpoints return a JSON object containing `data` and `pagination`.

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | Request succeeded |
| 201 | Record created |
| 400 | Invalid request data |
| 404 | Record not found |
| 409 | Duplicate record or constraint conflict |

## Running Tests

Install the dependencies and run:

```powershell
python -m pytest -v
```

## Notes

This project is intended for learning and demonstration. The Flask development server is not intended for production deployment. Authentication, authorization, production deployment, and additional security hardening can be added in future versions.

## Author

Add your name and GitHub profile here.
