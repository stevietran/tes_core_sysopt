from pydantic import BaseModel
    
class TesOutput(BaseModel):
    tes_type: str
    tes_attr: dict
    tes_op_attr: dict
    htf: str
    htf_attr: dict
    material: str
    material_attr: dict
    runtime: float
    lcos: float
    capex: float