from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib import messages
from app.EmailBackEnd import EmailBackEnd
from django.contrib.auth import login,logout
from django.core.mail import send_mail
from django.conf import settings


def REGISTER(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # check email
        if User.objects.filter(email=email).exists():
            messages.warning(request, 'Email Already Exists !')
            return redirect('register')

        #check username
        if User.objects.filter(username=username).exists():
            messages.warning(request, 'Username Already exists !')
            return redirect('register')

        user =User(
            username=username,
            email=email,
        )

        send_mail(
            'BMS-EL Registration Confirmation',
            'Thank you for regististering to  BMS-EL. Your registration is confirmed !!!',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

        user.set_password(password)
        user.save()
        return redirect('login')
    return render(request,'registration/register.html')


def DO_LOGIN(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = EmailBackEnd.authenticate(request,username=email,password=password)

        if user != None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request,'Email and Password Are Invalid !!!')
            return redirect('login')


def PROFILE(request):
    return render(request, 'registration/profile.html')


def PROFILE_UPDATE(request):
    if request.method == "POST":
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_id = request.user.id

        user = User.objects.get(id=user_id)
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.email = email

        if password != None and password != "":
            user.set_password(password)
        user.save()
        messages.success(request, 'Profile is sucessfully updated!! ')
    return redirect('profile')


def LOGOUT(request):
    logout(request)
    messages.success(request, 'User Logged out sucessfully !!')
    return redirect('login')