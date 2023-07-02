from django.shortcuts import render,redirect
import pyrebase,time
from datetime import date
import pprint
# Create your views here.
firebaseConfig = {
  "apiKey": "AIzaSyALwZRcFKUMe2gOP_nnuNcQtFKnlSlLydM",
  "authDomain": "shrinkk-847a2.firebaseapp.com",
  "projectId": "shrinkk-847a2",
  "storageBucket": "shrinkk-847a2.appspot.com",
  "messagingSenderId": "310331286275",
  "databaseURL":"https://shrinkk-847a2-default-rtdb.asia-southeast1.firebasedatabase.app",
  "appId": "1:310331286275:web:f0c75eb98496de81147f36",
  "measurementId": "G-H8YPKLDE7V"
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

def homePage(request):
    data={'message':request.GET.get('status')}
    subscribers = db.child("websiteInfo").child('subscribers').get()
    if subscribers.val() == None :
        subscribers = 0
    else:
        subscribers = len(subscribers.val())

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