# Generated by Django 4.0 on 2022-01-14 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0008_issuemessage_rename_complaint_issue_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='issuemessage',
            old_name='complaint',
            new_name='issue',
        ),
        migrations.RenameField(
            model_name='issuemessage',
            old_name='trouble_files',
            new_name='trouble_file',
        ),
    ]
