from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры постов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='group',
            slug='slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Хороший длинный тестовый текст поста',
        )

    def setUp(self):
        """Создаем авторизованного и неавторизованного клиента"""
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostURLTest.user)

    def test_list_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        urls = ('/',
                f'/{str(self.group.title)}/{str(self.group.slug)}/',
                f'/profile/{str(self.user.username)}/',
                f'/posts/{self.post.id}/',
                )
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)

    def test_url_post_create(self):
        """Страница /create/ доступна только авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_url_post_edit(self):
        """Страница /posts/post_id/edit доступна только автору поста."""
        if self.user.username == self.post.author:
            response = self.\
                authorized_client.get(f'/posts/{self.post.id}/edit/')
            self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Адрес /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_to_login(self):
        """Адрес /posts/post_id/edit перенаправит анонимного пользователя
        на страницу авторизации.
        """
        response = self.client.\
            get(f'/posts/{self.post.id}/edit/', follow=True)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_urls_uses_correct_template(self):
        """Проверка соответствия URL-адреса и шаблона."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/{str(self.group.title)}/{str(self.group.slug)}/':
                'posts/group_list.html',
            f'/profile/{str(self.user.username)}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
