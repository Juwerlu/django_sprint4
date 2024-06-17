from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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

    pk_url_kwarg = 'post_id'

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect(
            'blog:post_detail',
            post_id=self.kwargs['post_id'],
        )


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

    def get_object(self):
        return get_object_or_404(Comment, pk=self.kwargs['comment_id'])

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class PostsListView(ListView):
    """Все посты в ленте."""

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.PAGINATED_BY
    queryset = Post.published.all()


class CategoryPostsView(ListView):
    """Посты по категориям."""

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'page_obj'
    paginate_by = settings.PAGINATED_BY
    category = None

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return self.category.posts(manager='published').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class PostCreateView(LoginRequiredMixin, PostsReverseMixin, CreateView):
    """Создание поста."""

    pass


class PostUpdateView(OnlyAuthorMixin, PostsReverseMixin, UpdateView):
    """Редактирование поста."""

    pass


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """Удаление поста."""

    model = Post


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
    pk_url_kwarg = 'post_id'

    def get_object(self):
        post_obj = get_object_or_404(Post, pk=self.kwargs['post_id'])
        if post_obj.author == self.request.user:
            return post_obj
        return get_object_or_404(
            Post.published,
            pk=self.kwargs['post_id']
        )

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
    author = None

    def get_queryset(self):
        self.author = get_object_or_404(User, username=self.kwargs['username'])
        if self.author == self.request.user:
            return self.author.posts(manager='annotated').all()
        return self.author.posts(manager='published').all()

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
        form.instance.post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.save()
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class CommentUpdateView(OnlyAuthorMixin, CommentPostMixin, UpdateView):
    """Редактирование комментария."""

    pass


class CommentDeleteView(OnlyAuthorMixin, CommentPostMixin, DeleteView):
    """Удаление комментария."""

    pass
