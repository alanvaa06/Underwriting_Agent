"""Pydantic v2 request/response/event schemas. Wire format for the SSE API."""

from typing import Any, Literal

from pydantic import BaseModel, Field, SecretStr


class CreditHistory(BaseModel):
    bankruptcies: int = Field(ge=0)
    foreclosures: int = Field(ge=0)
    late_payments_12mo: int = Field(ge=0)
    late_payments_24mo: int = Field(ge=0)
    oldest_tradeline_years: float = Field(ge=0)
    collections: list[str] = Field(default_factory=list)
    inquiries_6mo: int = Field(default=0, ge=0)
    total_tradelines: int = Field(default=0, ge=0)
    credit_notes: str = ""


class Employment(BaseModel):
    employer: str
    position: str
    years: float = Field(ge=0)
    monthly_income: float = Field(gt=0)
    type: Literal["W2", "1099", "self_employed"] = "W2"
    employment_gap: str = "None"
    gap_explanation: str = "N/A"


class Debts(BaseModel):
    car_loan: float = Field(default=0, ge=0)
    student_loan: float = Field(default=0, ge=0)
    credit_cards: float = Field(default=0, ge=0)
    other: float = Field(default=0, ge=0)

    @property
    def total_monthly(self) -> float:
        return self.car_loan + self.student_loan + self.credit_cards + self.other


class Assets(BaseModel):
    checking: float = Field(default=0, ge=0)
    savings: float = Field(default=0, ge=0)
    investments: float = Field(default=0, ge=0)
    retirement: float = Field(default=0, ge=0)


class PropertyInfo(BaseModel):
    purchase_price: float = Field(gt=0)
    property_type: Literal["single_family", "condo", "townhouse", "multi_family"] = "single_family"
    occupancy: Literal["primary", "secondary", "investment"] = "primary"
    appraised_value: float | None = None


class LoanRequest(BaseModel):
    loan_amount: float = Field(gt=0)
    down_payment: float = Field(ge=0)
    term_years: int = Field(default=30, ge=1, le=40)


class ApplicantIn(BaseModel):
    name: str
    ssn: str | None = None
    credit_score: int = Field(ge=300, le=850)
    credit_history: CreditHistory
    employment: Employment
    debts: Debts
    assets: Assets
    property_info: PropertyInfo
    loan: LoanRequest


class RunRequest(BaseModel):
    applicant: ApplicantIn
    api_key: SecretStr
    model: Literal["gpt-4o"] = "gpt-4o"


EventType = Literal[
    "agent_start",
    "agent_thinking",
    "agent_complete",
    "graph_transition",
    "decision",
    "error",
    "ping",
    "done",
]


class AgentEvent(BaseModel):
    type: EventType
    payload: dict[str, Any]
    ts: float
