from django.contrib import admin

from .models import UserProfile

# No custom UserAdmin registration, so remove:
# admin.site.unregister(User)
# admin.site.register(User, CustomUserAdmin)

# Just register UserProfile normally
admin.site.register(UserProfile)
