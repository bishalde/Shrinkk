from django.shortcuts import render,redirect

import time
from datetime import date
# Create your views here.

def homePage(request):
    data={'message':request.GET.get('status')}
    subscribers = 5
    data["subscribers"] = subscribers
    return render(request, 'homePage.html',data)


def subscribePage(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        subscribers = db.child('websiteInfo').child('subscribers').get().val()
        if subscribers:
            for key, data in subscribers.items():
                if 'email' in data and data['email'] == email:
                        status='Already Subscribed.!'
                        return redirect('/?status=' + status)
        
        time_string = time.strftime("%m/%d/%Y, %H:%M:%S", time.localtime())
        data = {
                    'email': email,
                    'dateTime': str(time_string),
                }
        db.child('websiteInfo').child('subscribers').push(data)
        status='ThakYou For Subscribing.!'
        return redirect('/?status=' + status)


def loginPage(request):
    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        data={'email':email,
              'password':password
              }
        return render(request,'loginPage.html',data) 
    
    return redirect("/")


def signupPage(request):
    data={"message":None}
    if request.method == 'POST':
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirmpassword=request.POST.get('confirmpassword')
        if password == confirmpassword:
            try:
                # Create a new user with email and password
                auth.create_user_with_email_and_password(email, password)
                data['message'] = "Account Created Successfully..!"
                return render(request, 'signupPage.html', data)
            
            except requests.exceptions.HTTPError as error:
                response = error.response.json()
                error_message = response.get('error', {}).get('message')
                if error_message == "EMAIL_EXISTS":
                    data['message'] = "Email already exists. Please use a different email."
                else:
                    data['message'] = "An error occurred while creating the account."
        else:
            data['message'] = "Passwords do not match."
        
    return render(request,'signupPage.html',data)