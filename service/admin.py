from django.contrib import admin
from service.models import *


# Register your models here.
admin.site.register(userInformation)
admin.site.register(subscriberInformation)
admin.site.register(URLInformation)
admin.site.register(URLSMade)
admin.site.register(URLSClicked)