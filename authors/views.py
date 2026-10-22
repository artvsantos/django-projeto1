from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_POST

from authors.forms import LoginForm, RegisterForm


def register(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request, 'Conta criada com sucesso. Agora é só entrar.',
        )
        return redirect('authors:login')

    return render(request, 'authors/pages/register.html', context={
        'form': form,
    })


def login_view(request):
    form = LoginForm(request.POST or None)
    next_url = request.GET.get('next', '')

    if request.method == 'POST' and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
        )

        if user is not None:
            login(request, user)
            messages.success(
                request,
                f'Você entrou como {user.first_name or user.username}.',
            )

            # Sem essa checagem, um link /authors/login/?next=https://...
            # mandaria o usuário para outro site logo depois de entrar.
            if url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect('recipes:home')

        form.add_error(None, 'Usuário ou senha inválidos.')

    # O next precisa sobreviver ao POST, então vai junto na action do form.
    form_action = reverse('authors:login')
    if next_url:
        form_action += '?' + urlencode({'next': next_url})

    return render(request, 'authors/pages/login.html', context={
        'form': form,
        'form_action': form_action,
    })


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Você saiu da sua conta.')
    return redirect('authors:login')
