# Lab3
"""Print the configuration resolved for the current APP_ENV (used by the Lab 3 demo)."""

from app.core.config import get_settings


def main() -> None:
    s = get_settings()
    db = s.database_url.rsplit("/", 1)[-1]
    print(f"  app_env={s.app_env}  debug={s.debug}  db={db}")


if __name__ == "__main__":
    main()
