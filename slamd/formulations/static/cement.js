const CEMENT_FORMULATIONS_MATERIALS_URL = `${window.location.protocol}//${window.location.host}/materials/formulations/cement`;
let cementWeightConstraint = "";

/**
 * Despite the fact that some functions in cement.js and concrete.js look rather similar, we choose not to
 * extract too many common methods as the internal logic for the two cases might diverge. In order not to create
 * too much coupling between usecase which are different we explicitly prefer duplicating some parts of the code here.
 */
function toggleBasedOnSelectionAndConstraints() {
    const powderPlaceholder = document.getElementById("powder_selection");
    const liquidPlaceholder = document.getElementById("liquid_selection");

    const powderSelected = atLeastOneItemIsSelected(powderPlaceholder);
    const liquidSelected = atLeastOneItemIsSelected(liquidPlaceholder);

    const validSelectionConfiguration = powderSelected && liquidSelected;
    const validConstraintConfiguration = cementWeightConstraint !== undefined && cementWeightConstraint !== "" &&
        cementWeightConstraint > 0;

    const changeSelectionButton = document.getElementById("change_materials_and_processes_selection_button");
    changeSelectionButton.disabled = !(validSelectionConfiguration && validConstraintConfiguration);
}

function toggleSelectionConfirmationButtonAfterConstraintChange() {
    cementWeightConstraint = document.getElementById("weight_constraint").value;
    toggleBasedOnSelectionAndConstraints();
}

async function confirmSelection() {
    removeInnerHtmlFromPlaceholder("formulations_min_max_placeholder");
    removeInnerHtmlFromPlaceholder("formulations_weights_placeholder");
    document.getElementById("submit").disabled = true;
    cementWeightConstraint = document.getElementById("weight_constraint").value;

    const selectedMaterials = collectBuildingMaterialFormulationSelection();
    const url = `${CEMENT_FORMULATIONS_MATERIALS_URL}/add_min_max_entries`;

    insertSpinnerInPlaceholder("formulations_min_max_placeholder");
    await postDataAndEmbedTemplateInPlaceholder(url, "formulations_min_max_placeholder", selectedMaterials);
    removeSpinnerInPlaceholder("formulations_min_max_placeholder");

    addListenersToIndependentFields("CEMENT");
    // assignConfirmFormulationsConfigurationEvent();
}

window.addEventListener("load", function () {
    document.getElementById("confirm_materials_and_processes_selection_button").addEventListener("click", confirmSelection);

    document.getElementById("confirm_materials_and_processes_selection_button").addEventListener("click", confirmSelection);
    document.getElementById("weight_constraint").addEventListener("keyup", toggleSelectionConfirmationButtonAfterConstraintChange);
    document.getElementById("powder_selection").addEventListener("change", toggleBasedOnSelectionAndConstraints);
    document.getElementById("liquid_selection").addEventListener("change", toggleBasedOnSelectionAndConstraints);
    document.getElementById("delete_formulations_batches_button").addEventListener("click", deleteFormulations);

    // document.getElementById("change_materials_and_processes_selection_button").disabled = false;
    // document.getElementById("submit").disabled = false;
    // document.getElementById("delete_formulations_batches_button").disabled = false;

    const formulations = document.getElementById("formulations_dataframe");
    if (formulations) {
        document.getElementById("submit").disabled = false;
        document.getElementById("delete_formulations_batches_button").disabled = false;
    }
});
