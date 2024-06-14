from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
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
        return reverse(
            'blog:post_detail',
            kwargs={'post_pk': self.kwargs['post_pk']}
        )


class PostsListView(ListView):
    """Все посты в ленте."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATED_BY

    def get_queryset(self):
        return Post.published.order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))


class CategoryPostsView(ListView):
    """Посты по категориям."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = settings.PAGINATED_BY
    category_obj = None

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True
        )
        self.category_obj = category.posts(manager='published').order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))
        return self.category_obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category_obj
        return context


class PostCreateView(LoginRequiredMixin, PostsReverseMixin, CreateView):
    """Создание поста."""

    pass


class PostUpdateView(PostsReverseMixin, UpdateView):
    """Редактирование поста."""

    pk_url_kwarg = 'post_pk'

    def dispatch(self, request, *args, **kwargs):
        instance = self.get_object()
        post_pk = self.kwargs.get('post_pk')
        if instance.author != request.user:
            return redirect(
                'blog:post_detail',
                post_pk=post_pk,
            )
        return super().dispatch(request, *args, **kwargs)


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """Удаление поста."""

    model = Post
    pk_url_kwarg = 'post_pk'

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.get_object())
        return context


class PostDetailView(DetailView):
    """Отдельный пост."""

    model = Post
    template_name = 'blog/detail.html'
    post_obj = None
    pk_url_kwarg = 'post_pk'

    def get_object(self):
        self.post_obj = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        if self.post_obj.author == self.request.user:
            return self.post_obj
        return get_object_or_404(Post.published.order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments')))

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
        if self.author == self.request.user:
            return self.author.posts.order_by(
                '-pub_date'
            ).annotate(comment_count=Count('comments'))
        return self.author.posts(manager='published').order_by(
            '-pub_date'
        ).annotate(comment_count=Count('comments'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля."""

    model = Post
    form_class = ProfileForm
    template_name = 'blog/user.html'

    def get_object(self):
        return self.request.user

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
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_pk'])
        form.instance.author = self.request.user
        form.save()
        return redirect('blog:post_detail', post_pk=self.kwargs['post_pk'])


class CommentUpdateView(LoginRequiredMixin, CommentPostMixin, UpdateView):
    """Редактирование комментария."""

    pass


class CommentDeleteView(LoginRequiredMixin, CommentPostMixin, DeleteView):
    """Удаление комментария."""

    pass
