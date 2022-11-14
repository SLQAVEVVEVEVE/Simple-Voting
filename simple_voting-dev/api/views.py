from functools import wraps
from django.forms import ValidationError
from django.shortcuts import redirect
from django.http.response import JsonResponse
from django.template.loader import render_to_string

from .responses import APIResponseTemplate, GenericAPIResponses

from vote.models import Survey, User, VoteOption, Vote
from vote.forms import SurveyCreateForm, SurveyVoteForm
from vote.views import get_base_context, authentication_required


def limit_avaliable_method(handler):
    @wraps(handler)
    def wrapper(request, context, *args, **kwargs):
        return_value = handler(request, context=context)
        if return_value:
            return return_value
        else:
            return GenericAPIResponses.METHOD_NOT_ALLOWED
    return wrapper


def render_slice_to_responce(request, context, surveys, start_id, amount):
        last_not_voted, any_left, last_id = Survey.get_survey_slice(
            surveys, start_id, amount
        )

        rendered_surveys = []
        for survey in last_not_voted:
            survey_context = context | {
                'survey': survey.get_render_info(context['user'])
            }
            rendered_surveys.append(render_to_string('survey.html', survey_context, request))
        return JsonResponse(
            APIResponseTemplate.success(
                data = {
                    'surveys': rendered_surveys,
                    'any_left': any_left,
                    'last_post_id': last_id
                }
            )
        )


@get_base_context
@authentication_required
@limit_avaliable_method
def create_survey(request, context):
    if request.method == 'POST':
        form = SurveyCreateForm(request.POST)
        if not form.is_valid():
            return GenericAPIResponses.invalid_form(form)

        Survey.create(
            user = context['user'],
            title = form.cleaned_data['title'],
            description = form.cleaned_data['description'],
            allow_multiple = form.cleaned_data.get('allow_multiple'),
            vote_options = form.cleaned_data.get('vote_option')
        )

        return redirect('/')


@get_base_context
@authentication_required
@limit_avaliable_method
def vote_survey(request, context):
    if request.method == 'POST':
        form = SurveyVoteForm(request.POST)
        if not form.is_valid():
            return GenericAPIResponses.invalid_form(form)
        
        choice_ids = form.cleaned_data['choice_ids']
        vote_options = VoteOption.objects.filter(id__in=choice_ids)

        survey = vote_options.first().survey
        if survey in context['user'].get_voted_surveys():
            return JsonResponse(
                data=APIResponseTemplate.error(
                    detail='You have already voted in this survey'
                ),
                status=409
            )

        for option in vote_options:
            vote = Vote(
                user = context['user'],
                vote_option = option
            )
            vote.save()

        context['survey'] = survey.get_render_info(context['user'])
        return JsonResponse(
            APIResponseTemplate.success(
                data = {
                    'new_html': render_to_string('survey_base.html', context)
                }
            )
        )


@get_base_context
@authentication_required
@limit_avaliable_method
def get_survey(request, context):
    if request.method == 'GET':
        survey_id = request.GET.get('id')
        survey = Survey.objects.filter(id=survey_id).first()
        if survey is None:
            return JsonResponse(
                APIResponseTemplate.error(
                    detail='Survey not found'
                ),
                status=404
            )

        context['survey'] = survey.get_render_info(context['user'])
        return JsonResponse(
            APIResponseTemplate.success(
                data = {
                    'html': render_to_string('survey.html', context)
                }
            )
        )


@get_base_context
@authentication_required
@limit_avaliable_method
def get_new_surveys(request, context):
    if request.method == 'POST':
        return render_slice_to_responce(
            request,
            context,
            context['user'].get_unvoted_surveys(),
            request.POST.get('start_from'),
            request.POST.get('amount')
        )


@get_base_context
@limit_avaliable_method
def get_user_surveys(request, context):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        try:
            user = User.objects.filter(id=user_id).first()
        except ValidationError:
            user = context['user']
        
        if user is None:
            return APIResponseTemplate.error({
                'detail': 'Invalid user id'
            })

        return render_slice_to_responce(
            request,
            context,
            Survey.objects.filter(user=user),
            request.POST.get('start_from'),
            request.POST.get('amount')
        )


@get_base_context
@authentication_required
@limit_avaliable_method
def get_user_history(request, context):
    if request.method == 'POST':
        return render_slice_to_responce(
            request,
            context,
            context['user'].get_voted_surveys(),
            request.POST.get('start_from'),
            request.POST.get('amount')
        )