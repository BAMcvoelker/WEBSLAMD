import {assignClickEventToSubmitButton} from "./utils.js";
import {assignClickEventToTaskForm} from "./task.js"
import {assignClickEventToMaterialTypeField} from "./material_type.js";
import {
    assignClickEventToDesignTargetForm,
    handleAddingDesignTargets,
    handleDesignTargetsSubmission
} from "./target.js";
import {assignClickEventToPowdersForm, handlePowdersSubmission} from "./powder.js";
import {assignClickEventToLiquidForm, handleAddingLiquid, handleLiquidSubmission} from "./liquid.js";
import {assignClickEventToOtherForm, handleAddingOther, handleOtherSubmission} from "./other.js";
import {assignInputEventToCommentForm, handleCommentSubmission} from "./comment.js";
import {
    handleDeleteDesignAssistantSession,
    handleUploadDesignAssistantSession,
    passClickToDAFileInput
} from "./design_assistant_session.js"


window.addEventListener("load", function () {
    document.getElementById("nav-bar-design-assistant").setAttribute("class", "nav-link active");
    document.getElementById("da-button-upload").addEventListener("change", handleUploadDesignAssistantSession)
    document.getElementById("upload_session_button").addEventListener("click", passClickToDAFileInput)
    assignClickEventToSubmitButton("delete_session_button", handleDeleteDesignAssistantSession);
    assignClickEventToTaskForm();
    assignClickEventToMaterialTypeField();
    assignClickEventToSubmitButton("design_targets_submit_button", handleDesignTargetsSubmission);
    assignClickEventToSubmitButton("powders_submit_button", handlePowdersSubmission);
    assignClickEventToDesignTargetForm();
    assignClickEventToPowdersForm();
    assignClickEventToSubmitButton("additional_design_targets_button", handleAddingDesignTargets);
    assignClickEventToSubmitButton("submit_liquid_button", handleLiquidSubmission);
    assignClickEventToSubmitButton("additional_liquid_button", handleAddingLiquid);
    assignClickEventToLiquidForm();
    assignClickEventToSubmitButton("submit_other_button", handleOtherSubmission);
    assignClickEventToSubmitButton("additional_other_button", handleAddingOther);
    assignClickEventToOtherForm();
    assignClickEventToSubmitButton("submit_comment_button", handleCommentSubmission);
    assignInputEventToCommentForm()
});