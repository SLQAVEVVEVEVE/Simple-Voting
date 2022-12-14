# Generated by Django 4.0 on 2022-01-14 17:17

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('vote', '0007_rename_profile_picture_id_user_profile_picture_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssueMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('trouble_files', models.CharField(default=None, max_length=32, null=True)),
                ('from_support', models.BooleanField(default=False)),
                ('send_datetime', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.RenameModel(
            old_name='Complaint',
            new_name='Issue',
        ),
        migrations.DeleteModel(
            name='ComplaintMessage',
        ),
        migrations.AddField(
            model_name='issuemessage',
            name='complaint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vote.issue'),
        ),
    ]
