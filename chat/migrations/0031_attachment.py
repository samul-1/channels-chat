# Generated by Django 3.0.7 on 2020-07-10 22:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0030_auto_20200702_0045'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/%Y/%m/%d/')),
            ],
        ),
    ]