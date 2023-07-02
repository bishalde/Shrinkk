from django.shortcuts import render,redirect
import time
from datetime import date
from service.models import userInformation,subscriberInformation
# Create your views here.

def homePage(request):
    data={'message':request.GET.get('status')}
    subscribers = subscriberInformation.objects.filter().count()
    users = userInformation.objects.filter().count()
    data['users']=users
    data["subscribers"] = subscribers
    return render(request, 'homePage.html',data)


def subscribePage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if subscriberInformation.objects.filter(email=email).exists():
            status='Email Already Exists.!'
        else:
            subscriberInformation.objects.create(email=email)

        status='ThakYou For Subscribing.!'
        return redirect('/?status=' + status)


def loginPage(request):
    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')

        if userInformation.objects.filter(email=email,password=password).exists():
            username = userInformation.objects.get(email=email,password=password).username
            request.session['email'] = email
            request.session['username'] = username
            request.session.set_expiry(3600)

            return redirect("/") 
        else:
            status='Invalid Credentials.!'
            return redirect('/?status=' + status)
    
    return redirect("/")


def signupPage(request):
    data={"message":None}
    if request.method == 'POST':
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirmpassword=request.POST.get('confirmpassword')
        if password == confirmpassword:
            if userInformation.objects.filter(email=email).exists():
                data['message'] = "Email already exists."
            elif userInformation.objects.filter(username=username).exists():
                data['message'] = "Username already exists."
            else:
                userInformation.objects.create(username=username,email=email,password=password)
                data['message'] = "User created successfully.!"
                status='User created successfully..!'
                return redirect('/?status=' + status)
        else:
            data['message'] = "Passwords do not match."
        
    return render(request,'signupPage.html',data)


def logoutPage(request):
    request.session.flush()
    return redirect("/")