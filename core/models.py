from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Level(models.Model):
    YEAR_CHOICES = [
        ('1AP', '1ere annee'),
        ('2ST', '2eme annee (ST)'),
        ('2MI', '2eme annee (MI)'),
        ('3ST', '3eme annee (ST)'),
        ('3MI', '3eme annee (MI)'),
    ]
    name = models.CharField(max_length=10, choices=YEAR_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class Subject(models.Model):
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} {self.level}"


class Document(models.Model):
    TYPE_CHOICES = [
        ('COURS', 'Cours'),
        ('TP', 'TP & TD'),
        ('EXAM', 'Examen'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    doc_type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    file_doc = models.FileField(upload_to='library/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ════════════════════════════════════════
# NOUVEAU : Profil étudiant
# ════════════════════════════════════════
class StudentProfile(models.Model):
    YEAR_CHOICES = [
        ('1AP', '1ere annee'),
        ('2ST', '2eme annee (ST)'),
        ('2MI', '2eme annee (MI)'),
        ('3ST', '3eme annee (ST)'),
        ('3MI', '3eme annee (MI)'),
    ]
    user   = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    year   = models.CharField(max_length=10, choices=YEAR_CHOICES, blank=True)
    bio    = models.TextField(max_length=300, blank=True)

    def __str__(self):
        return f"Profil de {self.user.username}"

    def get_initials(self):
        name = self.user.get_full_name()
        if name:
            parts = name.split()
            return ''.join([p[0].upper() for p in parts[:2]])
        return self.user.username[0].upper()


# Crée automatiquement un profil vide à chaque nouvel utilisateur
@receiver(post_save, sender=User)
def create_or_save_profile(sender, instance, created, **kwargs):
    StudentProfile.objects.get_or_create(user=instance)

# core/models.py - ajouter en bas

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant'),
    ]
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.created_at:%d/%m/%Y %H:%M}"    
    

# core/models.py - ajouter en bas

class Notification(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    document   = models.ForeignKey(Document, on_delete=models.CASCADE)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif {self.user.username} — {self.document.title}"


# Signal : quand un document est ajouté, notifier tous les étudiants de la même année
@receiver(post_save, sender=Document)
def notify_students(sender, instance, created, **kwargs):
    if not created:
        return  # On notifie seulement à la création, pas à la modification

    # Trouver l'année du document
    level = instance.subject.level

    # Trouver tous les étudiants de cette année
    profiles = StudentProfile.objects.filter(year=level.name).select_related('user')

    # Créer une notification pour chacun
    notifications = [
        Notification(user=profile.user, document=instance)
        for profile in profiles
    ]
    Notification.objects.bulk_create(notifications)

class Favori(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='favoris')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering  = ['-added_at']
        unique_together = ('user', 'document')  # Un seul favori par doc par user

    def __str__(self):
        return f"{self.user.username} ♥ {self.document.title}"        



 
