from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm


# Create your views here.
def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request,user)
                messages.add_message(request, messages.SUCCESS,"Login successful.")
                return redirect("home")
            else:
                return render(request,"account/login.html",{"form":form})
        else:
            return render(request,"account/login.html",{"form":form})
    else:
        form = AuthenticationForm()
        return render(request,"account/login.html",{"form":form})


def user_register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        repassword = request.POST["repassword"]

        if password == repassword:
            if User.objects.filter(username = username).exists():
                messages.add_message(request, messages.ERROR,"This username already exists.")
                return render(request,"account/register.html")
            else:
                if User.objects.filter(email=email).exists():
                    messages.add_message(request, messages.ERROR,"This email already exists.")
                    return render(request,"account/register.html")
                else:
                    user = User.objects.create_user(username = username, email=email, password=password)
                    user.save()
                    return redirect("user_login")

        else:
            messages.add_message(request, messages.ERROR,"Password does not match.")
            return render(request,"account/register.html")


    else:
        return render(request,"account/register.html")

def pass_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request,"Password was updated.")
            return redirect("pass_change")
        else:
            return render(request, "account/change_password.html", {"form":form})

    form = PasswordChangeForm(request.user)
    return render(request, "account/change_password.html", {"form":form})

def user_logout(request):
    messages.add_message(request, messages.SUCCESS,"Logout successful.")
    logout(request)
    return redirect("home")