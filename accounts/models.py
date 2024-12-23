from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date


GENDER = (
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
)

ALCOHOLIC = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)

SMOKER = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)
class User(AbstractUser):
    custom_id = models.CharField(max_length=255, unique=True, editable=False)
    email = models.EmailField(unique=True)
    profile_for = models.CharField(max_length=255, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profiles', null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    family_name = models.CharField(max_length=255, null=True, blank=True)
    living_in = models.CharField(max_length=255, null=True, blank=True)
    community = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=6, choices=GENDER, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=13, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    online = models.BooleanField(default=False)
    device_token = models.CharField(max_length=250, null=True, blank=True)


    headline = models.CharField(max_length=255, null=True, blank=True)
    about_me = models.TextField(null=True, blank=True)
    caste = models.CharField(max_length=50, null=True, blank=True)
    religion = models.CharField(max_length=50, null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Height in CM")
    weight = models.PositiveIntegerField(null=True, blank=True, help_text="Weight in KG")
    education = models.CharField(max_length=100, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Income in Rs.")
    family_status = models.CharField(max_length=100, null=True, blank=True)
    alcoholic = models.CharField(max_length=6, choices=ALCOHOLIC, null=True, blank=True, default="No")
    smoker = models.CharField(max_length=6, choices=SMOKER, null=True, blank=True, default="No")
    hobbies = models.CharField(max_length=255, null=True, blank=True)
    skin_tone = models.CharField(max_length=50, null=True, blank=True)

    def get_age(self):
        if not self.dob:
            return None
        today = date.today()
        age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return age

    def get_gender(self):
        gender = dict(GENDER).get(self.gender, 'Unknown')
        return gender
