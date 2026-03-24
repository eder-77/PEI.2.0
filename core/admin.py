from django.contrib import admin
from .models import Level,Subject,Document,StudentProfile,Notification

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
  list_display=('name',)
  ordering=('name',)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
  list_display=('name','level')
  list_filter=('level',)
  ordering=('level',)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
  list_display=('title', 'subject', 'get_level', 'doc_type', 'uploaded_at')  
  list_filter = ('doc_type', 'subject__level', 'subject')
  search_fields=('title','subject__name')
  ordering=('subject__level',)

  def get_level(self,obj):
    return obj.subject.level
  get_level.short_description='Annee'

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
  list_display  = ('user', 'year')
  list_filter   = ('year',)
  search_fields = ('user__username',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'document', 'is_read', 'created_at')
    list_filter   = ('is_read',)
