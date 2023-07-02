from django.db import models

# Create your models here.
class userInformation(models.Model):
    username=models.CharField(max_length=100,primary_key=True)
    email=models.EmailField(max_length=150,unique=True)
    password=models.CharField(max_length=50)
    createdDate=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
class subscriberInformation(models.Model):
    email=models.EmailField(max_length=150,unique=True)
    dateTime=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email