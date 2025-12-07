from rest_framework import serializers
from data_api.models import Book

class BookSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField()
    author = serializers.CharField()
    publish_date = serializers.IntegerField()
    summary = serializers.CharField()

    def create(self, validated_data):
        return Book.objects.create(**validated_data)
    
    def update(self,instance,validated_data):
        instance.title = validated_data.get("title",instance.title)
        instance.author = validated_data.get("author",instance.author)
        instance.publish_date = validated_data.get("publish_date",instance.publish_date)
        instance.summary = validated_data.get("summary",instance.summary)
        instance.save()
        return instance