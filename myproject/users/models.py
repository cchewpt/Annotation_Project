from django.db import models
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
import bcrypt
import uuid
import os
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class user_map(models.Model):
    user_id = models.CharField(max_length=10, unique=True, primary_key=True) # Field for user_id
    username = models.CharField(max_length=150, unique=True,db_column='user_username')
    email = models.EmailField(max_length=255, unique=True,db_column='user_email')
    password = models.CharField(max_length=255,db_column='user_pwd')
    tel = models.CharField(max_length=10,db_column='user_tel')
    user_role = models.CharField(max_length=10,db_column='user_role')
    
    class Meta:
        db_table = 'user'  # กำหนดชื่อตารางเป็น 'user'
        managed = True

class Users(models.Model):
    user_id = models.CharField(max_length=10, unique=True, primary_key=True, db_column='user_id')
    username = models.CharField(max_length=150, unique=True, db_column='user_username')
    password = models.CharField(max_length=255, db_column='user_pwd')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')
    email = models.EmailField(max_length=255, unique=True, db_column='user_email')
    tel = models.CharField(max_length=10,db_column='user_tel')
    user_fname = models.CharField(max_length=50,db_column='user_fname')
    user_lname = models.CharField(max_length=50,db_column='user_lname')

    class Meta:
        db_table = 'user'  # Use your actual table name in MySQL
        managed = False

    @property
    def is_authenticated(self):
        return True  # Custom implementation for your Users model

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))

    def __str__(self):
        return self.username
    

class ProposedText(models.Model):
    text_id = models.CharField(max_length=25, unique=True, primary_key=True, db_column='text_id')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    proposed_text = models.TextField(max_length=255, db_column='word_text')
    word_class = models.SmallIntegerField(db_column='word_class', default=0)
    word_status = models.CharField(db_column="word_status", max_length=30, null=True, blank=True, default="รออนุมัติ")
    upload_id = models.ForeignKey('ProposedFile', on_delete=models.CASCADE, db_column='uploaded_id')  # ForeignKey to ProposedFile
    word_class_type = models.CharField(max_length=100, db_column='word_class_type', null=True, blank=True)  # New field for word class type

    class Meta:
        db_table = 'proposed_text'
        managed = True

    def __str__(self):
        return self.proposed_text

class ProposedFile(models.Model):
    upload_id = models.CharField(max_length=25,primary_key=True, db_column='upload_id')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    file_name = models.CharField(max_length=50, db_column='file_name')
    file_type = models.CharField(max_length=5, db_column='file_type')
    file_size = models.FloatField(db_column='file_size')
    file_data = models.TextField(db_column='file_data')
    uploaded_date = models.DateTimeField(auto_now_add=True, db_column='uploaded_date')
    file_path = models.TextField(db_column='file_path')
    text_id = models.ForeignKey(ProposedText, on_delete=models.CASCADE, db_column='proposed_text_id')  # Change this to ForeignKey

    class Meta:
        db_table = 'proposed_file'
        managed = True

    def __str__(self):
        return self.file_name

