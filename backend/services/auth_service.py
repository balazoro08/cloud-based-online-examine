from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import User, Student, Teacher
from backend.utils.security import hash_password

def register_student_user(user_data, db: Session) -> User:
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ValueError("Email is already registered")

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="student"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    student_profile = Student(
        user_id=user.id,
        roll_number=user_data.roll_number,
        department=user_data.department,
        year=user_data.year,
        section=user_data.section
    )
    db.add(student_profile)
    db.commit()
    db.refresh(user)
    return user

def create_user_by_admin(user_data, db: Session) -> User:
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise ValueError("Email is already registered")

    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if user_data.role == "teacher":
        teacher_profile = Teacher(
            user_id=user.id,
            department=user_data.department or "General"
        )
        db.add(teacher_profile)
    elif user_data.role == "student":
        student_profile = Student(
            user_id=user.id,
            roll_number=user_data.roll_number or f"STU-{user.id:04d}",
            department=user_data.department or "General"
        )
        db.add(student_profile)
    
    db.commit()
    db.refresh(user)
    return user
