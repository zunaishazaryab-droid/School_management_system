SOFTWARE REQUIREMENTS SPECIFICATION

School Management Software

Version 2.0 — Complete System + Frontend/UI Specification

Reference: the supplied SchoolMarkaz demo is used only as a high-level frontend/workflow reference. The system will use its own branding, UI and implementation.

Current scope: biometric attendance and WhatsApp API automation are deferred to a future phase.

## 1. Introduction

### 1.1 Purpose

This SRS defines the functional, frontend, backend, database, security, reporting and workflow requirements for a professional School Management Software system. It centralizes students, teachers, attendance, academics, fees, examinations, timetable, expenses, communication and reports.

### 1.2 Objectives

- Replace manual registers and scattered spreadsheets.
- Provide a modern, clean and easy-to-use dashboard.
- Use role-based access for Owner/Admin, Principal, Coordinator and Teacher.
- Make daily tasks fast: search student, attendance, fee collection, lecture/homework and marks.
- Provide PDF and Excel reports.
- Scale from about 160 students to 500–1,000+.
- Remain ready for future biometric, WhatsApp/SMS, parent portal, transport, library and mobile features.
## 2. Scope


| Area | Version 2.0 |
| --- | --- |
| Students | Included |
| Teachers/Staff | Included |
| Classes/Sections/Subjects | Included |
| Manual Attendance | Included |
| Biometric Attendance | Deferred |
| Lectures/Syllabus/Homework | Included |
| Fees/Receipts/Ledger | Included |
| Exams/Results | Included |
| Timetable | Included |
| Expenses | Included |
| Manual Communication | Included |
| WhatsApp API | Deferred |
| Performance/Reports/Search | Included |
| Audit/Backup/Security | Included |

## 3. Users and Roles


| Role | Main Access |
| --- | --- |
| Owner/Admin | Full system, users, settings, finance, reports, audit and backup. |
| Principal | Dashboard, students, teachers, attendance, academics, exams and reports. |
| Coordinator | Classes, sections, timetable, attendance, syllabus, homework and selected reports. |
| Teacher | Assigned classes/subjects, attendance, lectures, syllabus, homework, marks and own performance. |

## 4. Frontend / UI Design Requirements

The frontend should have the modern dashboard-first experience seen in the supplied SchoolMarkaz demo: clear navigation, summary cards, data tables, forms, reports and role-specific workflows. This is a design direction, not a requirement to copy the product.

### 4.1 Visual Style

- Modern professional school ERP appearance.
- Clean light interface with consistent primary brand color and accent.
- Rounded cards, readable typography, spacing and simple icons.
- Responsive on desktop, laptop, tablet and mobile.
- Tables with search, filters, pagination and actions.
- Forms divided into logical sections.
- Confirmation dialogs for destructive actions.
- Success/error/warning notifications.
- Simple enough for non-technical school staff.
### 4.2 Main Layout

- Left sidebar: Dashboard, Students, Teachers/Staff, Classes, Attendance, Academics, Homework, Fees, Exams & Results, Timetable, Expenses, Communication, Performance, Reports, Notifications, Activity Log, Settings.
- Top bar: global search, notifications, current user/role, profile and logout.
- Main area: page title, breadcrumb, filters/actions and content.
- Collapsible sidebar on small screens.
- Role-based navigation so users only see permitted modules.
### 4.3 Login

- School logo/system name.
- Username/email and password.
- Show/hide password.
- Remember me.
- Forgot/reset password.
- Clear validation errors.
- Secure session and logout.
### 4.4 Dashboard


| Component | Information |
| --- | --- |
| Students | Total students + quick link |
| Teachers | Total teachers/staff |
| Today's Attendance | Present, absent, late |
| Teacher Attendance | Today's teacher summary |
| Fee Collection | Today/month collection |
| Pending Fees | Outstanding dues/defaulters |
| Expenses | Today/month expenses |
| Syllabus | Overall completion % |
| Homework | Recent/pending |
| Recent Activities | Latest important actions |
| Notifications | Important reminders |

### 4.5 Dashboard Arrangement

- Top: 4–6 KPI cards.
- Middle: attendance, fee, expense and syllabus summaries.
- Lower: recent activity, pending fees, upcoming exams and homework.
- Quick actions: Add Student, Mark Attendance, Collect Fee, Add Lecture, Add Homework, Enter Marks.
- Charts must remain readable and not overload the page.
## 5. Frontend Screen Inventory


| Module | Screens |
| --- | --- |
| Authentication | Login, Forgot Password, Reset Password, Profile |
| Dashboard | Role-specific dashboards |
| Students | List, Add, Edit, Profile, Academic History, Attendance, Fees, Results, Documents, Promotion |
| Teachers | List, Add, Edit, Profile, Attendance, Classes/Subjects, Salary/Advances/Deductions, Performance |
| Classes | Classes, Sections, Subjects, Assignments |
| Attendance | Daily student/teacher attendance, history, monthly reports |
| Lectures | List, Add/Edit, Details |
| Syllabus | Class→Subject→Chapter→Topic, progress |
| Homework | Create, list, history, diary |
| Fees | Types, setup, ledger, collection, receipts, dues, defaulters |
| Exams | Setup, date sheet, marks, grades, results, report cards |
| Timetable | Class, teacher, periods |
| Expenses | Entry, categories, daily/monthly/annual reports |
| Communication | Manual messages, announcements, history |
| Performance | Teacher performance dashboard/details |
| Reports | Filtered PDF/Excel report center |
| Notifications | System alerts |
| Audit | Activity log |
| Settings | School, academic year, users, roles, permissions, backup/security |

## 6. Student Management

- Admission/student ID, name, guardian, optional CNIC, contact/WhatsApp, DOB, gender, address, class, section, admission date and previous school.
- Photo, medical/emergency information and documents.
- Optional biometric ID field reserved for future.
- Profile tabs: Overview, Academic, Attendance, Fees, Exams/Results, Homework, Documents, Remarks, Promotion History.
- Search by name, ID, guardian, phone, class or section.
- Printable student card/profile.
- Promotion workflow.
## 7. Teacher & Staff Management

- ID, name, contact, qualification, experience, joining date and assigned classes/subjects.
- Salary, advances, deductions and leave.
- Attendance/monthly history.
- Performance based on attendance, punctuality, lectures, syllabus, homework, copies and results.
- Teacher profile with timetable/workload.
## 8. Classes, Sections & Academic Structure

- Classes and sections CRUD.
- Class teacher assignment.
- Subjects and teacher assignment.
- Academic year management.
- Validation for conflicting assignments.
## 9. Attendance — Manual in Version 2.0

- Select date, class and section.
- Register with Present/Absent/Late.
- Bulk marking and individual correction.
- Save date/time metadata.
- History and monthly percentage.
- Teacher attendance and monthly reports.
- Biometric integration deferred.
## 10. Daily Lecture Records

- Date, class, section, subject, chapter, topic, objectives, classwork, homework.
- Present/absent counts, copies checked and remarks.
- Searchable lecture history.
- Use data for syllabus and teacher performance.
## 11. Syllabus Tracking

- Hierarchy: Class → Subject → Chapter → Topic.
- Statuses: Not Started, In Progress, Completed.
- Automatic completion percentage.
- Reports by class, subject and teacher.
- Dashboard progress indicator.
## 12. Homework / Diary

- Create by class, section and subject.
- Title, description, assigned date and due date.
- Teacher history.
- Future parent/student viewing.
- Contributes to performance monitoring.
## 13. Fee Management

- Admission, monthly, annual, exam, transport and other fee types.
- Discount, fine, previous dues, paid and remaining.
- Jan–Dec history.
- Student ledger.
- Payment collection and printable receipt.
- Pending/defaulter list.
- Daily/monthly reports.
- PDF receipt and PDF/Excel reports.
- Future online payment gateway.
## 14. Exams & Results

- Exam types and schedules.
- Subject total/obtained marks.
- Percentage and grade.
- Position where required by school rules.
- Remarks and result history.
- Printable report card.
- Class performance analytics.
## 15. Timetable

- Period setup.
- Class-wise timetable.
- Teacher-wise timetable.
- Subject/teacher allocation.
- Conflict validation.
- Printable timetable.
## 16. Expenses & Finance

- Salary, electricity, rent, stationery, maintenance, furniture, transport, events and other categories.
- Daily/monthly/annual records.
- Income vs expense.
- Category-wise reports.
- Permission-controlled finance access.
## 17. Parent Communication

- Manual individual, class/section and all-school messages.
- Message history/status.
- Templates for absence, fee reminder, homework, result and announcement.
- WhatsApp/SMS API automation deferred.
## 18. Teacher Performance

- Attendance/punctuality.
- Lecture completion.
- Syllabus completion.
- Homework.
- Copies checked.
- Result indicators.
- Leave.
- Coordinator/Principal remarks.
- Monthly/term summary.
## 19. Reports Center

- Student list/profile.
- Student and teacher attendance.
- Fee collection, pending fees, defaulters and ledgers.
- Exam/result/report cards.
- Syllabus and homework/lecture reports.
- Teacher performance.
- Expense and income-vs-expense.
- Timetable.
- Filters by date, class, section, subject and teacher.
- PDF and Excel export where applicable.
## 20. Search & Notifications

- Global search in top bar.
- Search student, teacher, class, ledger, receipt and permitted records.
- Alerts for pending fees, attendance issues, exams and incomplete syllabus.
- Respect role permissions.
## 21. Activity / Audit Log

- Record important create/update/delete, login/logout and financial actions.
- Store user, action, module, record reference and timestamp.
- Authorized roles only.
- Avoid unnecessary personal data in logs.
## 22. Database Requirements

Recommended production stack: Django + PostgreSQL.

- Users/Roles/Permissions
- Students/Guardians/Documents
- Teachers/Staff/Salary/Leave
- Academic Years/Classes/Sections/Subjects/Assignments
- Student/Teacher Attendance
- Lectures/Syllabus/Homework
- Fee Types/Assignments/Payments/Ledgers/Receipts
- Exams/Marks/Grades/Results
- Timetable/Periods
- Expenses/Categories
- Messages/Announcements/Notifications
- Performance
- Audit Logs
- Settings/Backups
## 23. Backend/API Requirements

- Modular Django apps.
- Role-based authorization for every protected action.
- Server-side validation.
- Pagination/filter/search.
- Atomic transactions for financial operations.
- Secure document handling.
- Separation of business logic, models, views/API and templates/components.
- Keep REST API readiness for future mobile apps.
## 24. Security

- Django secure authentication/password hashing.
- Role/permission checks.
- CSRF and secure sessions.
- Input validation/output escaping.
- Restricted financial/personal records.
- Secure uploads.
- Audit trail.
- Scheduled backups and tested restore.
- Secrets/API keys in environment variables.
- HTTPS in production.
## 25. Non-Functional Requirements


| Requirement | Target |
| --- | --- |
| Usability | Easy for non-technical staff |
| Responsive UI | Desktop/tablet/mobile |
| Performance | Fast common dashboard/list actions |
| Scalability | ~160 to 500–1,000+ students |
| Reliability | Consistent transactions/records |
| Maintainability | Modular Django structure |
| Security | Authenticated, authorized, audited |
| Backup | Scheduled and tested restore |
| Accessibility | Readable, clear, practical keyboard support |

## 26. Key Workflows

1. Login → role → dashboard.
1. Add Student → class/section → profile.
1. Attendance → class/section → statuses → save → history.
1. Lecture → class/subject → topic/classwork/homework → save.
1. Syllabus → topic status → percentage updates.
1. Fee → assign → collect → receipt → ledger.
1. Exam → marks → percentage/grade → report card.
1. Expense → category + amount → save → finance report.
1. Announcement → audience → publish → history.
1. Reports → report + filters → preview → PDF/Excel.
## 27. Reusable Frontend Components

- Button, Input, Select, DatePicker, SearchBox, Table, Modal, Card, Badge, Tabs, Pagination, Alert.
- Consistent Add/Edit/Delete actions.
- Status badges: Present/Absent/Late, Paid/Pending, Completed/In Progress/Not Started.
- Empty states and loading states.
- Inline validation.
- Responsive tables/card view on small screens.
## 28. Recommended Build Order

1. Project setup, database and theme.
1. Authentication, roles and permissions.
1. Main layout: sidebar, topbar, dashboard cards and responsive shell.
1. Classes, sections, subjects and academic year.
1. Student and teacher management.
1. Manual attendance.
1. Lectures, syllabus and homework.
1. Fees, ledgers and receipts.
1. Exams, marks and report cards.
1. Timetable and expenses.
1. Communication, notifications and teacher performance.
1. Reports, PDF/Excel, search and audit.
1. Security, backup, testing and UI polishing.
1. Future biometric + WhatsApp/SMS + portals/mobile apps.
## 29. Acceptance Criteria

- Authorized users can log in and access only permitted modules.
- Student/teacher records can be created, edited, searched and viewed.
- Attendance and history work.
- Lectures, syllabus and homework work.
- Fees can be assigned, collected, receipted and tracked.
- Exams/results/report cards work.
- Timetable and expenses work.
- Reports filter/export.
- Important actions are logged.
- Responsive desktop/mobile UI.
- One consistent database.
- Backup/restore procedure available.
- Biometric and WhatsApp are not required for Version 2.0 acceptance.
## 30. Future Expansion

- Fingerprint/biometric attendance.
- Automatic WhatsApp/SMS.
- Parent portal/mobile app.
- Student portal.
- Teacher mobile app.
- Online payments.
- Transport.
- Library.
- Inventory.
- Online tests/assignments.
- Digital report cards.
- Multi-branch.
- Advanced analytics.
## 31. UI/UX Reference Note

The supplied SchoolMarkaz demo is used as a reference for the desired type of school-management experience: dashboard-first navigation, quick access to students, attendance, fees, exams/results, reports and role-oriented workflows. The public product description also highlights admin, teacher, student and parent-oriented interfaces plus dashboard, student-record and reports previews. The project must use original branding and UI, not copy proprietary code or exact visual assets.

## 32. Technology Recommendation


| Layer | Recommendation |
| --- | --- |
| Backend | Python + Django |
| Database | PostgreSQL |
| Frontend | Django Templates + responsive CSS/JS; separate frontend later if needed |
| Auth | Django Authentication + roles/permissions |
| Reports | PDF + Excel |
| Deployment | Cloud or local school server |
| Version Control | Git + GitHub/GitLab |
| Future API | Django REST Framework |

## 33. Conclusion

This Version 2.0 SRS combines the original school-management requirements with a dedicated frontend/UI specification based on the supplied demo direction. Development should be done module-by-module in Antigravity/VS Code, not with one giant prompt. The interface should be modern, professional and easy for school staff. Biometric and WhatsApp automation remain future modules so the core system can be completed and tested first.
