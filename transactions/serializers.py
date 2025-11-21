from rest_framework import serializers


class SummaryPointSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.IntegerField()
