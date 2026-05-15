"""
mnemo/capture/ocr.py
Owner: Vinayak

Native Windows OCR via pywinrt. No external Tesseract dependency.
Falls back gracefully if Windows version is too old.
"""

import logging

log = logging.getLogger(__name__)


def extract_text(image_bytes: bytes) -> str:
    """
    Run Windows OCR on the given image bytes.
    Returns extracted text, or empty string on failure.
    """
    # TODO(week 2):
    # import winrt.windows.media.ocr as ocr
    # import winrt.windows.graphics.imaging as imaging
    # async pipeline:
    #   1. Wrap image_bytes in InMemoryRandomAccessStream
    #   2. BitmapDecoder.create_async(stream)
    #   3. softwareBitmap = await decoder.get_software_bitmap_async()
    #   4. engine = OcrEngine.try_create_from_user_profile_languages()
    #   5. result = await engine.recognize_async(softwareBitmap)
    #   6. return result.text
    raise NotImplementedError("Vinayak — week 2 deliverable")
