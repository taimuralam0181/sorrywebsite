from io import BytesIO
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image

from .models import SorryPage


class SorryPageValidationTests(TestCase):
    def image_upload(self, name="memory.png"):
        stream = BytesIO()
        Image.new("RGB", (2, 2), "pink").save(stream, format="PNG")
        return SimpleUploadedFile(name, stream.getvalue(), content_type="image/png")

    def video_upload(self, name="sorry.mp4", content=b"video"):
        return SimpleUploadedFile(name, content, content_type="video/mp4")

    def valid_data(self):
        return {
            "her_name": "Tania",
            "your_name": "Taimur",
            "theme": "romantic",
            "sorry_message": "I am truly sorry.",
            "letter_title": "I'm Sorry",
            "letter_body": "Please forgive me.",
            "signature": "Taimur",
            "photo_caption": "Our memory",
        }

    def test_valid_uploads_create_page_and_public_data(self):
        response = self.client.post(
            "/create/",
            {**self.valid_data(), "photos": [self.image_upload()], "sorry_video": self.video_upload()},
        )
        self.assertRedirects(response, "/preview/" + SorryPage.objects.get().slug + "/")
        page = SorryPage.objects.get()
        self.assertTrue(page.sorry_video)
        self.assertTrue(page.photos.exists())

    def test_empty_upload_is_rejected(self):
        response = self.client.post(
            "/create/",
            {**self.valid_data(), "photos": [SimpleUploadedFile("empty.png", b"", content_type="image/png")]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SorryPage.objects.count(), 0)
        self.assertContains(response, "non-empty image file")

    def test_failed_media_verification_does_not_leave_page(self):
        with patch("sorry.views._saved_media_is_valid", return_value=False):
            response = self.client.post("/create/", self.valid_data())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SorryPage.objects.count(), 0)

    def test_saved_page_can_be_published_and_verified(self):
        response = self.client.post("/create/", self.valid_data())
        page = SorryPage.objects.get()
        self.assertRedirects(response, f"/preview/{page.slug}/")
        response = self.client.post(f"/preview/{page.slug}/publish/")
        self.assertRedirects(response, f"/published/{page.slug}/")
        page.refresh_from_db()
        self.assertTrue(page.is_published)
        public_response = self.client.get(f"/s/{page.slug}/")
        self.assertEqual(public_response.status_code, 200)

    def test_invalid_form_stays_on_builder_and_preserves_input(self):
        response = self.client.post(
            "/create/",
            {"her_name": "Still entered", "your_name": "", "theme": "romantic", "sorry_message": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Still entered")
        self.assertContains(response, "Please check the highlighted details.")
