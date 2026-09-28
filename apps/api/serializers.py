from rest_framework import serializers
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import ClassRoom, Section, Subject
from apps.attendance.models import StudentAttendance
from apps.lectures.models import DailyLecture, Homework
from apps.fees.models import FeeInvoice
from apps.examinations.models import Exam, ExamStudentResult
from apps.communication.models import Announcement


class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='current_class.name', read_only=True)
    section_name = serializers.CharField(source='current_section.name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'id', 'admission_number', 'first_name', 'last_name',
            'gender', 'date_of_birth', 'class_name', 'section_name',
            'guardian_name', 'guardian_phone', 'status', 'created_at'
        ]


class TeacherSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    designation_display = serializers.CharField(source='get_designation_display', read_only=True)

    class Meta:
        model = Teacher
        fields = [
            'id', 'employee_id', 'full_name', 'designation', 'designation_display',
            'department', 'qualification', 'phone_number', 'status'
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    admission_number = serializers.CharField(source='student.admission_number', read_only=True)

    class Meta:
        model = StudentAttendance
        fields = ['id', 'date', 'student_name', 'admission_number', 'status', 'remarks']


class HomeworkSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    class_name = serializers.CharField(source='class_room.name', read_only=True)

    class Meta:
        model = Homework
        fields = ['id', 'title', 'subject_name', 'class_name', 'description', 'assigned_date', 'due_date', 'status']


class FeeInvoiceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_room.name', read_only=True)

    class Meta:
        model = FeeInvoice
        fields = [
            'id', 'invoice_number', 'student_name', 'class_name', 'fee_month',
            'payable_amount', 'paid_amount', 'balance_amount', 'status', 'due_date'
        ]


class ExamResultSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    exam_title = serializers.CharField(source='exam.title', read_only=True)

    class Meta:
        model = ExamStudentResult
        fields = [
            'id', 'student_name', 'exam_title', 'total_marks',
            'obtained_marks', 'percentage', 'grade', 'is_passed', 'position_in_class'
        ]


class AnnouncementSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'content', 'priority', 'audience', 'publish_date', 'author_name', 'is_published']
