import os

import requests
from flask import Flask, render_template, request, url_for
from PIL import Image, ImageOps
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from werkzeug.utils import secure_filename


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOAD_FOLDER = os.path.join(STATIC_DIR, "uploads")
OCR_SPACE_URL = "https://api.ocr.space/parse/image"
BASE_MODEL_PATH = "microsoft/trocr-base-handwritten"

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

processor = TrOCRProcessor.from_pretrained(BASE_MODEL_PATH)
pretrained_model = VisionEncoderDecoderModel.from_pretrained(BASE_MODEL_PATH)
pretrained_model.eval()


def split_text_lines(image):
    gray = ImageOps.autocontrast(image.convert("L"))
    width, height = gray.size
    pixels = gray.load()
    scan_left = width // 10
    scan_right = width - scan_left
    minimum_dark_pixels = max(8, (scan_right - scan_left) // 50)
    active_rows = [
        sum(1 for x in range(scan_left, scan_right) if pixels[x, y] < 160)
        >= minimum_dark_pixels
        for y in range(height)
    ]

    max_gap = max(6, height // 75)
    y = 0
    while y < height:
        if active_rows[y]:
            y += 1
            continue
        gap_start = y
        while y < height and not active_rows[y]:
            y += 1
        if gap_start > 0 and y < height and y - gap_start <= max_gap:
            active_rows[gap_start:y] = [True] * (y - gap_start)

    ranges = []
    start = None
    for y, active in enumerate(active_rows + [False]):
        if active and start is None:
            start = y
        elif not active and start is not None:
            minimum_height = max(6, height // 100)
            if (
                y - start >= minimum_height
                and start > height * 0.03
                and y < height * 0.97
            ):
                ranges.append((start, y))
            start = None

    padding = max(4, height // 100)
    lines = []
    for top, bottom in ranges:
        crop = image.crop(
            (scan_left, max(0, top - padding), scan_right, min(height, bottom + padding))
        )
        crop_gray = ImageOps.autocontrast(crop.convert("L"))
        mask = crop_gray.point(lambda value: 255 if value < 140 else 0)
        bbox = mask.getbbox()
        if bbox:
            left, crop_top, right, crop_bottom = bbox
            crop = crop.crop(
                (
                    max(0, left - padding),
                    max(0, crop_top - padding),
                    min(crop.width, right + padding),
                    min(crop.height, crop_bottom + padding),
                )
            )
        lines.append(crop.convert("RGB"))

    return lines or [image.convert("RGB")]


def local_predict_text(image_path):
    image = Image.open(image_path).convert("RGB")
    predictions = []

    for line in split_text_lines(image):
        gray = ImageOps.autocontrast(line.convert("L"), cutoff=1)
        mask = gray.point(lambda value: 255 if value < 180 else 0)
        clean = Image.new("L", gray.size, 255)
        clean.paste(gray, mask=mask)

        border = max(12, clean.height // 3)
        canvas = Image.new(
            "RGB",
            (clean.width + border * 2, clean.height + border * 2),
            "white",
        )
        canvas.paste(clean.convert("RGB"), (border, border))

        pixel_values = processor(images=canvas, return_tensors="pt").pixel_values
        generated_ids = pretrained_model.generate(
            pixel_values,
            max_new_tokens=64,
            num_beams=5,
            early_stopping=True,
        )
        text = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
        )[0].strip()
        if text:
            predictions.append(text)

    return "\n".join(predictions) or "Kono text detect hoyni."


def api_predict_text(image_path):
    api_key = os.environ.get("OCR_SPACE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OCR_SPACE_API_KEY set kora nei.")

    with open(image_path, "rb") as image_file:
        response = requests.post(
            OCR_SPACE_URL,
            headers={"apikey": api_key},
            files={"file": (os.path.basename(image_path), image_file)},
            data={
                "language": "eng",
                "isOverlayRequired": "false",
                "OCREngine": "2",
                "scale": "true",
            },
            timeout=60,
        )

    response.raise_for_status()
    result = response.json()

    if result.get("IsErroredOnProcessing"):
        message = result.get("ErrorMessage") or "OCR.Space processing failed."
        if isinstance(message, list):
            message = " ".join(str(part) for part in message)
        raise RuntimeError(str(message))

    parsed_results = result.get("ParsedResults") or []
    text_parts = [
        item.get("ParsedText", "").strip()
        for item in parsed_results
        if item.get("ParsedText", "").strip()
    ]
    return "\n".join(text_parts) or "Kono text detect hoyni."


def predict_text(image_path):
    try:
        return api_predict_text(image_path)
    except (requests.RequestException, RuntimeError, ValueError) as error:
        app.logger.warning("OCR.Space failed; using pretrained model: %s", error)
        return local_predict_text(image_path)


@app.route("/", methods=["GET", "POST"])
def index():
    text = ""
    image_url = None

    if request.method == "POST":
        file = request.files.get("image")
        if not file or not file.filename:
            text = "Image select korun."
        else:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(path)
            image_url = url_for("static", filename=f"uploads/{filename}")

            try:
                text = predict_text(path)
            except (requests.RequestException, RuntimeError, ValueError) as error:
                text = f"OCR API error: {error}"

    return render_template("index.html", text=text, image=image_url)


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
