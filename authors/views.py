from django.contrib import messages
from django.shortcuts import redirect, render

from authors.forms import RegisterForm


def register(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(
            request, 'Conta criada com sucesso. Bem-vindo(a) ao Receitas!',
        )
        return redirect('recipes:home')

    return render(request, 'authors/pages/register.html', context={
        'form': form,
    })
