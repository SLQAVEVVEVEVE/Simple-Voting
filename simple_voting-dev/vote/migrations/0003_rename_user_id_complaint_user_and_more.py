# Generated by Django 4.0 on 2022-01-02 09:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0002_complaint_survey_remove_user_age_remove_user_desc_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='complaint',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='complaintmessage',
            old_name='complaint_id',
            new_name='complaint',
        ),
        migrations.RenameField(
            model_name='survey',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='vote',
            old_name='user_id',
            new_name='user',
        ),
        migrations.RenameField(
            model_name='vote',
            old_name='vote_option_id',
            new_name='vote_option',
        ),
        migrations.RenameField(
            model_name='voteoption',
            old_name='survey_id',
            new_name='survey',
        ),
    ]
