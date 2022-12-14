import tempfile
import shutil

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms

from ..models import Group, Post, Follow, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Author1')
        cls.authorized_client = Client()
        cls.author = User.objects.create(username='Author2')
        cls.authorized_author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_author.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Группа 1',
            slug='test-slug',
            description='Описание группы 1',
        )
        cls.second_group = Group.objects.create(
            title='Группа 2',
            slug='test-slug-new',
            description='Описание группы 2'
        )
        cls.post = Post.objects.bulk_create(
            [Post(
                text='Записи группы 1',
                author=cls.author,
                group=cls.group,
                image=uploaded
            )] * 15
        )
        cls.post = Post.objects.bulk_create(
            [Post(
                text='Записи группы 2',
                author=cls.user,
                group=cls.second_group,
                image=uploaded,
            )] * 4
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': 'Author1'}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': 4}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': 11}):
            'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        post_image = Post.objects.first().image
        self.assertTrue(post_image, 'posts/small.gif')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)
        self.assertIn('posts', response.context)
        post_image = Post.objects.first().image
        self.assertTrue(post_image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Author1'})
        )
        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)
        self.assertIn('posts', response.context)
        self.assertIn('page_obj', response.context)
        post_image = Post.objects.first().image
        self.assertTrue(post_image, 'posts/small.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 7})
        )
        self.assertIn('post', response.context)
        post_image = Post.objects.first().image
        self.assertTrue(post_image, 'posts/small.gif')

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_add_comment_not_guest(self):
        """Авторизованный пользователь может комментить"""
        coments = {'text': 'какой-то коммент'}
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 3}),
            data=coments, follow=True
        )
        response = self.authorized_client.get(f'{"/posts/3/"}')
        self.assertContains(response, coments['text'])

    def test_add_comment_guest(self):
        """Гости комментить не могут"""
        coments = {'text': 'тут мог быть ваш коммент'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': 17}),
            data=coments, follow=True
        )
        response = self.guest_client.get(f'{"/posts/17/"}')
        self.assertNotContains(response, coments['text'])

    def test_cache_index(self):
        """Тест кэша главной страницы(index)"""
        response = self.authorized_author.get(reverse('posts:index'))
        post = response.content
        Post.objects.create(
            text='Какой-то текст',
            author=self.author,
        )
        first = self.authorized_author.get(reverse('posts:index'))
        first_post = first.content
        self.assertEqual(first_post, post)
        cache.clear()
        second = self.authorized_author.get(reverse('posts:index'))
        second_post = second.content
        self.assertNotEqual(first_post, second_post)

    def test_paginator_first_page_contains_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_paginator_second_page_contains_nine_records(self):
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 9)

    def test_paginator_group_list_contains_four_records(self):
        response = self.guest_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug-new'})
        )
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_paginator_profile_contains_four_records(self):
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': 'Author1'})
        )
        self.assertEqual(len(response.context['page_obj']), 4)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create(username='follower')
        self.user_following = User.objects.create(username='following')
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)
        self.post = Post.objects.create(
            author=self.user_following,
            text='Какая-то запись для тестов'
        )

    def test_follow(self):
        '''Тест подписки'''
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        '''Тест отписки'''
        self.client_auth_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.client_auth_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_sub_post(self):
        """Саб видит запись"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_follower.get('/follow/')
        post = response.context['page_obj'][0].text
        self.assertEqual(post, 'Какая-то запись для тестов')

    def test_unsub_post(self):
        """Ансаб не видит запись"""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client_auth_following.get('/follow/')
        self.assertNotEqual(response, 'Какая-то запись для тестов')
