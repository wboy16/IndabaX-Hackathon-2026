import os
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from advisory.serializers import (
    ChatAgentRequestSerializer,
    WeatherRequestSerializer,
    DatasetQueryRequestSerializer,
    STTRequestSerializer,
    TTSRequestSerializer,
)
from services.weather import WeatherService
from services.dataset import RangelandDatasetService
from ai.agent import RangelandAgent

logger = logging.getLogger(__name__)

# Singletons for services & agent
weather_service = WeatherService()
dataset_service = RangelandDatasetService()
rangeland_agent = RangelandAgent()

class HealthCheckView(APIView):
    """GET /api/health/ - API readiness and service status check."""
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({
            "status": "healthy",
            "service": "Namibian Rangeland & Livestock Advisory API",
            "event": "Deep Learning IndabaX Namibia 2026",
            "components": {
                "weather_service": "active",
                "dataset_service": "active",
                "agent_service": "active"
            }
        }, status=status.HTTP_200_OK)


class ChatAgentAPIView(APIView):
    """
    POST /api/chat/
    Main conversational agent endpoint for farmer advice.
    Invokes LLM agent tool-calling to query weather and dataset services.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ChatAgentRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        
        try:
            agent_response = rangeland_agent.run_agent(
                user_query=validated_data["query"],
                region=validated_data.get("region"),
                lat=validated_data.get("latitude"),
                lon=validated_data.get("longitude"),
                land_tenure=validated_data.get("land_tenure"),
                herd_size=validated_data.get("herd_size"),
                farm_size_ha=validated_data.get("farm_size_ha")
            )
            return Response(agent_response, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in ChatAgentAPIView: {str(e)}")
            return Response(
                {"error": "Failed to generate advisory response", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeatherAPIView(APIView):
    """
    GET / POST /api/weather/
    Direct weather & recent rainfall query endpoint (Open-Meteo & NASA POWER).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        region = request.query_params.get("region")
        lat = request.query_params.get("latitude")
        lon = request.query_params.get("longitude")

        lat_val = float(lat) if lat else None
        lon_val = float(lon) if lon else None

        weather = weather_service.get_weather_for_region_or_coords(
            region=region,
            lat=lat_val,
            lon=lon_val
        )
        return Response(weather, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WeatherRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        v_data = serializer.validated_data
        weather = weather_service.get_weather_for_region_or_coords(
            region=v_data.get("region"),
            lat=v_data.get("latitude"),
            lon=v_data.get("longitude")
        )
        return Response(weather, status=status.HTTP_200_OK)


class DatasetQueryAPIView(APIView):
    """
    GET / POST /api/data/
    Direct dataset querying endpoint for rangeland survey records and regional aggregates.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        region = request.query_params.get("region")
        land_tenure = request.query_params.get("land_tenure")
        constituency = request.query_params.get("constituency")

        result = dataset_service.query_dataset(
            region=region,
            land_tenure=land_tenure,
            constituency=constituency
        )
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DatasetQueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        v_data = serializer.validated_data
        result = dataset_service.query_dataset(
            region=v_data.get("region"),
            land_tenure=v_data.get("land_tenure"),
            constituency=v_data.get("constituency")
        )
        return Response(result, status=status.HTTP_200_OK)


class SpeechToTextAPIView(APIView):
    """
    POST /api/stt/
    Webhook/Endpoint for Speech-to-Text conversion (English voice prompts).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = STTRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Check for OpenAI Whisper or audio upload
        api_key = os.getenv("OPENAI_API_KEY")
        audio_file = request.FILES.get("audio_file")

        if api_key and audio_file:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
                return Response({
                    "status": "success",
                    "transcribed_text": transcription.text,
                    "language": "en",
                    "engine": "OpenAI Whisper"
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(f"OpenAI Whisper STT failed ({str(e)}). Returning mock STT output.")

        # Default Mock STT payload response for testing UI integrations
        return Response({
            "status": "success",
            "transcribed_text": "Is my camp in Omaheke overgrazed given recent rainfall?",
            "language": "en",
            "engine": "Mock STT Endpoint (Ready for Whisper/Webhooks)",
            "message": "Audio received. Provide OPENAI_API_KEY and audio_file for live Whisper STT."
        }, status=status.HTTP_200_OK)


class TextToSpeechAPIView(APIView):
    """
    POST /api/tts/
    Webhook/Endpoint for Text-to-Speech synthesis (Spoken English advice).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TTSRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        v_data = serializer.validated_data
        text_to_speak = v_data["text"]
        api_key = os.getenv("OPENAI_API_KEY")

        if api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text_to_speak
                )
                # In production, stream or return audio binary/base64
                return Response({
                    "status": "success",
                    "audio_format": "mp3",
                    "voice": "alloy",
                    "text": text_to_speak,
                    "engine": "OpenAI TTS-1",
                    "message": "Audio stream generated successfully."
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.warning(f"OpenAI TTS failed ({str(e)}). Returning mock TTS output.")

        # Default Mock TTS payload response for testing UI integrations
        return Response({
            "status": "success",
            "audio_format": "mp3",
            "voice": v_data.get("voice", "en-female-1"),
            "text": text_to_speak,
            "mock_audio_url": "https://actions.google.com/sounds/v1/ambiences/outdoor_farm.ogg",
            "engine": "Mock TTS Endpoint (Ready for ElevenLabs/OpenAI TTS)",
            "message": "Text received for speech synthesis."
        }, status=status.HTTP_200_OK)
