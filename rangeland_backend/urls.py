from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def root_api_index(request):
    return JsonResponse({
        "project": "AI Agent for Rangeland & Livestock Advisory Backend",
        "event": "Deep Learning IndabaX Namibia 2026 Hackathon",
        "status": "operational",
        "endpoints": {
            "health": "/api/health/",
            "chat_agent": "/api/chat/",
            "weather": "/api/weather/",
            "dataset_query": "/api/data/",
            "stt_speech_to_text": "/api/stt/",
            "tts_text_to_speech": "/api/tts/",
        },
        "documentation": "See README.md for complete frontend & ML integration guidelines."
    })

urlpatterns = [
    path('', root_api_index, name='root_api_index'),
    path('admin/', admin.site.urls),
    path('api/', include('advisory.urls')),
]
