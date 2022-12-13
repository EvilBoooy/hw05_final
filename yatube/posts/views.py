from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

from .models import Post, Group, Follow, User
from .forms import PostForm, CommentForm
from .utils import get_page_context


def index(request):
    post_list = Post.objects.all()
    context = {
        'page_obj': get_page_context(post_list, request),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    context = {
        'group': group,
        'posts': posts,
        'page_obj': get_page_context(posts, request),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_count = Post.objects.filter(author=author).count()
    context = {
        'author': author,
        'posts': posts,
        'page_obj': get_page_context(posts, request),
        'posts_count': posts_count,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        obj = form.save(commit=False)
        obj.author = request.user
        obj.save()
        return redirect('posts:profile', request.user)
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    posts = Post.objects.select_related('group')
    post = get_object_or_404(posts, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author != request.user:
        return redirect('posts:index')
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.id)
    return render(request,
                  'posts/create_post.html', {'form': form, 'is_edit': True})


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
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': get_page_context(post_list, request)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(author=author, user=user)
    if user != author and not following.exists():
        follow = Follow.objects.create(user=user, author=author)
        follow.save
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(user=request.user, author=user)
    if following.exists():
        following.delete()
    return redirect('posts:profile', username)
