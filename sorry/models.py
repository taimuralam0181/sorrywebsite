import uuid

from django.db import models


def generate_page_slug():
    return uuid.uuid4().hex


class SorryPage(models.Model):
    slug = models.CharField(max_length=32, unique=True, default=generate_page_slug, editable=False)
    her_name = models.CharField(max_length=100)
    your_name = models.CharField(max_length=100)
    theme = models.CharField(max_length=20, default="romantic")
    sorry_message = models.TextField()
    letter_title = models.CharField(max_length=160, blank=True)
    letter_body = models.TextField(blank=True)
    signature = models.CharField(max_length=160, blank=True)
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    photo_caption = models.CharField(max_length=200, blank=True)
    video = models.FileField(upload_to="videos/", blank=True, null=True)
    sorry_video = models.FileField(upload_to="videos/", blank=True, null=True)
    memory_video = models.FileField(upload_to="videos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"Sorry page for {self.her_name}"


class SorryPhoto(models.Model):
    sorry_page = models.ForeignKey(SorryPage, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="photos/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at", "id"]

    def __str__(self):
        return f"Memory for {self.sorry_page.her_name}"


class PeopleMessage(models.Model):
    sorry_page = models.ForeignKey(SorryPage, on_delete=models.CASCADE, related_name="people_messages")
    relationship = models.CharField(max_length=50)
    name = models.CharField(max_length=100, blank=True)
    video = models.FileField(upload_to="people_messages/")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at", "id"]

    def __str__(self):
        return f"{self.relationship} message for {self.sorry_page.her_name}"
