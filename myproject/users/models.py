from django.db import models
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import AbstractUser, BaseUserManager,AbstractBaseUser
from django.contrib.auth.models import User
import bcrypt
import uuid
import os
from django.utils.timezone import now
from django.utils.crypto import get_random_string
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

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # Use set_password to hash the password
        user.save(using=self._db)
        return user

class Users(models.Model):
    user_id = models.CharField(max_length=10, unique=True, primary_key=True, db_column='user_id')
    username = models.CharField(max_length=150, unique=True, db_column='user_username')
    password = models.CharField(max_length=255, db_column='user_pwd')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')
    email = models.EmailField(max_length=255, unique=True, db_column='user_email')
    tel = models.CharField(max_length=10, db_column='user_tel')
    user_fname = models.CharField(max_length=50, db_column='user_fname')
    user_role = models.CharField(max_length=10, db_column='user_role')
    user_lname = models.CharField(max_length=50, db_column='user_lname')

    class Meta:
        db_table = 'user'  # Use your actual table name in MySQL
        managed = False

    @property
    def is_authenticated(self):
        return True  # Indicate that the user is authenticated

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))

    def __str__(self):
        return self.username


class Admins(models.Model):
    admin_id = models.CharField(max_length=10, unique=True, primary_key=True, db_column='admin_id')
    admin_username = models.CharField(max_length=150, unique=True, db_column='admin_username')  # Changed field name
    admin_pwd = models.CharField(max_length=255, db_column='admin_pwd')  # Ensure the field name matches
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')
    admin_email = models.EmailField(max_length=255, unique=True, db_column='admin_email')
    admin_tel = models.CharField(max_length=10, db_column='admin_tel')
    admin_name = models.CharField(max_length=50, db_column='admin_fname')
    admin_role = models.CharField(max_length=10, db_column='admin_role')
    admin_lname = models.CharField(max_length=50, db_column='admin_lname')

    class Meta:
        db_table = 'admin'  # Use your actual table name in MySQL
        managed = False

    @property
    def is_authenticated(self):
        return True  # Indicate that the admin is authenticated
    @property
    def is_active(self):
        return True  # or add logic if you have specific active conditions
    
    @property
    def is_staff(self):
        return True  # Consider all admins as staff; modify as needed for your logic

    def set_password(self, raw_password):
        self.admin_pwd = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        is_correct = bcrypt.checkpw(raw_password.encode('utf-8'), self.admin_pwd.encode('utf-8'))  # Update to admin_pwd
        print(f"Checking password for {self.admin_username}: {raw_password} -> {is_correct}")
        return is_correct

    def __str__(self):
        return self.admin_username

    

class ProposedText(models.Model):
    text_id = models.CharField(max_length=25, unique=True, primary_key=True, db_column='text_id')
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    proposed_text = models.TextField(max_length=255, db_column='word_text')
    word_class = models.SmallIntegerField(db_column='word_class', default=0)
    word_status = models.CharField(db_column="word_status", max_length=30, null=True, blank=True, default="รออนุมัติ")
    upload_id = models.ForeignKey('ProposedFile', on_delete=models.CASCADE, db_column='uploaded_id')  # ForeignKey to ProposedFile
    word_class_type = models.CharField(max_length=100, db_column='word_class_type', null=True, blank=True)  # New field for word class type
    admin = models.ForeignKey(Admins, on_delete=models.CASCADE, db_column='admin_id', null=True, blank=True)
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

class AnnotatedText(models.Model):
    annotated_id = models.BigIntegerField(  # Use BigIntegerField for larger numeric values
        unique=True,
        primary_key=True,
        db_column='annotated_id'
    )
    task_id = models.ForeignKey(
        'Task',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='task_id'
    )
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    annotated_class = models.SmallIntegerField(db_column='annotated_class')
    annotated_type = models.CharField(max_length=30, null=True, blank=True,default="1", db_column='annotated_type')
    annotated_text = models.TextField(db_column='annotated_text')
    annotated_date = models.DateTimeField(auto_now_add=True, db_column='annotated_date')
    text_id = models.ForeignKey('ProposedText', on_delete=models.CASCADE, null=True, blank=True, db_column='text_id')

    class Meta:
        db_table = 'annotated_text'

class Task(models.Model):
    task_id = models.CharField(max_length=6, unique=True, primary_key=True, db_column='task_id')  # Set max_length to 6
    admin = models.ForeignKey(
        'Admins',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='admin_id'
    )
    task_name = models.CharField(max_length=50, db_column='task_name')
    created_date = models.DateField(db_column='created_date')
    due_date = models.DateField(db_column='due_date')
    kappa_score = models.FloatField(db_column='kappa_score')
    task_status = models.SmallIntegerField(db_column='task_status')

    class Meta:
        db_table = 'task'

    def __str__(self):
        return self.task_name
    
class UserTask(models.Model):
    user_task_id = models.AutoField(primary_key=True)  # Primary Key
    task = models.ForeignKey(Task, on_delete=models.CASCADE)  # Foreign Key to Task
    user = models.ForeignKey(Users, on_delete=models.CASCADE)  # Foreign Key to User
    assigned_date = models.DateField()  # Date when the task was assigned
    latest_assign_date = models.DateField()  # Latest date the task was assigned

    def __str__(self):
        return f"UserTask {self.user_task_id} - User: {self.user.username}, Task: {self.task}"

    class Meta:
        db_table = 'user_task'
        verbose_name = "User Task"
        verbose_name_plural = "User Tasks"