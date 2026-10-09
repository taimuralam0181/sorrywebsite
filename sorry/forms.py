from pathlib import Path

from django import forms
from PIL import Image, UnidentifiedImageError

from .models import SorryPage


MAX_IMAGE_SIZE = 5 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm"}


def validate_image_file(photo):
    if not photo or not photo.name or photo.size <= 0:
        raise forms.ValidationError("Please choose a non-empty image file.")
    extension = Path(photo.name).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise forms.ValidationError("Please upload a JPG, JPEG, PNG, or WEBP image.")
    if photo.size > MAX_IMAGE_SIZE:
        raise forms.ValidationError("Please choose an image smaller than 5 MB.")
    if not photo.content_type or not photo.content_type.startswith("image/"):
        raise forms.ValidationError("That file is not a valid image.")
    try:
        image = Image.open(photo)
        image.verify()
    except (UnidentifiedImageError, OSError):
        raise forms.ValidationError("That file is not a valid image.")
    finally:
        photo.seek(0)
    return photo


def validate_video_file(video):
    if not video or not video.name or video.size <= 0:
        raise forms.ValidationError("Please choose a non-empty video file.")
    extension = Path(video.name).suffix.lower()
    if extension not in ALLOWED_VIDEO_EXTENSIONS:
        raise forms.ValidationError("Please upload an MP4 or WEBM video.")
    if video.size > MAX_VIDEO_SIZE:
        raise forms.ValidationError("Please choose a video smaller than 50 MB.")
    if video.content_type not in {"video/mp4", "video/webm"}:
        raise forms.ValidationError("That file is not a supported MP4 or WEBM video.")
    return video


class SorryPageForm(forms.ModelForm):
    photo = forms.FileField(required=False)
    video = forms.FileField(required=False)
    sorry_video = forms.FileField(required=False)
    memory_video = forms.FileField(required=False)

    class Meta:
        model = SorryPage
        fields = [
            "her_name",
            "your_name",
            "theme",
            "sorry_message",
            "letter_title",
            "letter_body",
            "signature",
            "photo",
            "photo_caption",
            "video",
            "sorry_video",
            "memory_video",
        ]

    def clean_theme(self):
        theme = self.cleaned_data["theme"]
        if theme not in {"romantic", "cute", "dark", "emotional"}:
            raise forms.ValidationError("Please choose one of the available themes.")
        return theme

    def clean_photo(self):
        photo = self.cleaned_data.get("photo")
        if not photo:
            return photo
        return validate_image_file(photo)

    def clean_video(self):
        return self._clean_video("video")

    def clean_sorry_video(self):
        return self._clean_video("sorry_video")

    def clean_memory_video(self):
        return self._clean_video("memory_video")

    def _clean_video(self, field_name):
        video = self.cleaned_data.get(field_name)
        if not video:
            return video
        return validate_video_file(video)
