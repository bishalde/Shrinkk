from django.shortcuts import render,redirect
from django.http import HttpResponse
import time
from datetime import date
from service.models import *
import random
import string
import qrcode

DOMAIN="https://shrinkk.vercel.app/"
# Create your views here.

def generate_short_code():
    length = 6  
    characters = string.ascii_letters + string.digits  
    short_code = ''.join(random.choice(characters) for _ in range(length))
    return short_code


def update_URLSMade():
    try:
        query=URLSMade.objects.get(id=1)
        query.count+=1
        query.save()
    except Exception as e :
        print(e)


def homePage(request):
    data={'message':request.GET.get('status')}
    subscribers = subscriberInformation.objects.filter().count()
    data["subscribers"] = subscribers

    users = userInformation.objects.filter().count()
    data['users']=users

    URLSMadeCount = URLSMade.objects.get(id=1).count
    data["URLSMadeCount"] = URLSMadeCount

    URLSClickedCount = URLSClicked.objects.get(id=1).count
    data["URLSClickedCount"] = URLSClickedCount

    return render(request, 'homePage.html',data)


def shortenPage(request):
    global DOMAIN
    data={'urlgenerated_details':None,'message':None,'showdata':None,'domain':DOMAIN}
    if request.method == 'POST':
        original_url = request.POST.get('longurl')
        domain = request.POST.get('domain')
        backhalf = request.POST.get('backhalf')
        user = request.session.get('username')
        if backhalf != None and len(backhalf)>0 and len(backhalf)<7:
            short_code=backhalf
            if URLInformation.objects.filter(short_code=backhalf).exists():
                status='BackHalf Already Exists.!'
                data={'message':status}
                return render(request,'shortenPage.html',data)

            else:
                qr_img = qrcode.QRCode(version = 3,
                        box_size = 4,
                        border = 2)
                # qr_img = qrcode.make("{}/{}".format(DOMAIN,short_code))  
                # qr_img.save("media/data/qr/{}.png".format(short_code))
                data['qrlink']='https://api.qrserver.com/v1/create-qr-code/?data={}{}&amp;size=100x100'.format(DOMAIN,short_code)
                qurey=URLInformation(original_url=original_url,short_code=short_code,user=user)
                qurey.save()
                update_URLSMade()
                status='Short URL CREATED.!'
                data['message']=status
                data['urlgenerated_details'] = {
                    'original_url':original_url,
                    'short_code':short_code,
                }
                data['showdata']="ok"
                return render(request,'shortenPage.html',data)
                   
        else:
            while True:
                short_code=generate_short_code()
                if URLInformation.objects.filter(short_code=short_code).exists():
                    continue

                else:
                    qr_img = qrcode.QRCode(version = 3,
                        box_size = 4,
                        border = 2)
                    # qr_img = qrcode.make("{}/{}".format(DOMAIN,short_code))  
                    # qr_img.save("media/data/qr/{}.png".format(short_code))
                    qurey=URLInformation(original_url=original_url,short_code=short_code,user=user)
                    qurey.save()
                    update_URLSMade()
                    status='Short Code CREATED.!'

                    data['message']=status
                    data['urlgenerated_details'] = {
                    'original_url':original_url,
                    'short_code':short_code,
                    }
                    data['qrlink']='https://api.qrserver.com/v1/create-qr-code/?data={}{}&amp;size=100x100'.format(DOMAIN,short_code)

                    data['showdata']="ok"
                    return render(request,'shortenPage.html',data)

    
    return render(request,'shortenPage.html',data)


def redirecturl(request,short_code):
    try:
        query=URLInformation.objects.get(short_code=short_code)
        query2=URLSClicked.objects.get(id=1)
        query2.count+=1
        query2.save()

        return redirect(query.original_url)
    except:
        return HttpResponse("<h1>Page Not Found.!</h1>")


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