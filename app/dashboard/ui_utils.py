def format_currency(value: float) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


def format_delta(value: float) -> str:
    prefix = "+" if value > 0 else ""
    return f"{prefix}{format_currency(value)}"


def get_display_name(auth_user: dict, user_profile: dict | None) -> str:
    for candidate in [
        (user_profile or {}).get("display_name"),
        (user_profile or {}).get("full_name"),
        auth_user.get("email"),
    ]:
        text = str(candidate or "").strip()
        if text:
            return text
    return "usuario"
