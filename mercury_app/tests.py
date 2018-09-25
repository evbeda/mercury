from django.test import TestCase
from social_django.models import UserSocialAuth
from django.contrib.auth import get_user_model


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(
            username='mercury_user',
            password='the_best_password_of_ever',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        self.user.set_password('the_best_password_of_ever_2')
        self.user.save()
        self.auth = UserSocialAuth.objects.create(
            user=self.user, provider='eventbrite', uid="563480245671"
        )
        login = self.client.login(username='mercury_user', password='the_best_password_of_ever_2')
        return login


class HomeViewTest(TestBase):

    def setUp(self):
        super(HomeViewTest, self).setUp()

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
