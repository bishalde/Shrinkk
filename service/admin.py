from django.contrib import admin
from service.models import userInformation,subscriberInformation


# Register your models here.
admin.site.register(userInformation)
admin.site.register(subscriberInformation)