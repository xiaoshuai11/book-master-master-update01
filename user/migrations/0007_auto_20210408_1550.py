# Generated by Django 2.0.1 on 2021-04-08 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_rate_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='shuxin',
            field=models.CharField(default='张帅', max_length=32, unique=True, verbose_name='属性'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(max_length=32, unique=True, verbose_name='姓名'),
        ),
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=32, unique=True, verbose_name='账号名'),
        ),
    ]
