from django import forms

class UserSignupForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254, required=True)
    password = forms.CharField(label="Password", min_length=8, max_length=128, 
                               widget=forms.PasswordInput(), required=True)
    confirm_password = forms.CharField(label="Confirm password", min_length=8, max_length=128,
                                       widget=forms.PasswordInput(), required=True)
    username = forms.CharField(label="Username", max_length=50, required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError('passwords do not match')


class UserLoginForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254, required=True)
    password = forms.CharField(label="Password", min_length=8, max_length=128, 
                               widget=forms.PasswordInput(), required=True)


class UserEditForm(forms.Form):
    email = forms.EmailField(label="New email", max_length=254, required=False)
    password = forms.CharField(label="New password", min_length=8, max_length=128, 
                               widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(label="Confirm new password", min_length=8, max_length=128,
                                       widget=forms.PasswordInput(), required=False)
    username = forms.CharField(label="New username", max_length=50, required=False)
    reset_username = forms.BooleanField(label="Reset to default", required=False)
    profile_picture = forms.FileField(label='Upload profile picture', required=False)
    reset_profile_picture = forms.BooleanField(label="Reset to default", required=False)

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password is not None and password != confirm_password:
            raise forms.ValidationError('passwords do not match')
        return cleaned_data

class UserIssuesForm(forms.Form):
    title = forms.CharField(label= "Title", min_length=10, max_length=100,required=True)
    content = forms.CharField(label="Description of issue", required=True)
    trouble_file = forms.FileField(label='Upload Files to Help Issue', required=False)
    def clean(self):
        cleaned_data = super().clean()
        
        if cleaned_data.get('title') is None or cleaned_data.get('content') is None:
            raise forms.ValidationError("Title or Description of issue can't be empty")

        return cleaned_data
class UserIssuesMsgForm(forms.Form):
    content = forms.CharField(label= "Create Message", required=True)
    trouble_file = forms.FileField(label='Upload Files', required=False)
    def clean(self):
        cleaned_data = super().clean()
        
        if cleaned_data.get('content') is None:
            raise forms.ValidationError("Content of Message goes BRRRRRR")
        return cleaned_data

class SurveyCreateForm(forms.Form):
    title = forms.CharField(label="Title", max_length=200, required=True)
    description = forms.CharField(label="Description", required=False)
    type = forms.ChoiceField(choices=[(1, "1:N"),
                                      (2, "M:N"), 
                                      (3, "YES/NO")], label="Type", required=False)
    allow_multiple = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()

        options = [x.strip() 
                   for x in self.data.getlist('vote_option') 
                   if x.strip() != ""]

        if options is None or len(options) < 1:
            raise forms.ValidationError(
                'Surveys must have at least 1 vote option'
            )

        if any(len(option) > 100 for option in options):
            raise forms.ValidationError(
                'Vote options can\'t be longer than 100 characters'
            )

        cleaned_data['vote_option'] = options
        return cleaned_data


def nullable_pop(dict_, key):
    try:
        return dict_.pop(key)
    except KeyError:
        return None

class SurveyVoteForm(forms.Form):
    def __init__(self, *args, **kwargs):
        fields = nullable_pop(kwargs, 'vote_options')

        super().__init__(*args, **kwargs)

        if fields:
            self.fields['options'] = forms.MultipleChoiceField(
                                        widget=forms.CheckboxSelectMultiple, 
                                        choices=fields, 
                                        required=True)

    def clean(self):
        cleaned_data = super().clean()
        
        cleaned_data['choice_ids'] = self.data.getlist('choice_id') + \
                                    self.data.getlist('choice_id[]')    # :\
                                    
        if len(cleaned_data['choice_ids']) == 0:
            raise forms.ValidationError(
                'You. Must. Vote.'
            )

        return cleaned_data
