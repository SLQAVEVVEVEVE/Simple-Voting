# Generated by Django 4.0 on 2022-01-03 07:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0005_remove_user_photo_user_profile_picture_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='profile_picture_id',
            field=models.CharField(default=None, max_length=32, null=True),
        ),
    ]
