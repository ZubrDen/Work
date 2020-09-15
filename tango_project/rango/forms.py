from django import forms
from django.contrib.auth.models import User
from rango.models import Page, Category, UserProfile

class CategoryForm(forms.ModelForm):
    name = forms.CharField(max_length=128,
                           help_text='Please enter the category name.')
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    likes = forms.IntegerField(widget=forms.HiddenInput(), initial=0)
    slug = forms.CharField(widget=forms.HiddenInput(), required=False)

    # Встроенный класс для предоставления дополнительной информации о форме.
    class Meta:
        # Обеспечивает связь между ModelForm и моделью
        model = Category
        fields = ('name',)

class PageForm(forms.ModelForm):
    title = forms.CharField(max_length=128,
                            help_text='Please enter the title of the page')
    url = forms.URLField(max_length=200,
                         help_text='Please enter the URL of the page')
    views = forms.IntegerField(widget=forms.HiddenInput(), initial=0)

    class Meta:
        # Обеспечивает связь между ModelForm и моделью
        model = Page

        # Какие поля мы хотим включить в нашу форму?
        # Таким образом, нам не нужно каждое поле в представленной модели.
        # Некоторые поля могут разрешать значения NULL, поэтому мы можем не включать их.
        # Здесь мы скрываем внешний ключ.
        # мы можем либо исключить поле категории из формы,
        exclude = ('category',)
        # или укажите поля для включения (т.е. не включают поле категории)
        # fields = ('title', 'url', 'views')

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('website', 'picture')
