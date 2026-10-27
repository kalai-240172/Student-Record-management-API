from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
from contextlib import closing

app = Flask(__name__)

# Store the database beside this Python file
DATABASE = Path(__file__).with_name("database.db")


def get_db():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    """Create the students table if it does not exist."""
    with closing(get_db()) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                year INTEGER NOT NULL CHECK (year BETWEEN 1 AND 4)
            )
        """)
        db.commit()

        db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL UNIQUE,
                course_name TEXT NOT NULL,
                credits INTEGER NOT NULL CHECK (credits BETWEEN 1 AND 10)
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrollment_date TEXT NOT NULL DEFAULT CURRENT_DATE,
                status TEXT NOT NULL DEFAULT 'enrolled'
                    CHECK (status IN ('enrolled', 'completed', 'dropped')),
                FOREIGN KEY (student_id) REFERENCES students(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id)
                    ON DELETE CASCADE,
                UNIQUE (student_id, course_id)
            )
        """)
        db.commit()


def student_to_dict(student):
    """Convert a database row into a JSON-friendly dictionary."""
    return dict(student)


@app.route("/")
def home():
    return "Welcome to the Student Record Management API!"


@app.route("/health")
def health():
    return {"status": "healthy"}


# CREATE a student
@app.route("/api/students", methods=["POST"])
def create_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    for field in ["name", "email", "department", "year"]:
        if field not in data or data[field] in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    for field in ["name", "email", "department"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({
                "error": f"{field} must be a non-empty string"
            }), 400

    if not isinstance(data["year"], int) or isinstance(data["year"], bool):
        return jsonify({"error": "Year must be an integer"}), 400

    if data["year"] not in (1, 2, 3, 4):
        return jsonify({"error": "Year must be between 1 and 4"}), 400

    email = data["email"].strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    try:
        with closing(get_db()) as db:
            cursor = db.execute(
                """
                INSERT INTO students (name, email, department, year)
                VALUES (?, ?, ?, ?)
                """,
                (
                    data["name"].strip(),
                    email,
                    data["department"].strip(),
                    data["year"]
                )
            )
            db.commit()

            student = db.execute(
                "SELECT * FROM students WHERE id = ?",
                (cursor.lastrowid,)
            ).fetchone()

            return jsonify(student_to_dict(student)), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409


# READ all students
# READ, SEARCH, FILTER, SORT, AND PAGINATE STUDENTS
@app.route("/api/students", methods=["GET"])
def get_students():
    search = request.args.get("search", "").strip()
    department = request.args.get("department", "").strip()
    year_text = request.args.get("year", "").strip()

    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "asc").lower()

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({
            "error": "page and limit must be integers"
        }), 400

    if page < 1 or limit < 1 or limit > 100:
        return jsonify({
            "error": "page must be at least 1 and limit must be 1 to 100"
        }), 400

    if year_text:
        try:
            year = int(year_text)
        except ValueError:
            return jsonify({"error": "year must be an integer"}), 400

        if year not in (1, 2, 3, 4):
            return jsonify({"error": "year must be between 1 and 4"}), 400

    allowed_sort_fields = {
        "id": "id",
        "name": "name",
        "email": "email",
        "department": "department",
        "year": "year"
    }

    if sort_by not in allowed_sort_fields:
        return jsonify({
            "error": "Invalid sort_by field"
        }), 400

    if order not in ("asc", "desc"):
        return jsonify({
            "error": "order must be asc or desc"
        }), 400

    conditions = []
    params = []

    if search:
        conditions.append(
            "(name LIKE ? OR email LIKE ? OR department LIKE ?)"
        )
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])

    if department:
        conditions.append("LOWER(department) = LOWER(?)")
        params.append(department)

    if year_text:
        conditions.append("year = ?")
        params.append(int(year_text))

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    offset = (page - 1) * limit

    with closing(get_db()) as db:
        total = db.execute(
            "SELECT COUNT(*) FROM students" + where_clause,
            params
        ).fetchone()[0]

        sql = (
            "SELECT * FROM students"
            + where_clause
            + f" ORDER BY {allowed_sort_fields[sort_by]} {order.upper()}"
            + " LIMIT ? OFFSET ?"
        )

        students = db.execute(
            sql,
            params + [limit, offset]
        ).fetchall()

    return jsonify({
        "data": [dict(student) for student in students],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total,
            "total_pages": (total + limit - 1) // limit
        }
    }), 200
# READ one student
@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    with closing(get_db()) as db:
        student = db.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        return jsonify(student_to_dict(student)), 200


# UPDATE a student
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    for field in ["name", "email", "department", "year"]:
        if field not in data or data[field] in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    for field in ["name", "email", "department"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({
                "error": f"{field} must be a non-empty string"
            }), 400

    if not isinstance(data["year"], int) or isinstance(data["year"], bool):
        return jsonify({"error": "Year must be an integer"}), 400

    if data["year"] not in (1, 2, 3, 4):
        return jsonify({"error": "Year must be between 1 and 4"}), 400

    email = data["email"].strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    try:
        with closing(get_db()) as db:
            cursor = db.execute(
                """
                UPDATE students
                SET name = ?, email = ?, department = ?, year = ?
                WHERE id = ?
                """,
                (
                    data["name"].strip(),
                    email,
                    data["department"].strip(),
                    data["year"],
                    student_id
                )
            )

            if cursor.rowcount == 0:
                return jsonify({"error": "Student not found"}), 404

            db.commit()

            student = db.execute(
                "SELECT * FROM students WHERE id = ?",
                (student_id,)
            ).fetchone()

            return jsonify(student_to_dict(student)), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409


# DELETE a student
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    with closing(get_db()) as db:
        cursor = db.execute(
            "DELETE FROM students WHERE id = ?",
            (student_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404

        db.commit()

        return jsonify({
            "message": "Student deleted successfully"
        }), 200

# CREATE a course
@app.route("/api/courses", methods=["POST"])
def create_course():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    for field in ["course_code", "course_name", "credits"]:
        if field not in data or data[field] in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    for field in ["course_code", "course_name"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({"error": f"{field} must be a non-empty string"}), 400

    if not isinstance(data["credits"], int) or isinstance(data["credits"], bool):
        return jsonify({"error": "Credits must be an integer"}), 400

    if not 1 <= data["credits"] <= 10:
        return jsonify({"error": "Credits must be between 1 and 10"}), 400

    try:
        with closing(get_db()) as db:
            cursor = db.execute(
                """
                INSERT INTO courses (course_code, course_name, credits)
                VALUES (?, ?, ?)
                """,
                (
                    data["course_code"].strip().upper(),
                    data["course_name"].strip(),
                    data["credits"]
                )
            )
            db.commit()

            course = db.execute(
                "SELECT * FROM courses WHERE id = ?",
                (cursor.lastrowid,)
            ).fetchone()

            return jsonify(dict(course)), 201

    except sqlite3.IntegrityError:
        return jsonify({"error": "Course code already exists"}), 409


# READ all courses
@app.route("/api/courses", methods=["GET"])
def get_courses():
    search = request.args.get("search", "").strip()
    credits_text = request.args.get("credits", "").strip()

    sort_by = request.args.get("sort_by", "id")
    order = request.args.get("order", "asc").lower()

    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify({
            "error": "page and limit must be integers"
        }), 400

    if page < 1 or limit < 1 or limit > 100:
        return jsonify({
            "error": "page must be at least 1 and limit must be 1 to 100"
        }), 400

    if credits_text:
        try:
            credits = int(credits_text)
        except ValueError:
            return jsonify({"error": "credits must be an integer"}), 400

        if credits < 1 or credits > 10:
            return jsonify({
                "error": "credits must be between 1 and 10"
            }), 400

    allowed_sort_fields = {
        "id": "id",
        "course_code": "course_code",
        "course_name": "course_name",
        "credits": "credits"
    }

    if sort_by not in allowed_sort_fields:
        return jsonify({"error": "Invalid sort_by field"}), 400

    if order not in ("asc", "desc"):
        return jsonify({"error": "order must be asc or desc"}), 400

    conditions = []
    params = []

    if search:
        conditions.append(
            "(course_code LIKE ? OR course_name LIKE ?)"
        )
        pattern = f"%{search}%"
        params.extend([pattern, pattern])

    if credits_text:
        conditions.append("credits = ?")
        params.append(int(credits_text))

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    offset = (page - 1) * limit

    with closing(get_db()) as db:
        total = db.execute(
            "SELECT COUNT(*) FROM courses" + where_clause,
            params
        ).fetchone()[0]

        sql = (
            "SELECT * FROM courses"
            + where_clause
            + f" ORDER BY {allowed_sort_fields[sort_by]} {order.upper()}"
            + " LIMIT ? OFFSET ?"
        )

        courses = db.execute(
            sql,
            params + [limit, offset]
        ).fetchall()

    return jsonify({
        "data": [dict(course) for course in courses],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_records": total,
            "total_pages": (total + limit - 1) // limit
        }
    }), 200
# READ one course
@app.route("/api/courses/<int:course_id>", methods=["GET"])
def get_course(course_id):
    with closing(get_db()) as db:
        course = db.execute(
            "SELECT * FROM courses WHERE id = ?",
            (course_id,)
        ).fetchone()

        if course is None:
            return jsonify({"error": "Course not found"}), 404

        return jsonify(dict(course)), 200
# CREATE an enrollment
@app.route("/api/enrollments", methods=["POST"])
def create_enrollment():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    student_id = data.get("student_id")
    course_id = data.get("course_id")

    if (
        not isinstance(student_id, int) or isinstance(student_id, bool)
        or not isinstance(course_id, int) or isinstance(course_id, bool)
    ):
        return jsonify({
            "error": "student_id and course_id must be integers"
        }), 400

    with closing(get_db()) as db:
        student = db.execute(
            "SELECT id FROM students WHERE id = ?", (student_id,)
        ).fetchone()

        if student is None:
            return jsonify({"error": "Student not found"}), 404

        course = db.execute(
            "SELECT id FROM courses WHERE id = ?", (course_id,)
        ).fetchone()

        if course is None:
            return jsonify({"error": "Course not found"}), 404

        try:
            cursor = db.execute(
                """
                INSERT INTO enrollments (student_id, course_id)
                VALUES (?, ?)
                """,
                (student_id, course_id)
            )
            db.commit()

        except sqlite3.IntegrityError:
            return jsonify({
                "error": "Student is already enrolled in this course"
            }), 409

        enrollment = db.execute(
            """
            SELECT e.id, e.student_id, s.name AS student_name,
                   e.course_id, c.course_name, e.enrollment_date, e.status
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            WHERE e.id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

        return jsonify(dict(enrollment)), 201


# READ all enrollments
@app.route("/api/enrollments", methods=["GET"])
def get_enrollments():
    with closing(get_db()) as db:
        enrollments = db.execute("""
            SELECT e.id, e.student_id, s.name AS student_name,
                   e.course_id, c.course_name, e.enrollment_date, e.status
            FROM enrollments e
            JOIN students s ON e.student_id = s.id
            JOIN courses c ON e.course_id = c.id
            ORDER BY e.id
        """).fetchall()

        return jsonify([dict(e) for e in enrollments]), 200


# DELETE an enrollment
@app.route("/api/enrollments/<int:enrollment_id>", methods=["DELETE"])
def delete_enrollment(enrollment_id):
    with closing(get_db()) as db:
        cursor = db.execute(
            "DELETE FROM enrollments WHERE id = ?",
            (enrollment_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Enrollment not found"}), 404

        db.commit()

        return jsonify({
            "message": "Enrollment deleted successfully"
        }), 200

if __name__ == "__main__":
    
    init_db()
    
    
    app.run(debug=True)
    