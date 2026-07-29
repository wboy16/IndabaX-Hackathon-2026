from django.test import TestCase, Client
from django.urls import reverse
import json

class AdvisoryAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('api_health'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_weather_endpoint(self):
        response = self.client.get(reverse('api_weather'), {'region': 'Khomas'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("past_14_days_total_rainfall_mm", data)

    def test_dataset_query_endpoint(self):
        response = self.client.get(reverse('api_data'), {'region': 'Omaheke'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["found"])
        self.assertGreater(data["record_count"], 0)

    def test_chat_agent_endpoint(self):
        payload = {
            "query": "Is my camp in Omaheke overgrazed?",
            "region": "Omaheke",
            "land_tenure": "Commercial",
            "herd_size": 150,
            "farm_size_ha": 1200.0
        }
        response = self.client.post(
            reverse('api_chat'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["reasoning_explained"])
        self.assertIn("advice", data)
        self.assertIn("tools_executed", data)

    def test_stt_endpoint(self):
        response = self.client.post(
            reverse('api_stt'),
            data=json.dumps({"language": "en"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")

    def test_tts_endpoint(self):
        payload = {"text": "Move cattle to rest camp 4 based on recent rainfall."}
        response = self.client.post(
            reverse('api_tts'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
