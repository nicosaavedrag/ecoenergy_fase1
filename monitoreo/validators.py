import os
from PIL import Image
from django.core.exceptions import ValidationError


def validate_image_file(file_obj):
    """
    Validador estricto para archivos de imagen:
    1. Extensión permitida: .jpg, .jpeg, .png, .webp.
    2. Tamaño máximo: 2 MB.
    3. Contenido real de imagen verificado mediante Pillow (Image.verify()).
    """
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(
            f"Extensión '{ext}' no permitida. Formatos soportados: {', '.join(valid_extensions)}."
        )

    # Tamaño máximo de 2 MB
    max_size_bytes = 2 * 1024 * 1024
    if file_obj.size > max_size_bytes:
        raise ValidationError("El archivo supera el tamaño máximo permitido de 2 MB.")

    # Validación de contenido real con Pillow
    try:
        # Si es un InMemoryUploadedFile o TemporaryUploadedFile
        file_obj.seek(0)
        img = Image.open(file_obj)
        img.verify()
        file_obj.seek(0)
    except Exception as exc:
        raise ValidationError("El archivo no es una imagen válida o se encuentra corrupto.") from exc
