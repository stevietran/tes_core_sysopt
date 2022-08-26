from pydantic import BaseModel
from typing import Sequence, Optional

class LoadSplitProfileBase(BaseModel):
    time: float
    value: list

class LoadSplitProfileUpdate(LoadSplitProfileBase):
    ...

class ElectricSplitProfileBase(BaseModel):
    time: float
    value: list

class ElectricSplitProfileUpdate(ElectricSplitProfileBase):
    ...

class CostSplitProfileBase(BaseModel):
    time: float
    value: list

class CostSplitProfileUpdate(CostSplitProfileBase):
    ...

class ResultBase(BaseModel):
    tes_type: str
    tes_attr: dict
    tes_op_attr: dict
    chiller: str
    chiller_no_tes: str
    capex: float
    capex_no_tes: float
    lcos: float
    lcos_no_tes: float
    htf: str
    htf_attr: dict
    material: str
    material_attr: dict
    tes_capex: float
    tes_lcos: float
    runtime: float

class ResultReturn(BaseModel):
    result_data: ResultBase
    load_split_profile_no_tes: Optional[Sequence[LoadSplitProfileBase]]
    load_split_profile: Optional[Sequence[LoadSplitProfileBase]]
    electric_split_profile_no_tes: Optional[Sequence[ElectricSplitProfileBase]]
    electric_split_profile: Optional[Sequence[ElectricSplitProfileBase]]
    cost_split_profile_no_tes: Optional[Sequence[CostSplitProfileBase]]
    cost_split_profile: Optional[Sequence[CostSplitProfileBase]]