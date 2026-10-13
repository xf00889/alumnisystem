"""Validation for private direct and group message attachments.

Defense in depth: byte limits, extension allowlist, file signatures, image
verification and bounded OOXML inspection. Malware scanning is a separate
production requirement; no parser alone guarantees a file is harmless.
"""
import io
import os
import re
import zipfile

from django.core.exceptions import ValidationError

MAX_MESSAGE_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_MESSAGE_EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf',
    '.docx', '.xlsx', '.pptx', '.txt', '.csv',
})


def sanitize_filename(filename):
    filename = str(filename or 'attachment').replace('\\', '/').split('/')[-1]
    filename = re.sub(r'[\x00-\x1f\x7f]+', '', filename)
    filename = re.sub(r'[^\w .-]+', '_', filename, flags=re.UNICODE).strip(' .')
    basename, extension = os.path.splitext(filename)
    basename = basename[:100].strip(' .') or 'attachment'
    return basename + extension[:12].lower()


def get_file_extension(filename):
    return os.path.splitext(str(filename))[-1].lower()


def is_image_file(filename):
    return get_file_extension(filename) in {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def validate_message_attachment(file):
    if not file:
        return None
    filename = sanitize_filename(file.name)
    ext = get_file_extension(filename)
    if ext not in ALLOWED_MESSAGE_EXTENSIONS:
        raise ValidationError('Unsupported attachment format. Choose an image, PDF, DOCX, XLSX, PPTX, TXT or CSV file.')
    if not file.size or file.size > MAX_MESSAGE_FILE_SIZE:
        raise ValidationError('Attachments must be between 1 byte and 5 MB.')
    try:
        file.seek(0)
        data = file.read(MAX_MESSAGE_FILE_SIZE + 1)
        if len(data) != file.size or len(data) > MAX_MESSAGE_FILE_SIZE:
            raise ValidationError('Invalid attachment size.')
        if is_image_file(filename):
            _check_image(data, ext)
        elif ext == '.pdf':
            if not data.startswith(b'%PDF-'):
                raise ValidationError('The PDF file content does not match its extension.')
        elif ext in {'.docx', '.xlsx', '.pptx'}:
            _check_office_document(data, ext)
        elif ext in {'.txt', '.csv'}:
            if b'\x00' in data:
                raise ValidationError('Text attachments must not contain binary data.')
            try:
                data.decode('utf-8-sig')
            except UnicodeDecodeError as exc:
                raise ValidationError('Text attachments must be UTF-8 encoded.') from exc
    finally:
        file.seek(0)
    file.name = filename
    return file


def _check_image(data, ext):
    signatures = {
        '.jpg': data.startswith(b'\xff\xd8\xff'),
        '.jpeg': data.startswith(b'\xff\xd8\xff'),
        '.png': data.startswith(b'\x89PNG\r\n\x1a\n'),
        '.gif': data[:6] in {b'GIF87a', b'GIF89a'},
        '.webp': data[:4] == b'RIFF' and data[8:12] == b'WEBP',
    }
    if not signatures[ext]:
        raise ValidationError('Image content does not match the selected format.')
    try:
        from PIL import Image, UnidentifiedImageError
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > 25_000_000:
                raise ValidationError('Image dimensions exceed the safe limit.')
            image.verify()
    except (ValueError, OSError, SyntaxError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValidationError('The uploaded image could not be verified.') from exc


def _check_office_document(data, ext):
    mandatory = {
        '.docx': 'word/document.xml',
        '.xlsx': 'xl/workbook.xml',
        '.pptx': 'ppt/presentation.xml',
    }
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > 2000 or sum(item.file_size for item in infos) > 30 * 1024 * 1024:
                raise ValidationError('Office document exceeds safe unpacked size.')
            names = {i.filename for i in infos}
            if '[Content_Types].xml' not in names or mandatory[ext] not in names:
                raise ValidationError('The Office document structure is invalid.')
            if any('vbaproject.bin' in name.lower() for name in names):
                raise ValidationError('Macro-enabled Office documents are not allowed.')
            for info in infos:
                if info.flag_bits & 0x1:
                    raise ValidationError('Encrypted Office documents cannot be inspected.')
            # Check archive structure / CRC; total unpacked bytes bounded above.
            bad = archive.testzip()
            if bad:
                raise ValidationError('The Office document archive is damaged.')
    except (OSError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        raise ValidationError('The Office document could not be inspected.') from exc
