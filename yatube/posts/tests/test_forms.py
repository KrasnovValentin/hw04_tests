from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group

User = get_user_model()


class PostsCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.new_group = Group.objects.create(
            title='SuperNewGroupTitle',
            slug='super_group_slug',
            description='NewDescriptionSuperGroup'
        )
        Post.objects.create(
            text='Super newest testing texxxxt',
            author=cls.user,
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create(self):
        """Добавляем пост в базу данных."""
        posts_count = Post.objects.count()

        form_data = {
            'text': '#2 Super newest testing texxxxt',
            'group': self.new_group.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, '/auth/login/?next=/create/')

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.all().count(), posts_count + 1)
        self.assertEqual(Post.objects.order_by('-id')[0].group.id,
                         form_data['group'])

    def test_post_edit(self):
        """Редактируем пост в базе данных."""
        post1 = Post.objects.all()[0]
        response = self.guest_client.get(
            reverse('posts:post_edit', args=[post1.id])
        )
        self.assertRedirects(response, '/auth/login/?next=/posts/1/edit/')

        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[post1.id])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK.value)

        form_data = {
            'text': '#2 AfterEdit--Super newest testing texxxxt',
            'group': self.new_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[post1.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[post1.id]))
        self.assertEqual(form_data['text'], Post.objects.all()[0].text)
