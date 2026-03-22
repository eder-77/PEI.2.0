from django.db import models

class Level (models.Model):
  YEAR_CHOICES =[
    ('1AP','1ere annee'),
    ('2ST','2eme annee (ST)'),
    ('2MI','2eme annee (MI)'),
    ('3ST','3eme annee (SI)'),
    ('3MI','3eme annee (MI)'),
  ]

  name=models.CharField(max_length=10, choices=YEAR_CHOICES, unique=True)

  def __str__(self):
    return self.get_name_display()
  

class Subject(models.Model):
  level=models.ForeignKey(Level ,on_delete=models.CASCADE, related_name='subjects')
  name=models.CharField(max_length=100)

  def __str__(self):
    return f"{self.name} {self.level}"
  
class Document(models.Model):
  TYPE_CHOICES=[
    ('COURS','cours'),
    ('TP','tp'),
    ('EXAM','examen'),
  ]  
  subject=models.ForeignKey(Subject,on_delete=models.CASCADE,related_name='documents')
  title=models.CharField(max_length=200)
  doc_type=models.CharField(max_length=5, choices=TYPE_CHOICES)
  file_doc=models.FileField(upload_to='library/documents/')
  uploaded_at=models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return self.title




 
