"""
mnemo/capture/ocr.py
Owner: Vinayak

Native Windows OCR via pywinrt. No external Tesseract dependency.
Falls back gracefully if Windows version is too old.
"""

import asyncio
import logging
import platform

log = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    log.info("OCR Backend: WinRT (Windows Native)")
else:
    log.info("OCR Backend: Tesseract (Fallback)")


async def _run_ocr(image_bytes: bytes) -> str:
    """Async WinRT OCR pipeline."""
    import winrt.windows.graphics.imaging as imaging
    import winrt.windows.media.ocr as winrt_ocr
    import winrt.windows.storage.streams as streams

    # 1. Write bytes into a Windows InMemoryRandomAccessStream
    stream = streams.InMemoryRandomAccessStream()
    writer = streams.DataWriter(stream.get_output_stream_at(0))
    writer.write_bytes(image_bytes)
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)

    # 2. Decode the stream into a SoftwareBitmap
    decoder = await imaging.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    # 3. Convert to BGRA8 format if needed (OCR engine requirement)
    if bitmap.bitmap_pixel_format != imaging.BitmapPixelFormat.BGRA8:
        bitmap = imaging.SoftwareBitmap.convert(
            bitmap, imaging.BitmapPixelFormat.BGRA8
        )

    # 4. Create OCR engine and recognise
    engine = winrt_ocr.OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        # No language pack — try English explicitly
        try:
            import winrt.windows.globalization as globalization
            language = globalization.Language("en-US")
            engine = winrt_ocr.OcrEngine.try_create_from_language(language)
        except Exception:
            pass
            
    if engine is None:
        log.warning("WinRT OCR engine unavailable — no language pack found")
        return ""

    result = await engine.recognize_async(bitmap)
    return result.text.strip()


def extract_text(image_bytes: bytes) -> str:
    """
    Run Windows OCR on the given image bytes.
    Returns extracted text, or empty string on failure.
    """
    if not IS_WINDOWS:
        return _fallback_ocr(image_bytes)
        
    try:
        return asyncio.run(_run_ocr(image_bytes))
    except Exception as e:
        log.warning("WinRT OCR failed: %s — trying fallback", e)
        return _fallback_ocr(image_bytes)


def _fallback_ocr(image_bytes: bytes) -> str:
    """For Linux/Mac or if WinRT fails."""
    try:
        import io

        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img).strip()
    except Exception:
        return ""
