from typing import Any, Dict, List
import pandas as pd


class ScheduleDataPlugin:
    """
    Reads and validates raw supply-chain item data.
    CSV version for now. Later we can replace this with SQL.
    """

    REQUIRED_COLUMNS: List[str] = [
        "item_id",
        "project_id",
        "project_name",
        "project_country",
        "project_city",
        "equipment_code",
        "equipment_name",
        "equipment_category",
        "supplier_name",
        "supplier_country",
        "origin_country",
        "origin_city",
        "origin_port",
        "destination_port",
        "transport_mode",
        "baseline_due_date",
        "latest_expected_delivery_date",
        "actual_delivery_date",
        "delivery_status",
        "current_milestone",
        "criticality_score",
        "item_value_usd",
    ]

    def load_csv(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path)

    def validate_and_prepare_data(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df.copy()

        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        df["baseline_due_date"] = pd.to_datetime(df["baseline_due_date"], errors="coerce")
        df["latest_expected_delivery_date"] = pd.to_datetime(
            df["latest_expected_delivery_date"],
            errors="coerce"
        )
        df["actual_delivery_date"] = pd.to_datetime(
            df["actual_delivery_date"],
            errors="coerce"
        )

        bad_date_rows = df[
            df["baseline_due_date"].isna()
            | df["latest_expected_delivery_date"].isna()
        ]

        if not bad_date_rows.empty:
            bad_ids = bad_date_rows["item_id"].astype(str).tolist()
            raise ValueError(f"Invalid baseline/latest delivery dates for item_id(s): {bad_ids}")

        return df

    def get_data_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {
            "total_items": int(len(df)),
            "projects": sorted(df["project_name"].dropna().unique().tolist()),
            "origin_countries": sorted(df["origin_country"].dropna().unique().tolist()),
            "project_countries": sorted(df["project_country"].dropna().unique().tolist()),
            "origin_ports": sorted(df["origin_port"].dropna().unique().tolist()),
            "destination_ports": sorted(df["destination_port"].dropna().unique().tolist()),
        }