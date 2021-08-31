from django.test import TestCase
from django.contrib.auth import get_user_model


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        email = "test@test.com"
        password = "simple"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_with_normalized_email(self):
        email = "test@test.com"
        user = get_user_model().objects.create_user(
            email, "simple"
        )
        self.assertEqual(user.email, email.lower())

    def test_new_user_with_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                None,
                "simple"
            )

    def test_create_new_superuser(self):
        user = get_user_model().objects.create_superuser(
            email="superuser@test.com",
            password="simple",
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
