from django.urls import path
from.import views

urlpatterns= [
    path('cadastro/', views.cadastro, name="cadastro"),
    path('logar/', views.logar, name='logar'),
    path('sair/', views.sair, name="sair"),
    path('ativar_conta/<str:token>/', views.ativar_conta, name="ativar_conta"),
    path('reset_senha/', views.reset_senha, name='reset_senha'),
    path('confirmar_reset_senha/<str:token>/', views.confirmar_reset_senha, name='confirmar_reset_senha')
]