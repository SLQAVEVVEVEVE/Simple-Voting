# Generated by Django 4.0 on 2022-01-03 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0004_rename_password_hash_user_password_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='photo',
        ),
        migrations.AddField(
            model_name='user',
            name='profile_picture_id',
            field=models.UUIDField(default=None, null=True),
        ),
    ]
