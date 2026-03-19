from app.dashboard.queries.common import get_user_profile


def get_profile_header_data(client, user_id: str) -> dict:
    return {
        "user_profile": get_user_profile(client, user_id),
    }
