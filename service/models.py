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
    
class URLInformation(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.CharField(max_length=100)

    def __str__(self):
        return self.short_code

class URLSMade(models.Model):
    count=models.PositiveBigIntegerField(default=0)

    def __str__(self):
        return str(self.count)

class URLSClicked(models.Model):
    count=models.PositiveBigIntegerField(default=0)
    def __str__(self):
        return str(self.count)







