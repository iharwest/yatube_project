from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.
def index(request):    
    return HttpResponse('Главная страница проекта Yatube')

def group_posts(request, slug):
    return HttpResponse('Информация о группах {slug} проекта Yatube')
