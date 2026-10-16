import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__, static_folder="scripts")
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-this-secret-key"),
    DATABASE=os.path.join(app.root_path, "students.db"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

COURSES = (
    "Computer Science",
    "Data Science",
    "Web Development",
    "Cybersecurity",
    "Business Administration",
    "Artificial Intelligence",
    "Cloud Computing",
    "Digital Marketing",
)
GENDERS = ("Female", "Male","None of the above")


@dataclass
class Student:
    id: int
    name: str
    email: str
    age: int
    gender: str
    course: str
    password: str

    @classmethod
    def from_row(cls, row):
        return cls(**dict(row))


@contextmanager
def get_db():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with get_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                age INTEGER NOT NULL,
                gender TEXT NOT NULL,
                course TEXT NOT NULL,
                password TEXT NOT NULL
            )
            """
        )


def get_student(student_id):
    with get_db() as connection:
        row = connection.execute(
            "SELECT id, name, email, age, gender, course, password "
            "FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()
    return Student.from_row(row) if row else None


@app.route("/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        age_input = request.form.get("age", "").strip()
        gender = request.form.get("gender", "")
        course = request.form.get("course", "")
        password = request.form.get("password", "")
        errors = []

        if not name:
            errors.append("Full name is required.")
        if not email or "@" not in email:
            errors.append("Enter a valid email address.")
        try:
            age = int(age_input)
            if age < 1:
                errors.append("Age must be a positive number.")
        except ValueError:
            age = 0
            errors.append("Age must be a number.")
        if gender not in GENDERS:
            errors.append("Choose a valid gender option.")
        if course not in COURSES:
            errors.append("Choose a valid course.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html", courses=COURSES, genders=GENDERS), 400

        try:
            with get_db() as connection:
                connection.execute(
                    "INSERT INTO students (name, email, age, gender, course, password) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        name,
                        email,
                        age,
                        gender,
                        course,
                        generate_password_hash(password),
                    ),
                )
        except sqlite3.IntegrityError:
            flash("An account with that email address already exists.", "error")
            return render_template("register.html", courses=COURSES, genders=GENDERS), 400
        except sqlite3.Error:
            app.logger.exception("Could not save student registration")
            flash("Registration could not be saved. Please try again.", "error")
            return render_template("register.html", courses=COURSES, genders=GENDERS), 500

        return redirect(url_for("success", name=name))

    return render_template("register.html", courses=COURSES, genders=GENDERS)


@app.get("/success")
def success():
    name = request.args.get("name", "")
    if not name:
        return redirect(url_for("register"))
    return render_template("success.html", name=name)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as connection:
            row = connection.execute(
                "SELECT id, password FROM students WHERE email = ?",
                (email,),
            ).fetchone()

        if row and check_password_hash(row["password"], password):
            session.clear()
            session["student_id"] = row["id"]
            return redirect(url_for("profile"))

        flash("Email or password is incorrect.", "error")

    return render_template("login.html")


@app.get("/profile")
def profile():
    student_id = session.get("student_id")
    if student_id is None:
        flash("Please log in to view your profile.", "info")
        return redirect(url_for("login"))

    student = get_student(student_id)
    if student is None:
        session.clear()
        flash("Your account could not be found. Please log in again.", "error")
        return redirect(url_for("login"))

    return render_template("profile.html", student=student, courses=COURSES)


@app.post("/update-course")
def update_course():
    student_id = session.get("student_id")
    if student_id is None:
        return jsonify(error="Please log in to update your course."), 401

    course = request.form.get("course", "")
    if course not in COURSES:
        return jsonify(error="Choose a valid course."), 400

    try:
        with get_db() as connection:
            result = connection.execute(
                "UPDATE students SET course = ? WHERE id = ?",
                (course, student_id),
            )
            if result.rowcount != 1:
                session.clear()
                return jsonify(error="Your account could not be found. Please log in again."), 404
    except sqlite3.Error:
        app.logger.exception("Could not update student course")
        return jsonify(error="Course could not be updated. Please try again."), 500

    return jsonify(course=course)


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


init_db()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
