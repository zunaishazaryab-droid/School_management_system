import datetime
import random
from apps.students.models import Student
from apps.attendance.models import StudentAttendance
from apps.accounts.models import User

def seed_full_year_attendance():
    superuser = User.objects.filter(is_superuser=True).first() or User.objects.first()
    students = list(Student.objects.filter(status='ACTIVE'))
    if not students:
        print("No active students found!")
        return

    start_date = datetime.date(2026, 4, 1)
    end_date = datetime.date(2026, 10, 7)

    # Pakistani holidays / summer vacation notes
    holidays = {
        datetime.date(2026, 5, 1): "Labour Day Holiday",
        datetime.date(2026, 8, 14): "Independence Day Celebration & Holiday",
        datetime.date(2026, 9, 6): "Defence Day Observance",
    }

    total_created = 0
    total_updated = 0

    cur_date = start_date
    while cur_date <= end_date:
        # Skip Sundays (weekday 6)
        if cur_date.weekday() == 6:
            cur_date += datetime.timedelta(days=1)
            continue

        is_holiday = cur_date in holidays
        holiday_name = holidays.get(cur_date)

        for student in students:
            # Seed pseudo-random reproducible status based on student.id + date
            seed_val = (student.id * 1000) + cur_date.toordinal()
            rnd = random.Random(seed_val)

            if is_holiday:
                # Holidays marked as absent / leave
                status = StudentAttendance.Status.ABSENT
                remarks = f"School Closed: {holiday_name}"
            else:
                # 92% Present, 4% Late, 4% Absent
                roll = rnd.randint(1, 100)
                if roll <= 92:
                    status = StudentAttendance.Status.PRESENT
                    punch_hour = rnd.choice([7, 7, 7, 7])
                    punch_min = rnd.randint(40, 58)
                    punch_sec = rnd.randint(10, 59)
                    term = rnd.choice(["Main Gate Turnstile Terminal #1", "Junior Wing RFID Terminal #2", "Biometric Facial Scanner #1"])
                    remarks = f"Biometric Punch @ {punch_hour:02d}:{punch_min:02d}:{punch_sec:02d} via {term}"
                elif roll <= 96:
                    status = StudentAttendance.Status.LATE
                    punch_hour = 8
                    punch_min = rnd.randint(8, 25)
                    remarks = f"Late Check-in @ {punch_hour:02d}:{punch_min:02d} AM — Traffic / Transport Delay"
                else:
                    status = StudentAttendance.Status.ABSENT
                    abs_reasons = [
                        "Absent — Sick Leave Application on File",
                        "Absent — Domestic Event / Urgent Family Matter",
                        "Uninformed Absence — SMS Dispatched to Guardian",
                        "Absent — Doctor Appointment"
                    ]
                    remarks = rnd.choice(abs_reasons)

            obj, created = StudentAttendance.objects.update_or_create(
                student=student,
                date=cur_date,
                defaults={
                    'class_room': student.current_class,
                    'section': student.current_section,
                    'status': status,
                    'remarks': remarks,
                    'recorded_by': superuser,
                }
            )
            if created:
                total_created += 1
            else:
                total_updated += 1

        cur_date += datetime.timedelta(days=1)

    print(f"Done! Created: {total_created}, Updated: {total_updated} attendance records for {len(students)} students across full academic year.")

if __name__ == "__main__":
    seed_full_year_attendance()
