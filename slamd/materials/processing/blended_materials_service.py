from itertools import product

from slamd.common.error_handling import MaterialNotFoundException, ValueNotSupportedException, \
    SlamdRequestTooLargeException
from slamd.common.slamd_utils import not_numeric
from slamd.materials.processing.blending_configuration_parser import RatioParser
from slamd.materials.processing.forms.base_material_selection_form import BaseMaterialSelectionForm
from slamd.materials.processing.forms.blending_name_and_type_form import BlendingNameAndTypeForm
from slamd.materials.processing.forms.min_max_form import MinMaxForm
from slamd.materials.processing.forms.ratio_form import RatioForm
from slamd.materials.processing.material_type import MaterialType
from slamd.materials.processing.materials_persistence import MaterialsPersistence
from slamd.materials.processing.materials_service import MaterialsService, MaterialsResponse

RATIO_DELIMITER = '/'
MAX_NUMBER_OF_RATIOS = 100


class BlendedMaterialsService(MaterialsService):

    def create_materials_response(self, materials):
        return MaterialsResponse(materials, 'blended')

    def list_base_material_selection_by_type(self, material_type):
        if material_type not in MaterialType.get_all_types():
            raise MaterialNotFoundException('The requested type is not supported!')

        materials_by_type = MaterialsPersistence.query_by_type(material_type)
        base_materials = list(filter(lambda m: m.is_blended is False, materials_by_type))

        material_selection = []
        for material in base_materials:
            material_selection.append((material.uuid, material.name))

        form = BaseMaterialSelectionForm()
        form.base_material_selection.choices = material_selection
        return form

    def create_min_max_form(self, count):
        if not_numeric(count):
            raise ValueNotSupportedException('Cannot process selection!')

        count = int(count)

        if count < 2:
            raise ValueNotSupportedException('At least two items must be selected!')

        min_max_form = MinMaxForm()
        for i in range(count):
            min_max_form.all_min_max_entries.append_entry()
        return min_max_form

    def create_ratio_form(self, min_max_values_with_increments):
        if not self._ratio_input_is_valid(min_max_values_with_increments):
            raise ValueNotSupportedException('Configuration of ratios is not valid!')

        all_values = self._prepare_values_for_cartesian_product(min_max_values_with_increments)

        cartesian_product = product(*all_values)
        cartesian_product_list = list(cartesian_product)

        if len(cartesian_product_list) > MAX_NUMBER_OF_RATIOS:
            raise SlamdRequestTooLargeException(
                f'Too many blends were requested. At most {MAX_NUMBER_OF_RATIOS} ratios can be created!')

        ratio_form = RatioForm()
        for ratio_as_list in cartesian_product_list:
            all_ratios_for_entry = RatioParser.create_ratio_string(ratio_as_list)
            ratio_form_entry = ratio_form.all_ratio_entries.append_entry()
            ratio_form_entry.ratio.data = all_ratios_for_entry
        return ratio_form

    def save_blended_materials(self, submitted_blending_configuration):
        blending_name_any_type_form = BlendingNameAndTypeForm(submitted_blending_configuration)
        base_material_uuids = submitted_blending_configuration.getlist('base_material_selection')
        if not blending_name_any_type_form.validate():
            raise ValueNotSupportedException("The blending name is empty or already used!")

        all_ratios_as_string = [value for key, value in submitted_blending_configuration.items() if 'all_ratio_entries-' in key]

        if len(all_ratios_as_string) > MAX_NUMBER_OF_RATIOS:
            raise SlamdRequestTooLargeException(
                f'Too many ratios were passed! At most {MAX_NUMBER_OF_RATIOS} can be processed!')

        if not self._ratios_are_valid(all_ratios_as_string, len(base_material_uuids)):
            raise ValueNotSupportedException("There are invalid ratios. Make sure they satisfy the correct pattern!")

        ratios_as_list = RatioParser.create_ratio_list(all_ratios_as_string, RATIO_DELIMITER)

    def _prepare_values_for_cartesian_product(self, min_max_values_with_increments):
        all_values = []
        for i in range(len(min_max_values_with_increments) - 1):
            values_for_given_base_material = []
            current_value = min_max_values_with_increments[i]['min']
            max = min_max_values_with_increments[i]['max']
            increment = min_max_values_with_increments[i]['increment']
            while current_value <= max:
                values_for_given_base_material.append(current_value)
                current_value += increment
            all_values.append(values_for_given_base_material)
        return all_values

    def _validate_ranges(self, increment, max_value, min_value):
        return min_value < 0 or min_value > 100 or max_value > 100 or min_value > max_value \
               or max_value < 0 or increment <= 0 or not_numeric(max_value) \
               or not_numeric(min_value) or not_numeric(increment)

    def _ratio_input_is_valid(self, min_max_increments_values):
        for i in range(len(min_max_increments_values) - 1):
            min_value = min_max_increments_values[i]['min']
            max_value = min_max_increments_values[i]['max']
            increment = min_max_increments_values[i]['increment']
            if self._validate_ranges(increment, max_value, min_value):
                return False
        return True

    def _ratios_are_valid(self, all_ratios, number_of_base_materials):
        for ratio in all_ratios:
            pieces_of_a_ratio = ratio.split(RATIO_DELIMITER)
            if len(pieces_of_a_ratio) != number_of_base_materials:
                return False
            for pieces_of_a_ratio in pieces_of_a_ratio:
                if not_numeric(pieces_of_a_ratio):
                    return False
        return True
