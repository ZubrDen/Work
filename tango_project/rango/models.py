from django.db import models
from django.template.defaultfilters import slugify
from django.contrib.auth.models import User
from django import forms


class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Page(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    url = models.URLField()
    views = models.IntegerField(default=0)
    page_id = models.IntegerField(default=0)

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    # Эта строка обязательна. Связывает UserProfile с экземпляром модели User.
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Дополнительные атрибуты, которые мы хотим включить.
    website = models.URLField(blank=True)
    picture = models.ImageField(upload_to='profile_images', blank=True)

    # Переопределите метод __unicode __ (), чтобы получить что-то значимое!
    # Помните, что если вы используете Python 2.7.x, определите также __unicode__!
    def __str__(self):
        return self.user.usename


class UserProfileForm(forms.ModelForm):
    website = forms.URLField(required=False)
    picture = forms.ImageField(required=False)

    class Meta:
        model = UserProfile
        exclude = ('user',)







