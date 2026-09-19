from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import Exam, ExamAttempt, Student

def can_student_take_exam(student_id: int, exam_id: int, db: Session):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        return False, "Exam does not exist"
    
    if exam.status != "published":
        return False, "Exam is not currently published"

    now = datetime.utcnow()
    if exam.start_time and now < exam.start_time:
        return False, f"Exam starts at {exam.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    if exam.end_time and now > exam.end_time:
        return False, "Exam deadline has passed"

    existing_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == student_id,
        ExamAttempt.exam_id == exam_id
    ).first()

    if existing_attempt:
        if existing_attempt.status == "submitted":
            return False, "You have already completed and submitted this exam"
        elif existing_attempt.status == "in_progress":
            return True, "Resuming existing active attempt"

    return True, "Eligible to start exam"
