# Generated by Django 5.0.7 on 2024-09-17 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=10, unique=True)),
                ('username', models.CharField(db_column='user_username', max_length=150, unique=True)),
                ('email', models.EmailField(db_column='user_email', max_length=255, unique=True)),
                ('password', models.CharField(db_column='user_pwd', max_length=255)),
                ('tel', models.CharField(db_column='user_tel', max_length=10)),
            ],
            options={
                'db_table': 'user',
            },
        ),
    ]