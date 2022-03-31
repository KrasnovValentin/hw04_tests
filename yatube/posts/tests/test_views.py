from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.conf import settings

from posts.models import Group, Post
from posts.forms import PostForm

User = get_user_model()
per_page = settings.PERPAGE


class PostVIEWSTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры постов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='TestingDescription'
        )
        cls.new_group = Group.objects.create(
            title='new_group',
            slug='new_slug',
            description='NewDescription'
        )

        post_list = [Post(author=cls.user,
                          text=f'#_{i}__OldTestTextTextTextText',
                          group=cls.group,
                          ) for i in range(1, 10)]
        Post.objects.bulk_create(post_list)

        Post.objects.create(author=cls.user,
                            text='NewestTestTextTextTextText',
                            group=cls.new_group,
                            )
        cls.posts = Post.objects.all().order_by('-id')
        cls.posts_gr = Post.objects.filter(group=cls.group).order_by('-id')
        cls.post_n_gr = Post.objects.filter(group=cls.new_group)
        cls.posts_prf = Post.objects.filter(author=cls.user).order_by('-id')

    def setUp(self):
        """Создаем авторизованного и неавторизованного клиента"""
        self.guest_client = Client()
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostVIEWSTest.user)

    def test_pages_uses_correct_template(self):
        """Проверка на соответствие URL-адреса
        соответствующему шаблону.
        """
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}),
            'posts/profile.html':
                reverse('posts:profile',
                        kwargs={'username': self.user.username}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        for post in PostVIEWSTest.posts:
            response_det = self.guest_client.get(
                reverse('posts:post_detail', args=[post.id]))
            self.assertTemplateUsed(response_det, 'posts/post_detail.html')
            response_aut = self.author_client.get(
                reverse('posts:post_edit', kwargs={'post_id': f'{post.id}'}))
            self.assertTemplateUsed(response_aut, 'posts/create_post.html')

    def test_index_correct_context(self):
        """Проверка контекста шаблона index.html."""
        response = self.guest_client.get(reverse('posts:index'))
        post = response.context['posts'].order_by('-id')
        for i in range(len(self.posts)):
            self.assertEqual(post[i].text, self.posts[i].text)
            self.assertEqual(post[i].id, self.posts[i].id)
        self.assertEqual(response.context['page_title'],
                         'Последние обновления на сайте')

    def test_group_correct_context(self):
        """Проверка контекста шаблона group_list.html."""
        response = self.guest_client.get(reverse('posts:group_list',
                                                 kwargs={
                                                     'slug': self.group.slug}))
        post = response.context['posts'].order_by('-id')
        for i in range(len(self.posts_gr)):
            self.assertEqual(post[i].group.title,
                             self.group.title)
            self.assertEqual(post[i].text,
                             self.posts_gr[i].text)
            self.assertEqual(response.context['page_title'],
                             f'Записи сообщества {self.group.slug}')
            self.assertEqual(response.context['gr_descr'],
                             f'{self.group.description}')

    def test_profile_correct_context(self):
        """Проверка контекста шаблона profile.html."""
        response = self.guest_client. \
            get(reverse('posts:profile',
                        kwargs={'username': PostVIEWSTest.user}))
        post = response.context['posts'].order_by('-id')
        for i in range(len(PostVIEWSTest.posts)):
            self.assertEqual(post[i].author.username,
                             f'{self.posts[i].author.username}')
            self.assertEqual(post[i].text,
                             f'{self.posts[i].text}')

    def test_post_detail_correct_context(self):
        """Проверка контекста шаблона post_detail.html."""
        for i in range(len(PostVIEWSTest.posts)):
            response = self.guest_client. \
                get(reverse('posts:post_detail',
                            args=[PostVIEWSTest.posts[i].id]))
            self.assertEqual(response.context['post'], self.posts[i])
            self.assertEqual(response.context['id'], self.posts[i].id)
            self.assertEqual(response.context['page_title'],
                             self.posts[i].text[:30])

    def posts_forms(self, response):
        """Модуль проверки форм постов."""
        PostForm.fields = {'text': forms.fields.CharField,
                           'group': forms.fields.ChoiceField,
                           }
        for value, expected in PostForm.fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_form(self):
        """Проверка формы редактирования поста."""
        for i in range(len(PostVIEWSTest.posts)):
            response = self.author_client. \
                get(reverse('posts:post_edit',
                            args=[PostVIEWSTest.posts[i].id]))
            self.assertEqual(response.context['post'], self.posts[i])
            self.assertEqual(response.context['id'], self.posts[i].id)
            self.assertEqual(response.context['is_edit'], True)

    def test_post_create_correct_form(self):
        """Проверка формы создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.posts_forms(response)

    def test_new_post_correct_context(self):
        """Проверка нового поста."""
        response = self.author_client.get(reverse('posts:index'))
        new_post = response.context['posts'].order_by('-id')[0]
        self.assertEqual(new_post.text, self.posts[0].text)
        self.assertEqual(new_post.id, self.posts[0].id)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.new_group.slug}))
        post_new_gr = response.context['page_obj'][0]
        self.assertEqual(post_new_gr.text, self.post_n_gr[0].text)
        self.assertEqual(post_new_gr.id, self.post_n_gr[0].id)
        self.assertEqual(post_new_gr.group.title,
                         self.post_n_gr[0].group.title)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': PostVIEWSTest.user.username}))
        post_prf = response.context['posts'].order_by('-id')[0]
        self.assertEqual(post_prf.author.username,
                         self.posts_prf[0].author.username)
        self.assertEqual(post_prf.text, self.posts_prf[0].text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """ Создаем тестовые экземпляры постов."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pagin')
        cls.pag_group = Group.objects.create(
            title='pag_test_group',
            slug='pag_test_slug',
            description='Pag_TestingDescription'
        )

        pag_post_list = [Post(author=cls.user,
                              text=f'#_{i}__Pag_TestTextTextTextText',
                              group=cls.pag_group,
                              ) for i in range(1, 14)]

        Post.objects.bulk_create(pag_post_list)
        cls.pag_posts = Post.objects.all()

    def setUp(self):
        """Создаем авторизованного и неавторизованного клиента"""
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PaginatorViewsTest.user)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        response = self.author_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), per_page)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.pag_group.slug}))
        self.assertEqual(len(response.context['page_obj']), per_page)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': PaginatorViewsTest.user}))
        self.assertEqual(len(response.context['page_obj']), per_page)

    def test_second_page_contains_three_records(self):
        """Проверка: количество постов на второй странице равно 3."""
        response = self.author_client.get(reverse('posts:index')
                                          + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)

        response = self.author_client. \
            get(reverse('posts:group_list',
                        kwargs={'slug': self.pag_group.slug})
                + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)

        response = self.author_client. \
            get(reverse('posts:profile',
                        kwargs={'username': PaginatorViewsTest.user})
                + '?page=2')
        self.assertEqual(len(response.context['page_obj']),
                         len(self.pag_posts) - per_page)
