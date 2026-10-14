import os
import wave
import struct
import math
import datetime
from django.core.files import File
from apps.academics.models import ClassRoom, Section, Subject
from apps.accounts.models import User
from apps.lectures.models import DailyLecture
from django.conf import settings

def create_sample_wav(filename, duration_sec=3, freq=440.0):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    sample_rate = 16000
    num_samples = int(duration_sec * sample_rate)
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            # Gentle soft sine tone with fade out
            t = float(i) / sample_rate
            value = int(math.sin(2.0 * math.pi * freq * t) * 10000.0 * max(0.0, (1.0 - t / duration_sec)))
            data = struct.pack('<h', value)
            wav_file.writeframesraw(data)

def seed_sample_class_lectures():
    teacher_user = User.objects.filter(role='TEACHER').first() or User.objects.filter(is_superuser=True).first() or User.objects.first()
    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()

    if not classes.exists() or not subjects.exists():
        print("Classes or subjects missing.")
        return

    media_root = settings.MEDIA_ROOT
    demo_audio_path = os.path.join(media_root, 'lecture_recordings', 'sample_voice_lecture.wav')
    create_sample_wav(demo_audio_path, duration_sec=5, freq=520.0)

    sample_topics = [
        ("Mathematics", "Chapter 4: Quadratic Equations", "Derivation of Quadratic Formula & Completing Square", "Solved textbook exercises 4.1 questions 1 to 6 on board.", "Practice exercise 4.1 remaining questions in homework notebook."),
        ("English A", "Unit 2: The Daffodils by William Wordsworth", "Stanza Paraphrasing & Figures of Speech", "Detailed explanation of central theme and imagery in lines 1-12.", "Write summary and central idea of the poem in diary notebook."),
        ("General Science", "Chapter 3: Human Nervous System", "Reflex Actions and Structure of Brain", "Diagram of Neuron drawn on whiteboard, explained synapse transmission.", "Draw labeled diagram of Brain and define Cerebrum & Cerebellum."),
        ("Computer Science", "Chapter 5: Introduction to Python & Algorithms", "Variables, Data Types, and If-Else Conditionals", "Live demonstration of writing simple calculator script in Python.", "Write pseudocode algorithm for checking even/odd numbers."),
        ("Urdu A", "سبق نمبر 3: نظریہ پاکستان", "سبق کی بلند خوانی اور اہم نکات کی وضاحت", "مشکل الفاظ کے معانی اور پیراگراف نمبر 2 کی تشریح تختہ تحریر پر کروائی گئی۔", "مشقی سوالات نمبر 1 تا 4 کاپی پر حل کریں۔"),
        ("Islamiyat / Ethics", "باب دوم: ارکانِ اسلام اور نماز کی اہمیت", "نماز کی شرائط و فرائض اور باجماعت ادائیگی کی فضیلت", "تختہ تحریر پر نماز کے 7 فرائض اور خشوع و خضوع کے طریقے سکھائے گئے۔", "نماز کے ارکان اور دعائے قنوت زبانی یاد کریں۔")
    ]

    today = datetime.date.today()
    created_count = 0

    for cls in classes:
        sec = cls.sections.first()
        if not sec:
            sec = Section.objects.create(name='A', class_room=cls)

        for i, (sub_name, ch_name, topic, classwork, homework) in enumerate(sample_topics[:4]):
            sub = subjects.filter(name__icontains=sub_name.split()[0]).first()
            if not sub:
                sub = subjects.first()

            lec_date = today - datetime.timedelta(days=i)

            lec, created = DailyLecture.objects.get_or_create(
                date=lec_date,
                class_room=cls,
                section=sec,
                subject=sub,
                topic=topic,
                defaults={
                    'teacher': teacher_user,
                    'chapter_name': ch_name,
                    'learning_objectives': f"Understand core principles of {topic}.",
                    'classwork_description': classwork,
                    'homework_assigned': homework,
                    'present_students_count': 28,
                    'absent_students_count': 2,
                    'copies_checked_count': 25,
                    'remarks': "Good classroom engagement and participation."
                }
            )

            # Attach audio recording sample
            if not lec.audio_recording and os.path.exists(demo_audio_path):
                with open(demo_audio_path, 'rb') as f:
                    lec.audio_recording.save(f"audio_{cls.id}_{sub.id}_{i}.wav", File(f), save=True)

            if created:
                created_count += 1

    print(f"Successfully seeded {created_count} class-wise lectures with audio recordings.")

if __name__ == '__main__':
    seed_sample_class_lectures()
