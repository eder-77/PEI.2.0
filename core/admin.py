from django.contrib import admin
from .models import Level,Subject,Document

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

