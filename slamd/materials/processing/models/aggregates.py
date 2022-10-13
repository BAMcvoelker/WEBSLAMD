from dataclasses import dataclass
from slamd.materials.processing.models.material import Material


@dataclass
class Composition:
    fine_aggregates: float = None
    coarse_aggregates: float = None
    gravity: float = None
    bulk_density: float = None
    fineness_modulus: float = None
    water_absorption: float = None

@dataclass
class Aggregates(Material):
    composition: Composition = None

    def to_dict(self):
        out = super().to_dict()
        out['composition'] = self.composition.__dict__.copy()

        return out
