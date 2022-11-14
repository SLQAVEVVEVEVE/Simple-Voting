import jwt
import inspect
import datetime
from functools import wraps
from django.conf import settings
from django.db import IntegrityError
from django.forms import ValidationError
from django.shortcuts import render, redirect

from api.responses import GenericAPIResponses

from .models import Survey, User, IssueMessage, Issue, save_file
from .forms import SurveyCreateForm, UserEditForm, UserLoginForm, UserSignupForm, UserIssuesForm, UserIssuesMsgForm


def update_session(response, user):
    token_data = {'email': user.email}
    token = jwt.encode(token_data, settings.SECRET_KEY, algorithm='HS256')
    response.set_cookie('auth_token', token, max_age=3600*24*30)


def get_user(request):
    # Check if session cookie is present
    if 'auth_token' not in request.COOKIES:
        return None
    auth_token = request.COOKIES['auth_token']  

    try:
        token_data = jwt.decode(auth_token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.DecodeError:
        # If token is invalid
        return None
    
    # User.objects.get() would raise DoesNotExist error if 
    # user doesn't exist. Due to the fact that JWT is signed,
    # that should never happen, but better be safe than sorry 
    user = User.objects.filter(email=token_data['email']).first()
    return user


def get_base_context(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        # If someone accidentally tries to use this on function that
        # does not accept context argument, this error will be raised
        # Hopefully, will never be executed
        view_args = inspect.getargspec(view).args
        if 'context' not in view_args:
            raise NotImplementedError(
                f'View function "{view.__name__}" doesn\'t accept context argument, but uses "add_base_context" decorator'
            )

        user = get_user(request)

        context = {
            'current_time': datetime.datetime.now(),
            'user': user
        }

        return view(request, context=context)
    return wrapper

def authentication_required(view):
    @wraps(view)
    def wrapper(request, context, *args, **kwargs):
        user = context['user']

        if user is None:
            if request.method == 'GET':
                return render(request, 'error.html', status=401, context={
                    'status_code': 401,
                    'error': '401 Unauthorized',
                    'details': 'Authentication is required to view this page'
                })
            else:
                return GenericAPIResponses.AUTHENTICATION_REQUIRED
        else:
            return view(request, context)
    return wrapper

def admin_only(view):
    @wraps(view)
    def wrapper(request, context, *args, **kwargs):
        user = context['user']

        if user.is_superuser is False:
            return render(request, 'error.html', status=403, context={
                'status_code': 403,
                'error': '403 Forbidden',
                'details': 'You haven`t got priveleges to enter this page'
            })
        else:
            return view(request, context)
    return wrapper


@get_base_context
def index_page(request, context):
    if request.method == 'GET':
        user = context['user']
        if user is None:
            return redirect('/account/login')

        context['create_survey_form'] = SurveyCreateForm
        return render(request, 'index.html', context)
    
    else:
        return redirect('/')


@get_base_context
def signup(request, context):
    if request.method == 'GET':
        return render(request, 'signup.html', context)

    elif request.method == 'POST':
        form = UserSignupForm(request.POST)
        if not form.is_valid():
            context['form_errors'] = form.non_field_errors
            return render(request, 'signup.html', context)
        
        try:
            user = User.create(
                email = form.data['email'],
                password = form.data['password'],
                username = form.data['username'],
            )
            user.save()
        except IntegrityError:
            context['form_errors'] = ['User with provided email is already registered :O']
            return render(request, 'signup.html', context)

        response = redirect('/')
        update_session(response, user)
        return response


@get_base_context
def login(request, context):
    if request.method == 'GET':
        context['form'] = UserLoginForm
        return render(request, 'login.html', context)

    elif request.method == 'POST':
        form = UserLoginForm(request.POST)
        if not form.is_valid():
            context['form_errors'] = form.non_field_errors
            return render(request, 'login.html', context)
        
        user = User.check_credentials(form.data['email'], form.data['password'])
        if user is None:
            context['form_errors'] = ['User with provided credentials does not exist']
            return render(request, 'login.html', context)

        response = redirect('/')
        update_session(response, user)
        return response


def logout(request):
    response = redirect('/')
    response.delete_cookie('auth_token')
    return response


@get_base_context
def view_account(request, context):
    if request.method == 'GET':
        user_id = request.GET.get('id')
        user = context['user']
        owner = None

        if user_id is None:
            if user is None:
                return redirect('/')
            owner = user

        else:
            try:
                owner = User.objects.filter(id=user_id).first()
            except ValidationError:
                pass

            if owner is None:
                if user is not None:
                    return redirect('/account')
                else:
                    return render(request, 'error.html', status=404, context={
                        'status_code': 404,
                        'error': '404 Not Found',
                        'details': 'This account does not exist O.O'
                    })
            else:
                if user == owner:
                    return redirect('/account')
                


        context['owner'] = owner
        owner.add_account_context(context)

        return render(request, 'account.html', context)

    elif request.method == 'POST':
        return edit_account_handler(request, context)


@authentication_required
def edit_account_handler(request, context):
    context['owner'] = context['user']
    context['owner'].add_account_context(context)

    form = UserEditForm(request.POST, request.FILES)
    if not form.is_valid():
        context['form_errors'] = form.non_field_errors
        return render(request, 'account.html', context)

    err = User.update_user(
        user = context['user'],
        email = form.data['email'],
        password = form.data['password'],
        username = form.data['username'],
        reset_username = form.data.get('reset_username'),
        profile_picture = request.FILES.get('profile_picture'),
        reset_profile_picture = form.data.get('reset_profile_picture')
    )
    if err is not None:
        form.add_error(None, err)
        return render(request, 'account.html', context)
        
    # Update session cookie, so user doesn't get kicked out if email is changed
    response = render(request, 'account.html', context)
    update_session(response, context['user'])
    return response


@get_base_context
@authentication_required
def view_history(request, context):
    if request.method == 'GET':
        return render(request, 'history.html', context)


@get_base_context
@authentication_required
def create_issue(request,context):
    if request.method == 'GET':
        return redirect('/issue/chats')
        
    elif request.method == 'POST':
        form = UserIssuesForm(request.POST, request.FILES)
        if not form.is_valid():
            context['form_errors'] = form.non_field_errors
            return render(request, 'issue_chats.html', context)

        issue = Issue(
            user=context["user"],
            title=request.POST.get('title'),
            is_closed=False
        )
        if request.FILES.get('trouble_file') == None:
            issue_msg = IssueMessage(
            issue=issue,
            content=request.POST.get('content'),
            )
        else:
            issue_msg = IssueMessage(
            issue=issue,
            content=request.POST.get('content'),
            trouble_file=save_file(request.FILES.get('trouble_file'))
            )
        issue.save()
        issue_msg.save()
        return redirect("/issue/chats")

@get_base_context
@authentication_required
def close_issue(request,context):
    if request.method == 'POST':
        issue = Issue.objects.filter(id=request.POST.get('issue_id')).first()
        if issue.user == context["user"]:
            issue.is_closed = True
            issue.save()

            issue_id = request.POST.get('issue_id')
            print(issue_id)
            print(request.POST)
            return redirect(f"/issue/messages/?id={issue_id}")

@get_base_context
@authentication_required
def issue_chats(request,context):
    if request.method == 'GET':
        if context['user'].is_superuser:
            return redirect('/admin')

        context['issues_arr'] = Issue.objects.all().filter(user_id = context["user"]).order_by('is_closed', '-creation_datetime')
        return render(request, 'issue_chats.html', context)
    elif request.method == 'POST':
        redirect("/issue/chats")
    return render(request,'issue_chats.html',context)

@get_base_context
@authentication_required
def issue_chat_messages(request, context):
    if request.method == "GET":
        if request.GET.get("id") is not None:

            issue_id = request.GET.get("id")
            issue = Issue.objects.filter(id=issue_id).first()
            
            context["form"] = UserIssuesMsgForm
            if (issue.user == context["user"] and Issue.objects.filter(id=issue.id).exists or context["user"].is_superuser):
                context["issue_msg_arr"] = IssueMessage.objects.all().filter(issue=issue_id)
                context["current_issue"] = issue
                return render(request,'issue_chat_messages.html',context)
            else:
                return render(request, 'error.html', status=404, context={
                    'status_code': 404,
                    'error': '404 Not Found',
                    'details': 'Issue not found or your are not the owner of this issue POG'
                })
        else:
            return redirect("/issue/chats")

    elif request.method == "POST":
        form = UserIssuesMsgForm(request.POST, request.FILES)
        context['form'] = form
        issue_id = request.POST.get('issue_id')
        issue = Issue.objects.filter(id=issue_id).first()
        if not form.is_valid():
            return redirect(f"/issue/messages?id={issue_id}")

        issue_id = request.POST.get('issue_id')
        issue = Issue.objects.filter(id=issue_id).first()
        issue_msg = IssueMessage(
            issue=issue,
            content=request.POST.get('content'),
        )

        if request.FILES.get('trouble_file') is not None:
            issue_msg.trouble_file = save_file(request.FILES.get('trouble_file'))
        if context["user"].is_superuser:
            issue_msg.from_support = True

        issue_msg.save()
        return redirect(f"/issue/messages?id={issue_id}")


@get_base_context
@authentication_required
@admin_only
def admin_issues(request, context):
    if request.method == 'GET':
        context['issues_arr'] = Issue.objects.filter(is_closed=False).order_by('-creation_datetime')
        return render(request, 'issue_chats.html', context)

    elif request.method == 'POST':
        redirect("/issue/chats")

    return render(request,'issue_chats.html',context)
