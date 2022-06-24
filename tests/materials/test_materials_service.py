import pytest
from werkzeug.exceptions import BadRequest

from slamd import create_app
from slamd.materials.forms.admixture_form import AdmixtureForm
from slamd.materials.forms.aggregates_form import AggregatesForm
from slamd.materials.forms.liquid_form import LiquidForm
from slamd.materials.forms.powder_form import PowderForm
from slamd.materials.forms.process_form import ProcessForm
from slamd.materials.materials_service import MaterialsService

app = create_app('testing', with_session=False)


def test_create_material_form_creates_powder():
    with app.test_request_context('/materials/powder'):
        file, form = MaterialsService().create_material_form('powder')
        assert file == 'powder_form.html'
        assert isinstance(form, PowderForm)


def test_create_material_form_creates_liquid():
    with app.test_request_context('/materials/liquid'):
        file, form = MaterialsService().create_material_form('liquid')
        assert file == 'liquid_form.html'
        assert isinstance(form, LiquidForm)


def test_create_material_form_creates_aggregates():
    with app.test_request_context('/materials/aggregates'):
        file, form = MaterialsService().create_material_form('aggregates')
        assert file == 'aggregates_form.html'
        assert isinstance(form, AggregatesForm)


def test_create_material_form_creates_process():
    with app.test_request_context('/materials/process'):
        file, form = MaterialsService().create_material_form('process')
        assert file == 'process_form.html'
        assert isinstance(form, ProcessForm)


def test_create_material_form_creates_admixture():
    with app.test_request_context('/materials/admixture'):
        file, form = MaterialsService().create_material_form('admixture')
        assert file == 'admixture_form.html'
        assert isinstance(form, AdmixtureForm)


def test_create_material_form_raises_bad_request_when_invalid_form_is_requested():
    with app.test_request_context('/materials/invalid'):
        with pytest.raises(BadRequest):
            MaterialsService().create_material_form('invalid')
