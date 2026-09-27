from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Owner / Admin'
        PRINCIPAL = 'PRINCIPAL', 'Principal'
        COORDINATOR = 'COORDINATOR', 'Coordinator'
        TEACHER = 'TEACHER', 'Teacher'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text="Role determining user permissions in the school system."
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    is_active_staff = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_principal(self):
        return self.role == self.Role.PRINCIPAL

    @property
    def is_coordinator(self):
        return self.role == self.Role.COORDINATOR

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
