import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def resolve_google_application_credentials() -> str:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        return credentials_path

    credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not credentials_json:
        return "./service-account.json"

    credentials = json.loads(credentials_json)
    temp_credentials_path = Path(tempfile.gettempdir()) / "google-service-account.json"
    temp_credentials_path.write_text(json.dumps(credentials), encoding="utf-8")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(temp_credentials_path)
    return str(temp_credentials_path)


@dataclass(frozen=True)
class Settings:
    # Google / Gemini settings
    google_cloud_project: str = os.getenv(
        "GOOGLE_CLOUD_PROJECT",
        "clear-style-493512-n0",
    )

    google_cloud_location: str = os.getenv(
        "GOOGLE_CLOUD_LOCATION",
        "us-central1",
    )

    gemini_model: str = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )

    google_application_credentials: str = resolve_google_application_credentials()

    # Raw SupplyPulse dataset
    raw_data_path: str = os.getenv(
        "RAW_DATA_PATH",
        "./data/supplypulse_raw_supply_chain_items.csv",
    )

    # Bright Data SERP settings
    brightdata_api_key: str = os.getenv(
        "BRIGHTDATA_API_KEY",
        "",
    )

    brightdata_serp_zone: str = os.getenv(
        "BRIGHTDATA_SERP_ZONE",
        "serp",
    )

    brightdata_serp_endpoint: str = os.getenv(
        "BRIGHTDATA_SERP_ENDPOINT",
        "https://api.brightdata.com/request",
    )

    brightdata_default_search_engine: str = os.getenv(
        "BRIGHTDATA_DEFAULT_SEARCH_ENGINE",
        "google",
    )

    # Bright Data / Google SERP localization
    # gl = country localization, example: us, sg, in
    brightdata_default_country: str = os.getenv(
        "BRIGHTDATA_DEFAULT_COUNTRY",
        "us",
    )

    # hl = language localization, example: en, de, fr
    brightdata_default_language: str = os.getenv(
        "BRIGHTDATA_DEFAULT_LANGUAGE",
        "en",
    )

    # Optional Bright Data / SERP location field.
    # Keep empty unless we intentionally want a city/country location.
    brightdata_default_location: str = os.getenv(
        "BRIGHTDATA_DEFAULT_LOCATION",
        "",
    )

    # Optional Google encoded location parameter.
    # Keep empty unless we generate/provide uule later.
    brightdata_default_uule: str = os.getenv(
        "BRIGHTDATA_DEFAULT_UULE",
        "",
    )


settings = Settings()
