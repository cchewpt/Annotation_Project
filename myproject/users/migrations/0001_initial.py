# Generated by Django 5.1.1 on 2024-10-06 13:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Users',
            fields=[
                ('user_id', models.CharField(db_column='user_id', max_length=10, primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(db_column='user_username', max_length=150, unique=True)),
                ('password', models.CharField(db_column='user_pwd', max_length=255)),
            ],
            options={
                'db_table': 'user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='user_map',
            fields=[
                ('user_id', models.CharField(max_length=10, primary_key=True, serialize=False, unique=True)),
                ('username', models.CharField(db_column='user_username', max_length=150, unique=True)),
                ('email', models.EmailField(db_column='user_email', max_length=255, unique=True)),
                ('password', models.CharField(db_column='user_pwd', max_length=255)),
                ('tel', models.CharField(db_column='user_tel', max_length=10)),
                ('user_role', models.CharField(db_column='user_role', max_length=10)),
            ],
            options={
                'db_table': 'user',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='ProposedText',
            fields=[
                ('text_id', models.AutoField(db_column='text_id', primary_key=True, serialize=False, unique=True)),
                ('propose_t_admin_id', models.CharField(db_column='propose_t_admin_id', max_length=10)),
                ('propose_t_uploaded_id', models.CharField(db_column='propose_t_uploaded_id', max_length=10)),
                ('uploaded_id', models.CharField(db_column='uploaded_id', max_length=10)),
                ('user_proposed_text', models.TextField(db_column='word_text', max_length=255)),
                ('word_status', models.CharField(db_column='word_status', default='รออนุมัติ', max_length=15)),
                ('word_class', models.CharField(db_column='word_class', max_length=16)),
                ('word_class_type', models.CharField(db_column='word_class_type', max_length=20)),
                ('proposed_t_user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.users')),
            ],
            options={
                'db_table': 'proposed_text',
                'managed': True,
            },
        ),
    ]