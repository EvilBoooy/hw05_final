from django.test import TestCase, Client

from http import HTTPStatus

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Author1')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = User.objects.create_user(username='Author2')
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовая запись',
            group=cls.group,
        )

    def test_urls_uses_correct_template_not_guest(self):
        """URL-адрес использует нужный шаблон при вошедшем пользователе."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/profile/{self.user}/': 'posts/profile.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_author(self):
        """URL-адрес использует нужный шаблон при вошедшем авторе."""
        templates_url_names = {
            '/create/': 'posts/create_post.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_404(self):
        '''Cтраница 404 отдаёт кастомный шаблон'''
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_url_exist_at_desired_location(self):
        """Страница /group/<slug> доступна любому пользователю."""
        response = self.guest_client.get('/group/test-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_url_exist_at_desired_location(self):
        """Страница /posts/<post_id> доступна любому пользователю."""
        response = self.guest_client.get('/posts/1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_username_url_exists_at_desired_location(self):
        """Страница /profile/<author> доступна любому пользователю."""
        response = self.guest_client.get('/profile/Author1/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_url(self):
        """Страница /unexisting_page/ выдаёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/ доступна автору."""
        response = self.authorized_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
