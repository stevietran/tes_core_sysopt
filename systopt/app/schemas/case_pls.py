from pydantic import BaseModel

from typing import Sequence, Optional

class FlowProfile(BaseModel):
    parent_id: Optional[int]
    time: float
    value: float

class CaseParams(BaseModel):
    app: str
    accuracy_level: str
    country_selection: str
    safety_factor: float

class LoadData(BaseModel):
    load_type: str
    load_selection: Optional[str]
    load_value: Optional[float]
    load_profiles: Optional[Sequence[FlowProfile]]

class CaseData(BaseModel):
    params: CaseParams
    load_data: LoadData
