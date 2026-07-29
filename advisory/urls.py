from django.urls import path
from advisory.views import (
    HealthCheckView,
    ChatAgentAPIView,
    WeatherAPIView,
    DatasetQueryAPIView,
    SpeechToTextAPIView,
    TextToSpeechAPIView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='api_health'),
    path('chat/', ChatAgentAPIView.as_view(), name='api_chat'),
    path('weather/', WeatherAPIView.as_view(), name='api_weather'),
    path('data/', DatasetQueryAPIView.as_view(), name='api_data'),
    path('stt/', SpeechToTextAPIView.as_view(), name='api_stt'),
    path('tts/', TextToSpeechAPIView.as_view(), name='api_tts'),
]
