import os
import uuid

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password, check_password



def get_media_root():
    path = os.path.join(settings.MEDIA_ROOT)

    # Ensure path to file is valid
    try:
        os.makedirs(path)
    finally:
        return path

def save_file(file_data):
    filename = uuid.uuid4().hex
    media_path = get_media_root()
    filepath = os.path.join(media_path, filename)
    with open(filepath, 'wb') as f:
        for chunk in file_data.chunks():
            f.write(chunk)
    return filename

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254, unique=True)
    password = models.CharField(max_length=100)
    profile_picture_file = models.CharField(max_length=32, null=True, default=None)
    username = models.CharField(max_length=50, default="Anonymous")
    is_superuser = models.BooleanField(default=False)

    @classmethod
    def create(cls, **obj_fields):
        plain_passwd = obj_fields.get('password')
        obj_fields['password'] = make_password(plain_passwd)

        username = obj_fields.get('username')
        if username == '':
            obj_fields['username'] = 'Anonymous'

        return cls(**obj_fields)

    def check_password(self, password: str):
        return check_password(password, self.password)

    @staticmethod
    def check_credentials(email: str, password: str):
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        return None

    @staticmethod
    def update_user(user, email, password, username, reset_username,
                    profile_picture, reset_profile_picture, **gibberish):
        if email:
            if User.objects.filter(email=email) and user.email != email:
                return 'Provided email address is already taken'
            else:
                user.email = email
        
        if password:
            user.password = make_password(password)

        if reset_username:
            user.username = 'Anonymous'
        elif username:
            user.username = username

        # If profile picture is being changed
        if reset_profile_picture or profile_picture:
            # Delete previous profile picture
            media_path = get_media_root()
            if user.profile_picture_file is not None:
                filepath = os.path.join(media_path, user.profile_picture_file)

                try:
                    os.remove(filepath)
                except FileNotFoundError:
                    pass
                
                user.profile_picture_file = None

            # If file is being uploaded, create new with random filename
            if profile_picture:
                user.profile_picture_file = save_file(profile_picture)

        user.save()
        return None

    def get_voted_surveys(self):
        vote_option_ids = Vote.objects.filter(user=self).values_list('vote_option')
        vote_options = VoteOption.objects.filter(id__in=vote_option_ids)
        survey_ids = vote_options.values_list('survey').distinct()
        return Survey.objects.filter(id__in=survey_ids)

    def best_survey(self):
        user_surveys = Survey.objects.filter(user=self)
        if user_surveys.count() == 0:
            return None
            
        best_survey = user_surveys[0]
        for survey in user_surveys[1:]:
            if survey.votes.count() > best_survey.votes.count():
                best_survey = survey

        return best_survey

    def get_unvoted_surveys(self):
        user_votes = Vote.objects.filter(user=self).values('vote_option_id')
        surveys_voted = VoteOption.objects.filter(id__in=user_votes).values('survey_id').distinct()
        return Survey.objects.exclude(id__in=surveys_voted)

    def add_account_context(self, context):
        context['number_of_surveys'] = Survey.objects.filter(user=self).count()
        context['best_survey'] = None

        best_survey = self.best_survey()
        if best_survey is not None:
            context['best_survey'] = best_survey.get_render_info(context['user'])

        return context


class Survey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(default="")
    allow_multiple = models.BooleanField(default=False)
    creation_datetime = models.DateTimeField(default=timezone.now)
    
    @property
    def vote_options(self):
        return VoteOption.objects.filter(survey=self)

    @property
    def votes(self):
        return Vote.objects.filter(vote_option__in=self.vote_options)

    @classmethod
    def create(cls, user, title, description, allow_multiple, vote_options, **fields):
        survey = Survey(
            user = user,
            title = title,
            description = description,
            allow_multiple = True if allow_multiple else False  # For some reason, Django forms
                                                                # return allow_multiple as None
                                                                # or as 'on', so this workaround
                                                                # is required :\
        )
        survey.save()

        for option in vote_options:
            vote_option = VoteOption(
                survey = survey,
                content = option
            )
            vote_option.save()

        return survey

    def get_voted_fraction(self, vote_option):
        unique_users_votes = self.votes.values('user').distinct().count()
        if unique_users_votes == 0:
            return 0

        option_votes = vote_option.votes.count()
        return option_votes / unique_users_votes
    
    def get_render_info(self, user):
        render_info = {
            'allow_multiple': self.allow_multiple,
            'creation_datetime': self.creation_datetime,
            'title': self.title,
            'description': self.description,
            'vote_options': {},
            'user': {
                'id': self.user.id,
                'profile_picture': self.user.profile_picture_file,
                'username': self.user.username,
            },
            'show_results': self in user.get_voted_surveys(),
        }

        for vote_option in self.vote_options:
            render_info['vote_options'] |= {
                str(vote_option.id): {
                    'content': vote_option.content,
                    'voted_fraction': self.get_voted_fraction(vote_option)
                }
            }

        return render_info

    @staticmethod
    def get_survey_slice(surveys, start_from, amount):
        surveys = surveys.order_by('-creation_datetime')
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            amount = 1

        try:
            start_index = 0
            start_uuid = uuid.UUID(start_from)
            for idx, survey in enumerate(surveys):
                if survey.id == start_uuid:
                    start_index = idx + 1
                    break
        except (ValueError, TypeError, ValidationError):
            pass
        
        survey_slice = list(surveys[start_index:start_index + amount])
        any_left = start_index + amount < len(surveys)
        if len(survey_slice) != 0: 
            last_id = survey_slice[-1].id
        elif len(surveys) != 0:
            last_id = surveys.last().id
        else:
            last_id = None

        return survey_slice, any_left, last_id

        

class VoteOption(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    content = models.CharField(max_length=100)

    @property
    def votes(self):
        return Vote.objects.filter(vote_option=self)


class Vote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vote_option = models.ForeignKey(VoteOption, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote_datetime = models.DateTimeField(default=timezone.now)


class Issue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    is_closed = models.BooleanField(default=False)
    creation_datetime = models.DateTimeField(default=timezone.now)


class IssueMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE)
    content = models.TextField()
    trouble_file = models.CharField(max_length=32, null=True, default=None)
    from_support = models.BooleanField(default=False)
    send_datetime = models.DateTimeField(default=timezone.now)


