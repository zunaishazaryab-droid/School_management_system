import os
import sys
import django

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r'c:\Users\hp\OneDrive\Desktop\Schoolmanagment')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.core.models import SchoolSetting

s = SchoolSetting.get_settings()
s.school_name = "GEN'X VISION SCHOOL SYSTEM"
s.tagline = "Knowledge • Excellence • Leadership"
s.save()
print("Successfully updated SchoolSetting school_name to:", s.school_name)
