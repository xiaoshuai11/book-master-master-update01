# Generated by Django 2.0.1 on 2021-04-08 07:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0008_auto_20210408_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='shuxin',
            field=models.CharField(default='aaa', max_length=32, verbose_name='属性'),
        ),
    ]
