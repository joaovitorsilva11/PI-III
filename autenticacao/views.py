from django.shortcuts import render
from django.http import HttpResponse
from .utils import password_is_valid
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.messages import constants
from django.contrib import auth
import os
import uuid
from django.conf import settings
from .utils import password_is_valid, email_html
from .models import Ativacao
from hashlib import sha256
from django.utils import timezone

def cadastro(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'cadastro.html')
    elif request.method == "POST":
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')
        email = request.POST.get('email')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not password_is_valid(request, senha, confirmar_senha):
            return redirect('/auth/cadastro')

        try:
            user = User.objects.create_user(username=username, email=email,
                                            password=senha,
                                            is_active=False)
            user.save()

            token = sha256(f"{username}{email}".encode()).hexdigest()
            ativacao = Ativacao(token=token, user=user)
            ativacao.save()

            path_template = os.path.join(settings.BASE_DIR, 'autenticacao/templates/emails/cadastro_confirmado.html')
            
            # Enviar e-mail e capturar erros
            try:
                email_html(path_template, 'Cadastro confirmado', [email], username=username,
                           link_ativacao=f"http://127.0.0.1:8000/auth/ativar_conta/{token}")
            except Exception as e:
                messages.add_message(request, constants.ERROR, f'Houve um erro ao enviar o e-mail: {str(e)}')
                return redirect('/auth/cadastro')

            messages.add_message(request, constants.SUCCESS, 'Cadastro realizado com sucesso, verifique seu email para ativar a conta')
            return redirect('/auth/logar')

        except Exception as e:
            messages.add_message(request, constants.ERROR, f'Houve um erro interno no sistema: {str(e)}')

    return redirect('/auth/cadastro')

def logar(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'logar.html')
    elif request.method == "POST":
     username = request.POST.get('usuario')
     senha = request.POST.get('senha')

    usuario = auth.authenticate(username=username, password=senha)

    if not usuario:
            messages.add_message(request, constants.ERROR, 'Username ou senha inválidos')
            return redirect('/auth/logar')
    else:
            auth.login(request, usuario)
            return redirect('/pacientes')

def sair(request):
    auth.logout(request)
    return redirect('/auth/logar')

def ativar_conta(request, token):
    token = get_object_or_404(Ativacao, token=token)
    if token.ativo:
        messages.add_message(request, constants.WARNING, 'Essa token já foi usado')
        return redirect('/auth/logar')

    user = User.objects.get(username=token.user.username)
    user.is_active = True
    user.save()
    token.ativo = True
    token.save()
    messages.add_message(request, constants.SUCCESS, 'Conta ativada com sucesso')
    return redirect('/auth/logar')

def reset_senha(request):
    if request.method == "GET":
        return render(request, 'reset_senha.html')  # Renderiza o formulário de recuperação de senha
    elif request.method == "POST":
        email = request.POST.get('email')

        # Verifica se o e-mail está associado a um usuário
        if not User.objects.filter(email=email).exists():
            messages.add_message(request, constants.ERROR, 'E-mail não encontrado.')
            return redirect('/auth/reset_senha')  # Retorna um redirecionamento para a página de recuperação

        user = User.objects.get(email=email)

        # Excluindo registros anteriores, se existirem
        Ativacao.objects.filter(user=user, ativo=False).delete()

        # Gere um token único usando UUID
        token = str(uuid.uuid4())  # Gera um UUID único
        ativacao = Ativacao(token=token, user=user)
        ativacao.save()

        # Envio de e-mail
        path_template = os.path.join(settings.BASE_DIR, 'autenticacao/templates/emails/reset_senha.html')
        email_html(path_template, 'Redefinição de senha', [email], username=user.username, link_reset=f"http://127.0.0.1:8000/auth/confirmar_reset_senha/{token}")

        messages.add_message(request, constants.SUCCESS, 'Um link de redefinição de senha foi enviado para seu e-mail.')
        return redirect('/auth/logar')  # Retorna um redirecionamento para a página de login

    # Se o método não for GET nem POST, deve retornar um erro ou redirecionar
    return redirect('/auth/logar')  # Redireciona em caso de método inválido

def confirmar_reset_senha(request, token):
    if request.method == "POST":
        nova_senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if nova_senha != confirmar_senha:
            messages.add_message(request, constants.ERROR, 'As senhas não coincidem!')
            return redirect(f'/auth/confirmar_reset_senha/{token}')
        
        # Use filter().first() para evitar múltiplos objetos
        token_obj = Ativacao.objects.filter(token=token).first()
        
        if not token_obj:
            messages.add_message(request, constants.ERROR, 'Token inválido ou inexistente.')
            return redirect('/auth/logar')

        if token_obj.ativo:
            messages.add_message(request, constants.WARNING, 'Este token já foi utilizado.')
            return redirect('/auth/logar')

        user = token_obj.user
        user.set_password(nova_senha)
        user.save()

        token_obj.ativo = True
        token_obj.save()

        messages.add_message(request, constants.SUCCESS, 'Senha alterada com sucesso!')
        return redirect('/auth/logar')

    return render(request, 'confirmar_reset_senha.html', {'token': token})

