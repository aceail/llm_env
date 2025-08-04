from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from inference.models import InferenceResult


class EvaluationFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="pass")
        self.client.login(username="tester", password="pass")

        self.old_result = InferenceResult.objects.create(
            system_prompt="",
            user_prompt="old",
            image_urls=[],
            llm_output={},
            solution_name="old",
        )
        self.old_result.created_at = timezone.now() - timedelta(days=10)
        self.old_result.save(update_fields=["created_at"])

        self.new_result = InferenceResult.objects.create(
            system_prompt="",
            user_prompt="new",
            image_urls=[],
            llm_output={},
            solution_name="new",
        )

    def test_evaluation_list_filters_by_date(self):
        start = (timezone.now() - timedelta(days=1)).date().isoformat()
        response = self.client.get(reverse("evaluation") + f"?start_date={start}")
        expected_url = reverse("evaluation_detail", args=[self.new_result.pk]) + f"?start_date={start}"
        self.assertRedirects(response, expected_url)
