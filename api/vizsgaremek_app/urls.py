from . import views
from django.urls import include
from django.urls import path

urlpatterns = [
    path('', views.home, name='home'),
    path('debug/', views.debug, name='debug'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout', views.logout, name='logout'),
    
    path("teachers/", views.teacher_list, name="teacher_list"),  # 🔹 ÚJ
    path("evaluation/<int:teacher_id>/", views.evaluation, name="evaluation"),
    path("evaluation/<int:evaluation_id>/open/", views.evaluation_open, name="evaluation_open"),
    path("evaluation/thanks/", views.evaluation_thanks, name="evaluation_thanks"),
    path("teacher/<int:teacher_id>/report/", views.teacher_report, name="teacher_report"),
]
