from django.contrib import admin
from .models import Member

# Register your models here.
class MemberAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'email', 'phone', 'address', 'city', 'state', 'zip_code', 'membership_type', 'phone', 'joined_date')
    
admin.site.register(Member)
