from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from blog.models import Category, Comment, Post, User

from .forms import CommentForm, PostForm, ProfileForm


class OnlyAuthorMixin(UserPassesTestMixin):
    """Миксин для проверки автора объекта."""

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostsReverseMixin:
    """Миксин для постов."""

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class CommentPostMixin:
    """Миксин для комментариев."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_queryset(self):
        return self.request.user.comments.filter(author=self.request.user)

    def get_success_url(self):
        post_id = self.object.post.pk
        return reverse('blog:post_detail', kwargs={'pk': post_id})


class PostsListView(ListView):
    """Все посты в ленте."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATED_BY

    def get_queryset(self):
        return Post.published.select_related(
            'location',
            'category',
            'author'
        ).filter(
            is_published=True,
            pub_date__lte=timezone.now()
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))


class CategoryPostsView(ListView):
    """Посты по категориям."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = settings.PAGINATED_BY

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(Category, slug=category_slug)
        return Post.objects.filter(
            category=category, is_published=True, pub_date__lte=timezone.now()
        ).annotate(comment_count=Count('comments')).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        context['category'] = category
        return context


class PostCreateView(LoginRequiredMixin, PostsReverseMixin, CreateView):
    """Создание поста."""

    pass


class PostUpdateView(OnlyAuthorMixin, PostsReverseMixin, UpdateView):
    """Редактирование поста."""

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        post_id = self.kwargs.get('pk')
        if instance.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=post_id,
            )
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(OnlyAuthorMixin, PostsReverseMixin, DeleteView):
    """Удаление поста."""

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class PostDetailView(PostsReverseMixin, DetailView):
    """Отдельный пост."""

    model = Post
    template_name = 'blog/detail.html'
    post_object = None
    pk_url_kwargs = 'post_id'

    def get_queryset(self):
        self.post_object = get_object_or_404(Post, pk=self.kwargs['pk'])
        if self.post_object.author == self.request.user:
            return user_post_filter().filter(pk=self.kwargs['pk'])
        return get_filter().filter(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


class ProfileListView(ListView):
    """Возвращает посты автора."""

    model = Post
    template_name = 'blog/profile.html'
    paginate_by = settings.PAGINATED_BY

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        queryset = (
            self.author
            .posts.order_by('-pub_date')
            .annotate(comment_count=Count('comments'))
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля."""

    model = Post
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return get_object_or_404(User, username=self.request.user.username)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария."""

    model = Comment
    form_class = CommentForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['pk'])
        form.instance.author = self.request.user
        form.save()
        return redirect('blog:post_detail', pk=self.kwargs['pk'])


class CommentUpdateView(LoginRequiredMixin, CommentPostMixin, UpdateView):
    """Редактирование комментария."""

    pass


class CommentDeleteView(LoginRequiredMixin, CommentPostMixin, DeleteView):
    """Удаление комментария."""

    pass


def get_filter():
    query_set = (Post.objects.all().filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ))
    return query_set


def user_post_filter():
    query_set = (Post.objects.all().filter().annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date'))
    return query_set
