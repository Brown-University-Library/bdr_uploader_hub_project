from django.contrib import admin
from django.urls import path

from bdr_deposits_uploader_app import views

urlpatterns = [
    ## main ---------------------------------------------------------
    path('info/', views.info, name='info_url'),
    path('login/', views.pre_login, name='pre_login_url'),
    path('shib_login/', views.shib_login, name='shib_login_url'),
    path('logout/', views.logout, name='logout_url'),
    path('staff_config/new/', views.config_new, name='staff_config_new_url'),
    path('staff_config/<str:slug>/', views.config_slug, name='staff_config_slug_url'),
    path('student_upload/', views.upload, name='student_upload_url'),
    path('student_upload/<str:slug>/', views.upload_slug, name='student_upload_slug_url'),
    path('upload_successful/', views.upload_successful, name='upload_successful_url'),  # not yet implemented
    ## htmx helpers -------------------------------------------------
    path('hlpr_generate_slug/', views.hlpr_generate_slug, name='hlpr_generate_slug_url'),
    path('hlpr_check_name_and_slug/', views.hlpr_check_name_and_slug, name='hlpr_check_name_and_slug_url'),
    ## other --------------------------------------------------------
    path('', views.root, name='root_url'),
    path('admin/', admin.site.urls),
    path('error_check/', views.error_check, name='error_check_url'),
    path('version/', views.version, name='version_url'),
]
