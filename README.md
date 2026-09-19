# ExamCloud AI — Cloud-Based Online Examination System

Smarter Exams. Fairer Assessments. Better Learning.

ExamCloud AI is a full-stack, cloud-ready Online Examination and Assessment System built with **Python FastAPI**, **SQLAlchemy**, **Pydantic**, **HTML5**, **Vanilla CSS3**, and **Vanilla JavaScript**.

---

## 🌟 Features

### 👤 Role-Based Portals & Authorization
- **Admin**: System-wide dashboard, User management (Students/Teachers/Admins), Subject management, Exam monitor, and Audit logs.
- **Teacher**: Exam creation multi-step workflow, Question Builder with MCQ option management, Exam publishing/unpublishing, Class analytics, and Student submission reports.
- **Student**: Distraction-free live exam player, real-time timer countdown with autosave, automatic deadline enforcement, instant backend scoring breakdown, and score history.

### ⚙️ Core Technical Capabilities
- **RESTful Architecture**: Clean FastAPI endpoints with JSON schemas, OpenAPI documentation (`/docs`), and HTTP Bearer JWT security.
- **Dual Database Support**: Seamless switching between **SQLite** (`examcloud.db` for zero-configuration local development) and **PostgreSQL** (for production cloud deployments).
- **Backend Automatic Evaluation**: Server-side MCQ answer key comparison, formula calculation `(obtained / total) * 100`, pass/fail determination, and secure answer protection (answer keys are never exposed to student browsers).
- **Distraction-Free Exam Engine**: Countdown timer display, question navigation palette grid, answer status indicators (Answered, Unanswered, Current), and autosave indicators.

---

## 🚀 Quick Start Guide (Windows / Local Dev)

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Set Up Virtual Environment & Install Dependencies
Open PowerShell or Command Prompt in the project folder (`cloud-online-examination`):

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install required dependencies
pip install -r backend/requirements.txt
```

### 3. Initialize & Seed Database
The application includes an automatic seeding script that creates default accounts, subjects, sample exams, questions, and graded attempts:

```bash
python backend/seed.py
```

### 4. Launch Application
Run Uvicorn server:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Access the Platform
- **Landing Page & Portals**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔑 Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@examcloud.com` | `admin123` |
| **Teacher 1** | `teacher1@examcloud.com` | `teacher123` |
| **Teacher 2** | `teacher2@examcloud.com` | `teacher123` |
| **Student 1** | `student1@examcloud.com` | `student123` |
| **Student 2** | `student2@examcloud.com` | `student123` |

*(You can also register new student accounts directly on the registration page).*

---

## ☁️ Production / Cloud Deployment (PostgreSQL + Render / AWS / GCP / Azure)

### Environment Variables Configuration
In production, set the following environment variables on your cloud platform:

```env
DATABASE_URL=postgresql://username:password@your-postgres-host:5432/examination_db
SECRET_KEY=your-production-super-secret-jwt-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### Deployment Steps (Render Example)
1. Push repository to GitHub.
2. Create a new **Web Service** on Render.
3. Set Environment to **Python 3**.
4. Build Command: `pip install -r backend/requirements.txt`
5. Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. Attach a Render PostgreSQL Database and populate the `DATABASE_URL` environment variable.

---

## 📁 Project Structure

```
cloud-online-examination/
├── backend/
│   ├── main.py                   # FastAPI entry point & CORS
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment configuration
│   ├── seed.py                    # Database seeding script
│   ├── database/                  # SQLAlchemy engine & models
│   ├── schemas/                   # Pydantic request/response schemas
│   ├── routers/                   # REST API routes (auth, users, exams, attempts, results)
│   ├── services/                  # Business logic (auto-evaluator, exam logic)
│   └── utils/                     # JWT security & FastAPI dependencies
├── frontend/
│   ├── index.html                 # Main landing page
│   ├── login.html                 # Login portal
│   ├── register.html              # Student registration portal
│   ├── admin/                     # Admin dashboard & management pages
│   ├── teacher/                   # Teacher dashboard & exam builder pages
│   ├── student/                   # Student dashboard & live exam player
│   ├── css/                       # Design system stylesheets
│   └── js/                        # API client & interface controllers
└── README.md
```
