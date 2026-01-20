def remove_non_printable_characters(value: str):
    if value and not value.isprintable():
        return ''.join(ch for ch in value if ch.isprintable())
    return value
