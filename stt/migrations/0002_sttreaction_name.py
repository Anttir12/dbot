# Generated by Django 3.2.15 on 2022-08-17 15:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stt', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sttreaction',
            name='name',
            field=models.CharField(default='a', max_length=256),
            preserve_default=False,
        ),
    ]