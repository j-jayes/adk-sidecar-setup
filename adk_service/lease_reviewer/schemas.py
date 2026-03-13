"""
Pydantic schemas for structured lease document extraction.

The checklist agent uses `LeaseInformation` as its output schema,
ensuring the LLM returns a well-structured JSON object that we can
validate and display to the user.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LeaseInformation(BaseModel):
    """Structured information extracted from a residential lease agreement."""

    # --- Parties ---
    tenant_names: list[str] = Field(
        default_factory=list,
        description="Full names of all tenants listed in the lease.",
    )
    landlord_name: Optional[str] = Field(
        default=None,
        description="Full name or company name of the landlord / letting agent.",
    )

    # --- Property ---
    property_address: Optional[str] = Field(
        default=None,
        description="Full address of the leased property.",
    )

    # --- Term ---
    lease_start_date: Optional[str] = Field(
        default=None,
        description="Lease commencement date (ISO-8601 preferred).",
    )
    lease_end_date: Optional[str] = Field(
        default=None,
        description="Lease expiry date, or 'rolling' / 'periodic' if applicable.",
    )
    lease_type: Optional[str] = Field(
        default=None,
        description="Type of tenancy, e.g. 'Assured Shorthold Tenancy', 'Month-to-Month'.",
    )

    # --- Financial ---
    monthly_rent: Optional[float] = Field(
        default=None,
        description="Monthly rent amount in the document's currency.",
    )
    rent_currency: Optional[str] = Field(
        default=None,
        description="Currency code, e.g. 'GBP', 'USD', 'EUR'.",
    )
    rent_due_day: Optional[int] = Field(
        default=None,
        description="Day of the month on which rent is due (1-31).",
    )
    security_deposit: Optional[float] = Field(
        default=None,
        description="Security deposit amount.",
    )
    deposit_scheme: Optional[str] = Field(
        default=None,
        description="Deposit protection scheme name, if mentioned.",
    )

    # --- Key clauses ---
    notice_period_days: Optional[int] = Field(
        default=None,
        description="Notice period required to terminate the tenancy (days).",
    )
    pets_allowed: Optional[bool] = Field(
        default=None,
        description="Whether pets are explicitly allowed.",
    )
    subletting_allowed: Optional[bool] = Field(
        default=None,
        description="Whether subletting is explicitly permitted.",
    )
    utilities_included: list[str] = Field(
        default_factory=list,
        description="List of utilities included in the rent, e.g. ['water', 'gas'].",
    )

    # --- Checklist result ---
    missing_items: list[str] = Field(
        default_factory=list,
        description=(
            "List of important items that appear to be absent from the lease, "
            "e.g. ['deposit protection scheme', 'break clause', 'inventory reference']."
        ),
    )
    summary: str = Field(
        default="",
        description="Short plain-English summary of findings (2-4 sentences).",
    )
