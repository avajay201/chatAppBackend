from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date


GENDER = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
)
class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profiles', null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    online = models.BooleanField(default=False)
    
    def get_age(self):
        if not self.dob:
            return None
        today = date.today()
        age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return age

    def get_gender(self):
        gender = dict(GENDER).get(self.gender, 'Unknown')
        return gender
