# 🏛️ SYSTEM ARCHITECTURE SPECIFICATION (SPRINT 9)
## **GEN'X VISION SCHOOL SYSTEM — ERP & CAMPUS MANAGEMENT PLATFORM**
**Version:** 9.0 — Multi-Campus, Online CBT Engine, QR Verification & Executive Analytics  
**Date:** September 2026 | **Author:** Lead Systems Architect & AI Engineering Team  

---

## 1. Executive Summary & Architectural Scope

Sprint 9 expands the core School Management ERP into an **Enterprise-Grade Distributed Campus Platform**. It introduces four fundamental subsystems:
1. **Multi-Branch & Campus Multi-Tenancy Architecture:** Context-aware switching across multiple campus locations (e.g. *Main Campus*, *Girls Wing*, *Junior Branch*).
2. **Online Computer-Based Testing (CBT) & Assessment Engine:** Timed digital tests with MCQs, True/False, auto-shuffling, instant auto-grading, and result feedback.
3. **Dynamic QR Code Security & Badge Verification Gateway:** High-speed mobile/tablet gatekeeper portal to scan PVC student/staff badge QR tokens for real-time authentication.
4. **Executive Leadership & Revenue Forecast Analytics:** Multi-campus profit/loss analytics, fee recovery forecasts, and academic pass-rate matrices.

```mermaid
flowchart TD
    subgraph Enterprise Core
        DB[(PostgreSQL / SQLite Central Database)]
        AUTH[Role-Based Authentication & Permissions]
        SETTINGS[School Branding & Global Configuration]
    end

    subgraph Sprint 9 Subsystems
        CAMPUS[Multi-Branch & Campus Management]
        CBT[Online CBT Examination Engine]
        QR[QR Gatekeeper & Badge Verification]
        BI[Executive KPI & Financial Forecast Hub]
    end

    AUTH --> CAMPUS
    CAMPUS --> DB
    CBT --> DB
    QR --> DB
    BI --> DB

    STUDENT((Student / Parent)) --> CBT
    STUDENT --> QR
    STAFF((Faculty / Examiner)) --> CBT
    GUARD((Gatekeeper / Security)) --> QR
    DIRECTOR((Executive Leadership / Admin)) --> CAMPUS
    DIRECTOR --> BI
```

---

## 2. Component Subsystems & Database Models

### 2.1 Multi-Campus & Branch Management (`apps/core/models.py`)

```mermaid
erDiagram
    Branch ||--o{ Student : "enrolled in"
    Branch ||--o{ Teacher : "assigned to"
    Branch ||--o{ ClassRoom : "operates"
    Branch ||--o{ FeeInvoice : "bills"
    Branch ||--o{ Expense : "incurs"

    Branch {
        int id PK
        string name "e.g. Main Campus Johar Town"
        string code "e.g. GXV-MC01"
        string campus_type "MAIN, JUNIOR, GIRLS_WING, BOYS_WING"
        string address
        string city
        string phone
        string email
        string principal_name
        boolean is_main_branch
        boolean is_active
    }
```

- **Campus Context Middleware:** Determines active branch from user session or URL query (`?branch_id=X`). Admins can toggle between all branches or view consolidated group metrics.

---

### 2.2 Online CBT & Assessment Engine (`apps/examinations/models.py`)

```mermaid
erDiagram
    ClassRoom ||--o{ OnlineAssessment : "targets"
    Subject ||--o{ OnlineAssessment : "belongs to"
    OnlineAssessment ||--o{ AssessmentQuestion : "contains"
    OnlineAssessment ||--o{ StudentAssessmentAttempt : "attempted by"
    Student ||--o{ StudentAssessmentAttempt : "submits"

    OnlineAssessment {
        int id PK
        string title "e.g. Mid-Term Physics CBT Quiz"
        int duration_minutes "e.g. 45"
        decimal total_marks "e.g. 50.00"
        decimal passing_percentage "e.g. 40.00"
        datetime start_window
        datetime end_window
        boolean shuffle_questions
        boolean show_immediate_result
        string status "DRAFT, PUBLISHED, ARCHIVED"
    }

    AssessmentQuestion {
        int id PK
        int online_assessment_id FK
        string question_text
        string question_type "MCQ, TRUE_FALSE, SHORT_TEXT"
        string option_a
        string option_b
        string option_c
        string option_d
        string correct_answer "A, B, C, D, TRUE, FALSE"
        decimal marks "e.g. 2.00"
        string explanation
        int order_num
    }

    StudentAssessmentAttempt {
        int id PK
        int online_assessment_id FK
        int student_id FK
        datetime started_at
        datetime submitted_at
        decimal total_score
        decimal percentage
        boolean is_passed
        json answers_payload
        string status "IN_PROGRESS, SUBMITTED, EVALUATED"
    }
```

---

### 2.3 QR Code Gatekeeper & Identity Verification (`apps/students/` & `apps/teachers/`)

```mermaid
sequenceDiagram
    autonumber
    actor Guard as Security Guard / Gatekeeper (Mobile Device)
    participant Portal as QR Badge Verification Portal
    participant DB as Central Database
    participant Student as Student / Faculty Record

    Guard->>Portal: Scans Badge QR Code (/verify-badge/<token>/)
    Portal->>DB: Lookup dynamic security token & active enrollment
    alt Token Valid & Active
        DB-->>Portal: Returns Verified Student Profile (Photo, Roll #, Class, Blood Group, Emergency Phone)
        Portal-->>Guard: Displays Green "VERIFIED & VALID" Badge with Guardian Contact
    else Token Inactive or Revoked
        DB-->>Portal: Status: Inactive / Suspended / Invalid
        Portal-->>Guard: Displays Red "ALERT: INVALID OR EXPIRED BADGE"
    end
```

---

## 3. Workflows & Sequence Pipelines

### 3.1 Student Online CBT Exam Taking & Auto-Grading Flow

```mermaid
flowchart TD
    A[Student logs into Student Portal] --> B[Navigates to Active Online Quizzes]
    B --> C{Exam Window Active & Not Attempted?}
    C -- No --> D[Show Closed / Already Submitted Status]
    C -- Yes --> E[Click Start Assessment & Launch Fullscreen Interface]
    E --> F[Client-Side Countdown Timer & Question Stepper]
    F --> G[Student selects Answers A, B, C, D]
    G --> H[Submit Exam / Auto-Submit on Timeout]
    H --> I[Backend Auto-Grading Engine compares answers against Key]
    I --> J[Compute Total Score, Percentage & Pass/Fail Status]
    J --> K[Persist Attempt Record in Database & Log Activity]
    K --> L[Render Instant Scorecard & Correct Answers Review]
```

---

## 4. API Endpoints & Routing Architecture

| Module | Route | HTTP Verb | Access Role | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Campuses** | `/campuses/` | GET, POST | Admin, Owner | List all school branches & create new campus |
| **Campuses** | `/campuses/switch/<id>/` | GET | Admin, Principal | Switch active campus session context |
| **CBT Quizzes**| `/examinations/cbt/` | GET | Teacher, Admin, Student | List all online quizzes & assessments |
| **CBT Quizzes**| `/examinations/cbt/create/` | GET, POST | Teacher, Admin | Build timed quiz & set question parameters |
| **CBT Quizzes**| `/examinations/cbt/<id>/questions/`| GET, POST | Teacher, Admin | Add and manage MCQs & answer keys |
| **CBT Quizzes**| `/examinations/cbt/<id>/take/` | GET, POST | Student, Parent | Interactive timed test interface with auto-grading |
| **CBT Quizzes**| `/examinations/cbt/<id>/results/` | GET | Teacher, Admin | Cohort exam performance, rankings & analytics |
| **QR Verify** | `/verify-badge/<token>/` | GET | Public / Gatekeeper | Mobile-responsive badge scanner & verification |
| **Analytics** | `/reports/executive/` | GET | Admin, Owner | Multi-campus financial forecasts & pass-rate KPI hub |

---

## 5. Security, RBAC & Multi-Tenancy Isolation

1. **Branch-Level Data Filtering:** Queries automatically respect active branch scope when scoped to a specific campus.
2. **CBT Anti-Cheat & Integrity Controls:**
   - Single submission constraint (`unique_together = ('online_assessment', 'student')`).
   - Server-side deadline verification (submissions rejected if timestamp exceeds `end_window + grace_period`).
   - Random question order shuffling per student attempt.
3. **QR Token Cryptographic Signatures:** Verification tokens are generated using unique UUIDs / HMAC hashes to prevent forged URLs.

---

## 6. QA Verification Matrix & Acceptance Criteria

- [x] Multi-Campus CRUD and session switcher works across all modules.
- [x] Online CBT assessment can be created with 5+ MCQs.
- [x] Student takes timed test with countdown timer and submits successfully.
- [x] Auto-grading computes exact percentage, score, and pass/fail grade instantly.
- [x] QR Badge URL `/verify-badge/<token>/` renders valid badge with student photo and emergency contact.
- [x] Executive Dashboard computes multi-branch profit/loss, fee collections, and student enrollment trends.
- [x] 100% regression passing across Sprints 0 through 8.
