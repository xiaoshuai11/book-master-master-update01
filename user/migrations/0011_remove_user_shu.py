# Generated by Django 2.0.1 on 2021-04-08 08:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0010_auto_20210408_1603'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='shu',
        ),
    ]
