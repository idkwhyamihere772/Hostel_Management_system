# 🏢 Hostel & PG Management System

A modern, full-stack accommodation portal built with **FastAPI**, **MongoDB Atlas**, and vanilla **HTML/CSS/JavaScript**. Designed to help students discover verified hostels and PGs while enabling property owners to list their accommodations and manage inquiries.

---

## 🌟 Key Features

- **🏢 Public Accommodation Directory**:
  - Live accommodation counters (Total, Boys, Girls & Co-ed).
  - Filter chips for instant categorization (Boys Hostels, Girls Hostels, Co-ed / Mixed).
  - Search by hostel name, location, owner, or amenities (WiFi, AC, Food, CCTV, etc.).
  - Detailed rent cards with Single vs. Double Sharing pricing and direct contact actions.

- **🔒 Privacy-First User Architecture**:
  - Student profiles are kept private in the database (`MAIN.User`) rather than displayed publicly on the website.
  - Students register, log in, and view their personal college, budget, and sharing preferences securely.

- **🛡️ Role-Based Access Control (RBAC)**:
  - **Students**: Private account access, personalized budget & college settings.
  - **Hostel Owners**: Property listings with amenities, rent details, and caretaker contact info.
  - **Administrators**: Password-gated superuser controls (`admin` / `admin123`) for direct data management and deletions.

- **🔐 Robust Security**:
  - **Bcrypt**: One-way salt hashing for passwords.
  - **JWT (JSON Web Tokens)**: Stateless Bearer authentication (`HS256`) for session management.
  - **Protected Endpoints**: Dependency-injected role verification for sensitive operations (`DELETE /user/{username}`).

- **📖 Auto-Generated API Documentation**:
  - Built-in Swagger UI at `/docs` and ReDoc at `/redoc`.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **Database**: MongoDB Atlas (Cloud NoSQL)
- **Security**: Passlib (Bcrypt), PyJWT, Python-Multipart
- **Frontend**: Vanilla HTML5, CSS3 (Modern Glassmorphism & Responsive Design), Vanilla JavaScript (Fetch API)

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/hostel-pg-management.git
cd hostel-pg-management
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` with your credentials:
```env
mongo_uri=your_mongodb_atlas_connection_string
secret_key=your_secret_jwt_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

### 4. Run the Application
```bash
python -m uvicorn main:app --reload --port 8000
```

- Open the Web App: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Open Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves the frontend web app | No |
| `GET` | `/User` | List all registered records | No |
| `POST` | `/register` | Register a new user (student / hostel) | No |
| `POST` | `/login` | Authenticate and obtain JWT Bearer token | No |
| `GET` | `/me` | Get authenticated user profile | Yes (Bearer Token) |
| `PUT` | `/student/{username}` | Update student details | No |
| `PUT` | `/hostel/{username}` | Update hostel listing | No |
| `DELETE` | `/user/{username}` | Delete record from database | Yes (Admin or Owner) |

---

## ☁️ Deployment

This project can be easily deployed to **Render**, **Railway**, or **Koyeb**:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables**: Add `mongo_uri`, `secret_key`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in your deployment dashboard.

---

## 📄 License
MIT License
