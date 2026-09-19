import sys
import os
from datetime import datetime, timedelta

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.database import engine, SessionLocal, Base
from backend.database.models import User, Student, Teacher, Subject, Exam, Question, Option, ExamAttempt, Answer
from backend.utils.security import hash_password

def seed_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).filter(User.email == "admin@examcloud.com").first():
            print("Database already contains seed data.")
            return

        print("Seeding Users...")
        # Admin
        admin_user = User(
            name="Platform Admin",
            email="admin@examcloud.com",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        db.add(admin_user)

        # Teachers
        t1_user = User(
            name="Dr. Alan Turing",
            email="teacher1@examcloud.com",
            password_hash=hash_password("teacher123"),
            role="teacher"
        )
        t2_user = User(
            name="Prof. Ada Lovelace",
            email="teacher2@examcloud.com",
            password_hash=hash_password("teacher123"),
            role="teacher"
        )
        db.add_all([t1_user, t2_user])
        db.commit()

        t1_profile = Teacher(user_id=t1_user.id, department="Computer Science")
        t2_profile = Teacher(user_id=t2_user.id, department="Mathematics")
        db.add_all([t1_profile, t2_profile])

        # Students
        students_data = [
            ("Alex Johnson", "student1@examcloud.com", "CS-2026-001", "Computer Science", "3rd Year", "A"),
            ("Sophia Chen", "student2@examcloud.com", "CS-2026-002", "Computer Science", "3rd Year", "A"),
            ("Marcus Vance", "student3@examcloud.com", "MATH-2026-001", "Mathematics", "2nd Year", "B"),
            ("Elena Rostova", "student4@examcloud.com", "PHYS-2026-001", "Physics", "4th Year", "A"),
            ("David Miller", "student5@examcloud.com", "CS-2026-003", "Computer Science", "3rd Year", "B"),
        ]

        student_objs = []
        for name, email, roll, dept, yr, sec in students_data:
            u = User(
                name=name,
                email=email,
                password_hash=hash_password("student123"),
                role="student"
            )
            db.add(u)
            db.commit()
            s = Student(user_id=u.id, roll_number=roll, department=dept, year=yr, section=sec)
            db.add(s)
            student_objs.append(s)

        db.commit()

        print("Seeding Subjects...")
        sub1 = Subject(name="Computer Science", description="Software engineering, algorithms, web development, and cloud databases.")
        sub2 = Subject(name="Mathematics", description="Linear algebra, calculus, probability, and discrete structures.")
        sub3 = Subject(name="Physics", description="Classical mechanics, electromagnetism, and quantum fundamentals.")
        db.add_all([sub1, sub2, sub3])
        db.commit()

        print("Seeding Exams & Questions...")
        # Exam 1
        exam1 = Exam(
            title="Full Stack Web Development & Python Quiz",
            description="Comprehensive assessment covering Python FastAPI, REST architecture, SQLAlchemy ORM, and HTML5/JS integration.",
            subject_id=sub1.id,
            teacher_id=t1_profile.id,
            duration_minutes=45,
            total_marks=20.0,
            passing_percentage=50.0,
            start_time=datetime.utcnow() - timedelta(days=1),
            end_time=datetime.utcnow() + timedelta(days=14),
            status="published"
        )
        db.add(exam1)
        db.commit()

        questions_e1 = [
            ("Which HTTP method is typically used to create a new resource in a REST API?", 4.0, [
                ("GET", False), ("POST", True), ("PUT", False), ("DELETE", False)
            ]),
            ("What does ORM stand for in database architecture?", 4.0, [
                ("Object Relational Mapping", True),
                ("Operational Resource Model", False),
                ("Ordered Row Management", False),
                ("Online Repository Module", False)
            ]),
            ("In FastAPI, which library provides data validation and settings management using Python type annotations?", 4.0, [
                ("Django", False), ("Pydantic", True), ("Flask-Admin", False), ("Requests", False)
            ]),
            ("What is the default port used by Uvicorn server during FastAPI development?", 4.0, [
                ("3000", False), ("5000", False), ("8000", True), ("8080", False)
            ]),
            ("Which header is standard for transmitting JWT bearer authentication tokens?", 4.0, [
                ("Authorization", True), ("Authentication-Token", False), ("X-Access-Key", False), ("Content-Type", False)
            ]),
        ]

        for idx, (q_text, marks, opts) in enumerate(questions_e1, 1):
            q = Question(exam_id=exam1.id, question_text=q_text, marks=marks, question_order=idx)
            db.add(q)
            db.commit()
            for opt_text, is_corr in opts:
                db.add(Option(question_id=q.id, option_text=opt_text, is_correct=is_corr))

        # Exam 2
        exam2 = Exam(
            title="Linear Algebra & Matrix Fundamentals",
            description="Midterm test on matrix multiplication, eigenvalues, eigenvectors, and vector spaces.",
            subject_id=sub2.id,
            teacher_id=t2_profile.id,
            duration_minutes=30,
            total_marks=15.0,
            passing_percentage=60.0,
            start_time=datetime.utcnow() - timedelta(days=2),
            end_time=datetime.utcnow() + timedelta(days=7),
            status="published"
        )
        db.add(exam2)
        db.commit()

        questions_e2 = [
            ("What is the determinant of an identity matrix of size 3x3?", 5.0, [
                ("0", False), ("1", True), ("3", False), ("Undefined", False)
            ]),
            ("If matrix A is invertible, what is A multiplied by its inverse A⁻¹?", 5.0, [
                ("Zero Matrix", False), ("Identity Matrix", True), ("Transpose Matrix", False), ("Diagonal Matrix", False)
            ]),
            ("Vectors u and v are orthogonal if their dot product is equal to:", 5.0, [
                ("0", True), ("1", False), ("-1", False), ("Infinity", False)
            ]),
        ]

        for idx, (q_text, marks, opts) in enumerate(questions_e2, 1):
            q = Question(exam_id=exam2.id, question_text=q_text, marks=marks, question_order=idx)
            db.add(q)
            db.commit()
            for opt_text, is_corr in opts:
                db.add(Option(question_id=q.id, option_text=opt_text, is_correct=is_corr))

        db.commit()

        print("Seeding Sample Completed Attempts & Graded Results...")
        # Student 1 completed Exam 1 (Scored 20/20 = 100%)
        att1 = ExamAttempt(
            exam_id=exam1.id,
            student_id=student_objs[0].id,
            started_at=datetime.utcnow() - timedelta(hours=5),
            submitted_at=datetime.utcnow() - timedelta(hours=4),
            status="submitted",
            score=20.0,
            percentage=100.0
        )
        db.add(att1)

        # Student 2 completed Exam 1 (Scored 16/20 = 80%)
        att2 = ExamAttempt(
            exam_id=exam1.id,
            student_id=student_objs[1].id,
            started_at=datetime.utcnow() - timedelta(hours=3),
            submitted_at=datetime.utcnow() - timedelta(hours=2),
            status="submitted",
            score=16.0,
            percentage=80.0
        )
        db.add(att2)

        # Student 3 completed Exam 2 (Scored 10/15 = 66.67%)
        att3 = ExamAttempt(
            exam_id=exam2.id,
            student_id=student_objs[2].id,
            started_at=datetime.utcnow() - timedelta(hours=2),
            submitted_at=datetime.utcnow() - timedelta(hours=1),
            status="submitted",
            score=10.0,
            percentage=66.67
        )
        db.add(att3)

        db.commit()
        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
