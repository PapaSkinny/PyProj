from django.contrib import admin
from core.models import Movie, Genre, Rating

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'release_year', 'rating', 'get_genres']
    ordering = ('id',)   
    search_fields = ('title',)
    def get_genres(self, obj):
        return ", ".join([genre.name for genre in obj.genres.all()])
    get_genres.short_description = 'Жанры'

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')              # Отображаем ID и имя в списке
    search_fields = ('name',)                  # Поле поиска по имени
    ordering = ('name',)                       # Сортировка по имени

# Register the Rating model with custom admin interface
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'movie', 'score', 'id')  # Fields to display in the list view
    list_filter = ('user', 'movie','score')                  # Add filters for user and movie
    search_fields = ('user__username', 'movie__title')  # Enable search by username and movie title
    ordering = ('-id',)                              # Sort by ID (newest first)
    raw_id_fields = ('user', 'movie')                # Use raw ID fields for better performance with large datasets