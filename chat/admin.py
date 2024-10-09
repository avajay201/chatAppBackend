from django.contrib import admin
from .models import Chat, Message, BlockedUser, Report

admin.site.register(BlockedUser)
admin.site.register(Chat)
admin.site.register(Message)
admin.site.register(Report)
