from dataclasses import dataclass
from slamd.materials.processing.models.material import Material


@dataclass
class Composition:
    fe3_o2: float = None
    si_o2: float = None
    al2_o3: float = None
    ca_o: float = None
    mg_o: float = None
    na2_o: float = None
    k2_o: float = None
    s_o3: float = None
    ti_o2: float = None
    p2_o5: float = None
    sr_o: float = None
    mn2_o3: float = None


@dataclass
class Structure:
    fine: str = None
    gravity: str = None


@dataclass
class Powder(Material):
    composition: Composition = None
    structure: Structure = None
