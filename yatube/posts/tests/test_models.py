from django.test import TestCase

from ..models import Group, Post, User
from ..const import TEXTLIM


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_model_group_have_correct_object_names(self):
        """Проверяем, что у модели group корректно работает __str__."""
        title = (
                (self.group, self.group.title),
        )
        for text, expected_name in title:
            with self.subTest(expected_name=text):
                self.assertEqual(expected_name, str(text))

    def test_model_post_have_correct_object_names(self):
        """Проверяем, что у модели post корректно работает __str__."""
        title = (
                (self.post, self.post.text[:TEXTLIM]),
        )
        for text, expected_name in title:
            with self.subTest(expected_name=text):
                self.assertEqual(expected_name, str(text))
