import logging

from django import forms
from django.contrib import messages
from django.db import DatabaseError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import resolve, reverse

from .forms import SorryPageForm, validate_image_file, validate_video_file
from .models import PeopleMessage, SorryPage, SorryPhoto

logger = logging.getLogger(__name__)

PEOPLE_RELATIONSHIPS = ["দেবর", "ননদ", "Cousin", "Friend", "Brother", "Sister", "Mother", "Father", "Family", "Other", "Baby"]


def home(request):
    return render(request, "home.html")


def create_page(request):
    if request.method == "POST":
        logger.info(
            "Create submission received: path=%s fields=%d files=%d",
            request.path,
            len(request.POST),
            len(request.FILES),
        )
        form = SorryPageForm(request.POST, request.FILES)
        gallery_files = request.FILES.getlist("photos")
        gallery_error = None
        if len(gallery_files) > 5:
            gallery_error = "Please choose no more than 5 photos."
        else:
            try:
                for photo in gallery_files:
                    validate_image_file(photo)
            except forms.ValidationError as error:
                gallery_error = error.messages[0]
        people_uploads = []
        people_error = None
        selected_relationships = request.POST.getlist("people_relationship")
        for relationship in selected_relationships:
            if relationship not in PEOPLE_RELATIONSHIPS:
                people_error = "Please choose a valid relationship."
                break
            maximum = 3 if relationship == "Baby" else 10
            try:
                count = int(request.POST.get(f"people_count_{relationship}", "1"))
            except (TypeError, ValueError):
                people_error = "Please choose a valid number of people."
                break
            if count < 1 or count > maximum:
                people_error = f"Please choose between 1 and {maximum} people for {relationship}."
                break
            for index in range(count):
                prefix = f"people_{relationship}_{index}"
                name = request.POST.get(f"{prefix}_name", "").strip()[:100]
                video = request.FILES.get(f"{prefix}_video")
                if not video:
                    people_error = f"Please upload a video for {relationship} #{index + 1}."
                    break
                try:
                    validate_video_file(video)
                except forms.ValidationError as error:
                    people_error = error.messages[0]
                    break
                people_uploads.append((relationship, name, video))
            if people_error:
                break
        if form.is_valid() and not gallery_error and not people_error:
            try:
                with transaction.atomic():
                    page = form.save()
                    for order, photo in enumerate(gallery_files):
                        SorryPhoto.objects.create(sorry_page=page, image=photo, order=order)
                    for order, (relationship, name, video) in enumerate(people_uploads):
                        PeopleMessage.objects.create(
                            sorry_page=page,
                            relationship=relationship,
                            name=name,
                            video=video,
                            order=order,
                        )
                    if not _saved_media_is_valid(page):
                        raise ValueError("One or more uploaded files could not be saved.")
                    preview_url = reverse("sorry:preview", kwargs={"slug": page.slug})
                    if not page.slug or not preview_url or resolve(preview_url).url_name != "preview":
                        raise ValueError("The preview URL could not be generated.")
                messages.success(request, "Your page passed validation and was saved successfully.")
                logger.info("Create submission saved successfully: slug=%s", page.slug)
                return redirect("sorry:preview", slug=page.slug)
            except (DatabaseError, OSError, ValueError) as error:
                logger.exception("Create submission failed during save or verification")
                form.add_error(None, "Could not save your page safely. Check the upload and try again.")
        elif request.method == "POST":
            logger.warning(
                "Create submission rejected: form_valid=%s gallery_error=%s people_error=%s errors=%s",
                form.is_valid(),
                bool(gallery_error),
                bool(people_error),
                form.errors.as_json(),
            )
        if gallery_error:
            form.add_error(None, gallery_error)
        if people_error:
            form.add_error(None, people_error)
    else:
        form = SorryPageForm()
    return render(request, "builder.html", {"form": form, "people_relationships": PEOPLE_RELATIONSHIPS})


def preview_page(request, slug):
    page = get_object_or_404(SorryPage, slug=slug)
    return render(request, "saved_preview.html", {"page": page})


def publish_page(request, slug):
    page = get_object_or_404(SorryPage, slug=slug)
    if request.method == "POST":
        if not _page_is_publishable(page):
            messages.error(request, "This page still needs a valid saved file or required field before publishing.")
            return redirect("sorry:preview", slug=page.slug)
        try:
            page.is_published = True
            page.save(update_fields=["is_published", "updated_at"])
            public_url = request.build_absolute_uri(reverse("sorry:public", kwargs={"slug": page.slug}))
            if not page.is_published or not public_url or resolve(reverse("sorry:public", kwargs={"slug": page.slug})).url_name != "public":
                raise ValueError("The public URL could not be verified.")
        except (DatabaseError, OSError, ValueError) as error:
            logger.exception("Publish failed: slug=%s", page.slug)
            messages.error(request, "Publishing failed. Please try again.")
            return redirect("sorry:preview", slug=page.slug)
        messages.success(request, f"Published successfully: {public_url}")
        logger.info("Publish succeeded: slug=%s public_url=%s", page.slug, public_url)
        return redirect("sorry:published", slug=page.slug)
    return redirect("sorry:preview", slug=page.slug)


def published_page(request, slug):
    page = get_object_or_404(SorryPage, slug=slug, is_published=True)
    public_url = request.build_absolute_uri(f"/s/{page.slug}/")
    share_image_url = request.build_absolute_uri("/static/images/share-preview.jpg")
    gallery_photos = [
        {"url": photo.image.url, "caption": photo.caption, "alt": photo.caption or "A special memory"}
        for photo in page.photos.all()
        if photo.image
    ]
    if page.photo and not any(item["url"].endswith(page.photo.name) for item in gallery_photos):
        gallery_photos.insert(0, {
            "url": page.photo.url,
            "caption": page.photo_caption,
            "alt": page.photo_caption or "A special memory",
        })
    sorry_video = page.sorry_video or page.video
    memory_video = page.memory_video
    people_messages = [
        {
            "relationship": message.relationship,
            "name": message.name or ("A Little Message From Baby ❤️" if message.relationship == "Baby" else "Someone from your family ❤️"),
            "video": message.video,
            "is_baby": message.relationship == "Baby",
        }
        for message in page.people_messages.all()
        if message.video
    ]
    return render(
        request,
        "public_page.html",
        {
            "page": page,
            "public_url": public_url,
            "share_image_url": share_image_url,
            "gallery_photos": gallery_photos,
            "sorry_video": sorry_video,
            "memory_video": memory_video,
            "people_messages": people_messages,
        },
    )


def published_success(request, slug):
    page = get_object_or_404(SorryPage, slug=slug, is_published=True)
    public_url = request.build_absolute_uri(f"/s/{page.slug}/")
    return render(request, "published.html", {"page": page, "public_url": public_url})


def _stored_file_is_valid(field_file):
    return bool(field_file and field_file.name and field_file.storage.exists(field_file.name) and field_file.size > 0)


def _saved_media_is_valid(page):
    fields = (page.photo, page.video, page.sorry_video, page.memory_video)
    if any(field and not _stored_file_is_valid(field) for field in fields):
        return False
    return all(_stored_file_is_valid(message.video) for message in page.people_messages.all())


def _page_is_publishable(page):
    return bool(page.her_name.strip() and page.your_name.strip() and page.sorry_message.strip()
                and page.theme in {"romantic", "cute", "dark", "emotional"}
                and _saved_media_is_valid(page))
