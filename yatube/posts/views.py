from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from .utils import get_page_context


@cache_page(20, key_prefix='index_page')
def index(request):
    """Вывод шаблона главной страницы."""
    context = get_page_context(Post.objects.select_related(
        'author', 'group'), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Вывод шаблона постовотфильтрованных по группам."""
    group = get_object_or_404(Group, slug=slug)
    context = {
        'group': group,
    }
    context.update(get_page_context(group.group_posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Вывод шаблона профайла пользователя:
    на ней будет отображаться информация об авторе и его посты.
    """
    author = get_object_or_404(User, username=username)
    amount = author.posts.all().count()
    following = False
    following = (request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists())
    context = {
        'author': author,
        'amount': amount,
        'following': following,
    }
    context.update(get_page_context(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Вывод шаблона для просмотра отдельного поста"""
    posts = get_object_or_404(
        Post.objects.select_related('author'), pk=post_id)
    amount = posts.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = posts.comments.all()
    context = {
        'posts': posts,
        'amount': amount,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Вывод шаблона для публикации постов"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,)
    if form.is_valid():
        f = form.save(commit=False)
        f.author = request.user
        form.save()
        return redirect('posts:profile', f.author)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Вывод шаблона для редактирования постов"""
    posts = get_object_or_404(Post, pk=post_id)
    if request.user != posts.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=posts)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'posts': posts,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post = Post.objects.filter(
        author__following__user=request.user)
    context = get_page_context(post, request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username)
    follow.delete()
    return redirect('posts:profile', username=username)
