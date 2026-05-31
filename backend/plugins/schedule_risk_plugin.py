from datetime import date
from typing import Dict
import pandas as pd


class ScheduleRiskPlugin:
    """
    Deterministic schedule-risk calculation plugin.
    LLM should not calculate these numbers.
    """

    def calculate_delay_days(self, latest_expected_date, baseline_due_date) -> int:
        return int((latest_expected_date - baseline_due_date).days)

    def calculate_days_until_due(self, baseline_due_date) -> int:
        today = pd.Timestamp(date.today())
        return int((baseline_due_date - today).days)

    def calculate_schedule_risk_percentage(self, delay_days: int, days_until_due: int) -> float:
        if delay_days <= 0:
            return 0.0

        if days_until_due <= 0:
            return 100.0

        return round((delay_days / days_until_due) * 100, 2)

    def assign_schedule_risk_level(self, delay_days: int, risk_percentage: float) -> str:
        if delay_days <= 0:
            return "On Track"

        if risk_percentage < 5:
            return "Low"

        if risk_percentage < 15:
            return "Medium"

        return "High"

    def build_risk_reason(
        self,
        delay_days: int,
        days_until_due: int,
        risk_percentage: float,
        risk_level: str,
    ) -> str:
        if risk_level == "On Track":
            return "The item is not delayed against the baseline due date."

        if days_until_due <= 0:
            return (
                f"The item is {delay_days} days delayed and the baseline due date has already passed. "
                "This creates immediate schedule exposure."
            )

        return (
            f"The item is {delay_days} days delayed with {days_until_due} days remaining until the baseline due date. "
            f"The schedule risk is {risk_percentage}%, so it is categorized as {risk_level} risk."
        )

    def build_recommendation(self, risk_level: str) -> str:
        if risk_level == "High":
            return (
                "Escalate with supplier immediately, request a recovery plan, check alternate routing, "
                "and review project buffer."
            )

        if risk_level == "Medium":
            return "Monitor weekly, request supplier update, and prepare contingency options if the delay increases."

        if risk_level == "Low":
            return "Track in normal review cycle and confirm the next milestone date."

        return "No immediate action required; continue normal milestone tracking."

    def calculate_risks(self, df: pd.DataFrame) -> pd.DataFrame:
        result_df = df.copy()

        result_df["delay_days"] = result_df.apply(
            lambda row: self.calculate_delay_days(
                row["latest_expected_delivery_date"],
                row["baseline_due_date"],
            ),
            axis=1,
        )

        result_df["days_until_due"] = result_df.apply(
            lambda row: self.calculate_days_until_due(row["baseline_due_date"]),
            axis=1,
        )

        result_df["schedule_risk_percentage"] = result_df.apply(
            lambda row: self.calculate_schedule_risk_percentage(
                int(row["delay_days"]),
                int(row["days_until_due"]),
            ),
            axis=1,
        )

        result_df["schedule_risk_level"] = result_df.apply(
            lambda row: self.assign_schedule_risk_level(
                int(row["delay_days"]),
                float(row["schedule_risk_percentage"]),
            ),
            axis=1,
        )

        result_df["schedule_risk_reason"] = result_df.apply(
            lambda row: self.build_risk_reason(
                int(row["delay_days"]),
                int(row["days_until_due"]),
                float(row["schedule_risk_percentage"]),
                row["schedule_risk_level"],
            ),
            axis=1,
        )

        result_df["schedule_recommendation"] = result_df["schedule_risk_level"].apply(
            self.build_recommendation
        )

        return result_df

    def get_risk_breakdown(self, df: pd.DataFrame) -> Dict[str, int]:
        return {
            "totalItems": int(len(df)),
            "highRiskItems": int((df["schedule_risk_level"] == "High").sum()),
            "mediumRiskItems": int((df["schedule_risk_level"] == "Medium").sum()),
            "lowRiskItems": int((df["schedule_risk_level"] == "Low").sum()),
            "onTrackItems": int((df["schedule_risk_level"] == "On Track").sum()),
        }