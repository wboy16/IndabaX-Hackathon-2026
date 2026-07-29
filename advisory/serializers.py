from rest_framework import serializers

class ChatAgentRequestSerializer(serializers.Serializer):
    """Request schema for conversational LLM advisor agent endpoint."""
    query = serializers.CharField(
        required=True,
        help_text="Farmer's question or scenario (e.g., 'Is my camp in Omaheke overgrazed?')"
    )
    region = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Khomas",
        help_text="Namibian region (e.g. Khomas, Omaheke, Otjozondjupa, Zambezi)"
    )
    latitude = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Geographic latitude coordinate"
    )
    longitude = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Geographic longitude coordinate"
    )
    land_tenure = serializers.ChoiceField(
        choices=["Commercial", "Communal", "Conservancy"],
        required=False,
        allow_blank=True,
        default="Commercial",
        help_text="Land tenure classification"
    )
    herd_size = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Total livestock count in Large Stock Units (LSU) or head count"
    )
    farm_size_ha = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Total farm or camp size in hectares"
    )

class WeatherRequestSerializer(serializers.Serializer):
    """Request schema for live weather API endpoint."""
    region = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)

class DatasetQueryRequestSerializer(serializers.Serializer):
    """Request schema for dataset query endpoint."""
    region = serializers.CharField(required=False, allow_blank=True)
    land_tenure = serializers.CharField(required=False, allow_blank=True)
    constituency = serializers.CharField(required=False, allow_blank=True)

class STTRequestSerializer(serializers.Serializer):
    """Request schema for Speech-to-Text webhook/endpoint."""
    audio_file = serializers.FileField(required=False)
    audio_base64 = serializers.CharField(required=False, allow_blank=True)
    language = serializers.CharField(required=False, default="en")

class TTSRequestSerializer(serializers.Serializer):
    """Request schema for Text-to-Speech synthesis webhook/endpoint."""
    text = serializers.CharField(required=True, help_text="Text to convert into spoken audio advice")
    voice = serializers.CharField(required=False, default="en-female-1")
    language = serializers.CharField(required=False, default="en")
