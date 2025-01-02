from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz, name='quiz'),
    path('home/', views.home, name='home'),
    path('login/', views.login, name='login'), 
    path('register/', views.register, name='register'),
    path('logout/', views.logout, name='logout'), 
    path('profile/', views.profile, name='profile'), 
    path('<int:session_id>/', views.create_checkout_session, name="create_checkout_session"),
    path('session_success/', views.session_success, name="session_success"),
    path('session_cancel/', views.session_cancel, name="session_cancel"),
    path('stripe/webhook/', views.stripe_webhook, name="stripe_webhook")
      
]
