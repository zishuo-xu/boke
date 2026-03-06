def is_admin_user(user, admin_usernames) -> bool:
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and user.username in admin_usernames
    )

