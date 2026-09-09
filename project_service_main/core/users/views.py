from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import OrganizationSignupForm

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = OrganizationSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = OrganizationSignupForm()
        
    return render(request, 'users/signup.html', {'form': form})
