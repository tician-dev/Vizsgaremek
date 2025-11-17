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
    path('evaluation/', views.evaluation, name='evaluation'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/logout', views.logout, name='logout'),
]
