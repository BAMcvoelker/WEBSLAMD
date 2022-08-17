from slamd.materials.processing.materials_facade import MaterialsFacade
import pandas as pd


class FormulationsConverter:

    @classmethod
    def formulation_to_df(cls, materials, processes, weight_product, targets):
        full_dict, names = MaterialsFacade.materials_formulation_as_dict(materials, processes)
        all_targets = targets.split(';')
        for target in all_targets:
            full_dict[target] = ''

        all_rows = []
        for weights in weight_product:
            weight_dict = {}
            for i, weight in enumerate(weights):
                weight_dict[f'{names[i]} (kg)'] = weight
            all_rows.append({**weight_dict, **full_dict})
        dataframe = pd.DataFrame(all_rows)
        return dataframe