from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


## enables the user-profile model's fields to be edited inline with the user model (they're at the bottom)
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'


## custom User admin, incorporating UserProfileInline above
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


## re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

## register UserProfile separately -- in case we want to edit it directly
admin.site.register(UserProfile)
