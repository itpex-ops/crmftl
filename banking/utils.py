from django.utils import timezone


def _generate_number(prefix, model, field_name):
    """
    Generate sequential numbers like:
    PAY-20260722-0001
    """

    today = timezone.now().strftime("%Y%m%d")
    prefix_text = f"{prefix}-{today}"

    last_record = (
        model.objects.filter(**{f"{field_name}__startswith": prefix_text})
        .order_by(f"-{field_name}")
        .first()
    )

    if last_record:
        last_number = getattr(last_record, field_name)
        sequence = int(last_number.split("-")[-1]) + 1
    else:
        sequence = 1

    return f"{prefix_text}-{sequence:04d}"