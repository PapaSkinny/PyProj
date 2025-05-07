from django.contrib import admin
from core.models import Movie, Genre

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'release_year', 'rating', 'get_genres']

    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()])
    get_genres.short_description = 'Жанры'

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')              # Отображаем ID и имя в списке
    search_fields = ('name',)                  # Поле поиска по имени
    ordering = ('name',)                       # Сортировка по имени

