from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Genre
from .models import Rating
class RegisterForm(UserCreationForm):
   # email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username",  "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-3 py-2 rounded-md bg-gray-800 text-white placeholder-gray-407000 focus:outline-none focus:ring-2 focus:ring-purple-500',
                #'placeholder': field.label
            })

class MovieFilterForm(forms.Form):
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        empty_label='Все жанры',
        widget=forms.Select(attrs={'class': 'bg-gray-700  text-white rounded px-4 py-2'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('', 'Без сортировки'),
            ('title', 'По названию (A-Z)'),
            ('-title', 'По названию (Z-A)'),
            ('release_year', 'По году (по возрастанию)'),
            ('-release_year', 'По году (по убыванию)'),
            ('rating', 'По рейтингу (по возрастанию)'),
            ('-rating', 'По рейтингу (по убыванию)')
        ],
        required=False,
        widget=forms.Select(attrs={'class':' bg-gray-700 text-white rounded px-4 py-2'})
    )

class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.NumberInput(attrs={'min': 0, 'max': 10, 'class': 'bg-gray-800 text-white rounded w-16 p-1'}),
        } 

