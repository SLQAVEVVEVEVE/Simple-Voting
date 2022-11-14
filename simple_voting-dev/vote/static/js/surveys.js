let lastPostId, csrfToken, url, userId;

jQuery.fn.any = function(filter) { 
    for (var i = 0 ; i < this.length ; i++) {
       if (filter.call(this[i])) return true;
    }
    return false;
};

jQuery.fn.outerHTML = function() {
    return jQuery('<div />').append(this.eq(0).clone()).html();
  };

jQuery.fn.serializeObject = function() {
    var data = {};
    var serialized = this.serializeArray();
    $.each(serialized, function() {
        if (data[this.name]) {
            if (!data[this.name].push) {
                data[this.name] = [data[this.name]];
            }
            data[this.name].push(this.value || '');
        } else {
            data[this.name] = this.value || '';
        }
    });
    return data;
};

function handleAjaxError(responce) {
    let alertTxt = "Something went wrong...\n\n";
    let detail = responce.responseJSON.detail;

    if (detail != undefined) {
        alertTxt += detail;
    } else {
        alertTxt += "Unknown error :O";
    }
    alert(alertTxt);
}

function enhanceSurvey(surveyBase) {
    // Proper behaviour for checkbox surveys
    $(surveyBase).find(".require-one-selected").each((_, container) => {
        let btn = $(container).parent().parent().find("button")[0];
        $(container).find(".b_checkbox").each((_, checkboxContainer) => {
            $(checkboxContainer).click((e) => {
                e.preventDefault();
                let checkbox = $(checkboxContainer).find("input[type=checkbox]")[0];
                checkbox.checked = !checkbox.checked;
                $(checkboxContainer).toggleClass("selected");

                let anyChecked = $(container).find("input[type=checkbox]").any(function() {
                    return this.checked;
                });
                btn.disabled = !anyChecked;
            });
        });
    });

    // AJAX for voting
    $(surveyBase).find("form").each((_, form) => {
        $(form).submit(function(e) {
            e.preventDefault();
            let formData = $(form).serializeObject();
            
            let submitter = e.originalEvent.submitter;
            if ($(submitter).attr('name') == 'choice_id') {
                formData['choice_id'] = $(submitter).attr('value');
            }
            
            $.ajax({
                data: formData,
                method: "POST",
                url: $(form).attr('action'),
                success: (responce) => {
                    // Get any vote option
                    let id;
                    if (typeof formData['choice_id'] == "string") {
                        id = formData['choice_id'];
                    } else {
                        id = formData['choice_id'][0];
                    }

                    // Replace content for all surveys on page with that vote option
                    // This works if there are multiple copies of the same survey on one page
                    let html = responce.data.new_html.trim();
                    $(`input[value=${id}], button[value=${id}]`).each((_, surveyVoteOption) => {
                        let newHtml = $.parseHTML(html)[0];
                        $(surveyVoteOption).closest('.survey-base').replaceWith(newHtml);
                    })
                },
                error: handleAjaxError
            });
        });
    });

    // Survey popup hander
    $(surveyBase).parent(".survey-card").each((_, surveyCard) => {
        $(surveyCard).children("a[href$=survey-popup]").each((_, openPopup) => {
            $(openPopup).click((e) => {
                let html = $(surveyCard).outerHTML();
                $("#survey-popup .survey-card").replaceWith(html);
                $("#survey-popup a[href$=survey-popup]").remove();

                let description = $(surveyBase).children(".hidden-description").text();
                $("#survey-popup .description").text(description);
                
                $("#survey-popup .survey-card .survey-base").each(function() {
                    enhanceSurvey(this);
                });
            });
        });
    });

    return surveyBase;
}

$(document).ready(() => {
    csrfToken = $("#load-more").find('input[name=csrfmiddlewaretoken]').val();
    url = $("#load-more").find("input[name=ajax-url").val();
    userId = $("#load-more").find("input[name=user_id").val();

    // If any are loaded without AJAX
    $(".survey-base").each(function() {
        enhanceSurvey(this);
    });

    // AJAX for loading more surveys
    $("#load-more").submit((e) => {
        $('.loading-icon').css("display", "unset");
        e.preventDefault();

        data =  {
            'csrfmiddlewaretoken': csrfToken,
            'amount': 8,
            'start_from': lastPostId,
        }
        if (userId != undefined) {
            data['user_id'] = userId;
        }

        $.ajax({
            data: data,
            method: 'POST',
            url: url,
            success: (responce) => {
                lastPostId = responce.data.last_post_id;
                $.each(responce.data.surveys, (_, html) => {
                    let survey = $.parseHTML(html.trim())[0];
                    enhanceSurvey($(survey).children(".survey-base"));
                    $("#survey-container").append(survey);
                })

                if (!responce.data.any_left) {
                    $("#load-more").remove();
                }
            },
            error: handleAjaxError
        });
    });
    $("#load-more").submit();
});
