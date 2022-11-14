const newOptionBase = (
    '<div class="vote-option remove-option-container">' +
        '<button type="button" class="icon remove-option"></button>' +
        '<input name="vote_option" type="text" maxlength="100" autocomplete="off">' +
    '</div>'
);
let currentType = 1;
let cachedVoteOptions = [];

jQuery.fn.any = function(filter) { 
    for (var i = 0 ; i < this.length ; i++) {
       if (filter.call(this[i])) return true;
    }
    return false;
};

function updateSubmitButtonState() {
    let voteOptionInputFields = $("input[name=vote_option]");
    let anyHasContent = $(voteOptionInputFields).any(function() {
        return $(this).val().trim() != "";
    });

    if (voteOptionInputFields.length > 0 && anyHasContent) {
        $(".send_button").prop("disabled", false);
    } else {
        $(".send_button").prop("disabled", true);
    }
}

function enhanceVoteOption(voteOption) {
    $(voteOption).children(".remove-option").each((_, removeOptionBtn) => {
        $(removeOptionBtn).click(() => {
            $(removeOptionBtn).parent().remove();
        });
    });

    $(voteOption).children("button").each((_, optionBtn) => {
        $(optionBtn).click(updateSubmitButtonState);
    });

    $(voteOption).children("input").each((_, input) => {
        $(input).on("input propertychange", updateSubmitButtonState);
    });
}

function addVoteOption(content = "") {
    let newOption = $.parseHTML(newOptionBase)[0];
    enhanceVoteOption(newOption);
    $(newOption).children("input").val(content);
    $(newOption).insertBefore($(".add-option-container"));
}

function addMultipleVoteOptions(options) {
    for (const option of options) {
        addVoteOption(option);
    }
}

function changeSurveyType(newType) {
    if (currentType == 1 || currentType == 2) {
        cachedVoteOptions = [];
        $(".vote-option.remove-option-container input").each((_, voteOption) => {
            cachedVoteOptions.push($(voteOption).val());
        });
    }

    $(".vote-option:not(.add-option-container)").each((_, voteOption) => {
        $(voteOption).remove();
    });

    switch(newType) {
        case 1:
            addMultipleVoteOptions(cachedVoteOptions);
            $(".field.vote-options").css("display", "block");
            $("#id_allow_multiple").prop("checked", false);
            break;
            
        case 2:
            addMultipleVoteOptions(cachedVoteOptions);
            $(".field.vote-options").css("display", "block");
            $("#id_allow_multiple").prop("checked", true);
            break;

        case 3:
            addMultipleVoteOptions(["Yes", "No"]);
            $(".field.vote-options").css("display", "none");
            $("#id_allow_multiple").prop("checked", false);
            break;
    }
    updateSubmitButtonState();
    currentType = newType
}

$(document).ready(() => {
    // Remove vote option functionality
    $(".vote-option").each((_, voteOption) => {
        enhanceVoteOption(voteOption);
    });

    // Add vote option functionality
    $(".add-option").each((_, addOptionBtn) => {
        $(addOptionBtn).click(() => {
            addVoteOption();
        });
    });

    // Behaviour for survey type selector
    $(".popup .type").each((_, typeButton) => {
        $(typeButton).click(() => {
            $(".type.target").removeClass("target");
            $(typeButton).addClass("target");

            if ($(typeButton).hasClass("type-1")) changeSurveyType(1);
            if ($(typeButton).hasClass("type-2")) changeSurveyType(2);
            if ($(typeButton).hasClass("type-3")) changeSurveyType(3);
        });
    });

    // Choose first type
    $(".popup .type").first().click();
});
