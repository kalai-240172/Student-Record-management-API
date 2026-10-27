from flask import Flask, request, jsonify

app = Flask(__name__)

# Temporary storage for student records
students = {}
next_student_id = 1


@app.route("/")
def home():
    return "Welcome to the Student Record Management API!"


@app.route("/health")
def health():
    return {"status": "healthy"}


# CREATE a student
@app.route("/api/students", methods=["POST"])
def create_student():
    global next_student_id

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    required_fields = ["name", "email", "department", "year"]

    for field in required_fields:
        if field not in data or data[field] in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    if not all(
        isinstance(data[field], str) and data[field].strip()
        for field in ["name", "email", "department"]
    ):
        return jsonify({
            "error": "Name, email, and department must be non-empty strings"
        }), 400

    if not isinstance(data["year"], int) or isinstance(data["year"], bool):
        return jsonify({"error": "Year must be a number"}), 400

    if data["year"] not in (1, 2, 3, 4):
        return jsonify({"error": "Year must be between 1 and 4"}), 400

    email = data["email"].strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    if any(student["email"] == email for student in students.values()):
        return jsonify({"error": "Email already exists"}), 409

    student = {
        "id": next_student_id,
        "name": data["name"].strip(),
        "email": email,
        "department": data["department"].strip(),
        "year": data["year"]
    }

    students[next_student_id] = student
    next_student_id += 1

    return jsonify(student), 201


# READ all students
@app.route("/api/students", methods=["GET"])
def get_students():
    return jsonify(list(students.values())), 200


# READ one student
@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = students.get(student_id)

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(student), 200

# UPDATE a student
@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    student = students.get(student_id)

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a valid JSON object"}), 400

    required_fields = ["name", "email", "department", "year"]

    for field in required_fields:
        if field not in data or data[field] in (None, ""):
            return jsonify({"error": f"{field} is required"}), 400

    for field in ["name", "email", "department"]:
        if not isinstance(data[field], str) or not data[field].strip():
            return jsonify({
                "error": f"{field} must be a non-empty string"
            }), 400

    if not isinstance(data["year"], int) or isinstance(data["year"], bool):
        return jsonify({"error": "Year must be a number"}), 400

    if data["year"] not in (1, 2, 3, 4):
        return jsonify({"error": "Year must be between 1 and 4"}), 400

    email = data["email"].strip().lower()

    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "Enter a valid email address"}), 400

    for other_id, other_student in students.items():
        if other_id != student_id and other_student["email"] == email:
            return jsonify({"error": "Email already exists"}), 409

    student.update({
        "name": data["name"].strip(),
        "email": email,
        "department": data["department"].strip(),
        "year": data["year"]
    })

    return jsonify(student), 200

# DELETE a student
@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    student = students.get(student_id)

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    del students[student_id]

    return jsonify({
        "message": "Student deleted successfully",
        "student": student
    }), 200
if __name__ == "__main__":
    app.run(debug=True)