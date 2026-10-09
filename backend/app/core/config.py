"""
Central application configuration, loaded from environment variables.
Nothing else in the app should read os.environ directly - everything
goes through this Settings object so config is testable and auditable.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    ENVIRONMENT: str = "development"
    APP_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://mingly:mingly_dev_password@localhost:5432/mingly"

    # Sessions
    SESSION_SECRET: str = "change-me-in-env"
    SESSION_COOKIE_NAME: str = "mingly_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 30  # 30 days

    # LinkedIn OAuth (OpenID Connect - "Sign In with LinkedIn using OpenID Connect")
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/auth/linkedin/callback"

    # Email (plain SMTP, so any provider works - Resend, Postmark, Amazon SES,
    # etc.). Leave SMTP_HOST empty and emails are skipped and logged instead
    # of sent, so the app runs fine before an email account exists.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587  # 587 = STARTTLS, 465 = TLS from the start
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "Mingly <hello@mingly.ai>"


settings = Settings()
