import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpRequest
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from posts.models import Post, Group, User
from posts.forms import PostForm
from django.conf import settings

per_page = settings.PERPAGE


def index(request: HttpRequest) -> HttpResponse:
    """Модуль отвечающий за главную страницу."""
    posts: Post = Post.objects.all()
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'posts': posts,
        'page_obj': page_obj,
        'page_title': 'Последние обновления на сайте',
    }
    return render(request, 'posts/index.html', context)


def group_posts(request: HttpRequest, slug: str) -> HttpResponse:
    """Модуль отвечающий за страницу сообщества."""
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_obj,
        'page_title': f'Записи сообщества {slug}',
        'gr_descr': group.description
    }
    return render(request, 'posts/group_list.html', context)


def profile(request: HttpRequest, username: str) -> HttpResponse:
    """Модуль отвечающий за личную страницу."""
    author = get_object_or_404(User, username=username)
    paginator = Paginator(author.posts.all(), per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'author': author,
        'page_obj': page_obj,
        'posts': author.posts.all(),
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request: HttpRequest, post_id: int) -> HttpResponse:
    """Модуль отвечающий за просмотр отдельного поста."""
    post = get_object_or_404(
        Post.objects
            .select_related('author')
            .select_related('group'), id=post_id)
    context = {
        'post': post,
        'id': post_id,
        'page_title': post.text[:30],
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request: HttpRequest) -> HttpResponse:
    """Модуль отвечающий за страницу создания текста постов."""
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'posts/create_post.html', {'form': form, })
    form = PostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.pub_date = datetime.datetime.now()
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, 'posts/create_post.html', {'form': form, })


@login_required
def post_edit(request: HttpRequest, post_id: int) -> HttpResponse:
    """Модуль отвечающий за страницу редактирования текста постов."""
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(instance=post)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
        'id': post_id
    }
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if request.method != 'POST':
        return render(request, 'posts/create_post.html', context)
    form = PostForm(request.POST, instance=post)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', context)
    post.text = form.cleaned_data['text']
    post.group = form.cleaned_data['group']
    post.author = request.user
    post.save()
    return redirect('posts:post_detail', post_id)
