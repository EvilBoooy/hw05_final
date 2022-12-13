import shutil

from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from http import HTTPStatus

from posts.models import Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Author1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Группа 1',
            slug='test-slug',
            description='Описание группы 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_create_post_with_picture(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostCreateFormTests.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Какой-то текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': PostCreateFormTests.user})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])

    def test_post_edit(self):
        form_data = {
            'text': 'Какой-то текст',
            'group': self.group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(pk=self.group.pk)
        self.client.get(f'/posts/{post_edit.pk}/edit/')
        form_data = {
            'text': 'Я что-то поменял и всё снова сломалось',
            'group': self.group.pk
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': post_edit.pk
                    }),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(pk=self.group.pk)
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_edit.text,
                         'Я что-то поменял и всё снова сломалось')
