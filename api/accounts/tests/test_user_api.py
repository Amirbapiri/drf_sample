from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("api_v1:accounts_create")
TOKEN_URL = reverse("api_v1:accounts_token")
USER_ME = reverse("api_v1:accounts_me")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITest(TestCase):
    """
    Test the users API (public)
    """

    def setUp(self) -> None:
        self.client = APIClient()
        self.VALID_PAYLOAD = {
            "email": "test@test.com",
            "password": "simple",
            "name": "test name",
        }

        self.INVALID_PAYLOAD = {
            "email": "test_invalid@test.com",
            "password": "simple_invalid",
            "name": "test invalid name",
        }

    def test_create_valid_user_success(self):
        res = self.client.post(CREATE_USER_URL, self.VALID_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(self.VALID_PAYLOAD["password"]))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        create_user(**self.VALID_PAYLOAD)

        res = self.client.post(CREATE_USER_URL, self.VALID_PAYLOAD)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """
        Test that the password must be more that 5 characters.
        """
        self.VALID_PAYLOAD["password"] = "sim"
        res = self.client.post(CREATE_USER_URL, self.VALID_PAYLOAD)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        user_exists = get_user_model().objects.filter(
            email=self.VALID_PAYLOAD["email"]
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token created for a specific user"""
        create_user(**self.VALID_PAYLOAD)
        res = self.client.post(TOKEN_URL, self.VALID_PAYLOAD)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_invalid_credentials(self):
        """Test that token is not created when passed an invalid credentials"""
        create_user(**self.VALID_PAYLOAD)
        res = self.client.post(TOKEN_URL, self.INVALID_PAYLOAD)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test create payload when user does not exists"""
        res = self.client.post(TOKEN_URL, self.VALID_PAYLOAD)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        self.VALID_PAYLOAD["password"] = ""
        res = self.client.post(TOKEN_URL, self.VALID_PAYLOAD)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(USER_ME)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserAPITests(TestCase):
    """Test API requests that requires user to be authenticated"""

    def setUp(self) -> None:
        self.VALID_PAYLOAD = {
            "email": "test@test.com",
            "password": "simple",
            "name": "test name",
        }
        self.client = APIClient()
        self.user = create_user(
            **self.VALID_PAYLOAD
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(USER_ME)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name,
        })

    def test_post_method_not_allowed(self):
        res = self.client.post(USER_ME, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {
            'name': 'new test name',
            'password': 'new_password',
        }

        res = self.client.patch(USER_ME, payload)

        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload["name"])
        self.assertEqual(self.user.email, self.VALID_PAYLOAD["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
