from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login as auth_login
from django.db import connection
from django.contrib import messages
from io import TextIOWrapper
from .models import user_map, Users, ProposedText, ProposedFile,Admins,Task,AnnotatedText,UserTask
import bcrypt  # Import bcrypt for password hashing
import logging
from django.core.paginator import Paginator
import json
import uuid
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import xml.etree.ElementTree as ET
from django.db import transaction, IntegrityError
from django.utils.timezone import now
from django.http import HttpResponse
from django.core.exceptions import ValidationError
import csv
import datetime
import xml.etree.ElementTree as ET
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user
from django.db import models
import random
from django.contrib.auth.backends import BaseBackend
from django.utils.translation import gettext as _
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.crypto import get_random_string
from django.http import JsonResponse
from django.http import Http404
logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'index.html')  # แสดงหน้า home.html

def edit_profile(request):
    if request.user.is_authenticated:
            if request.method == 'POST':
                # Get the current authenticated user
                user = request.user

                # Fetch data from the form
                user_fname = request.POST.get('user_fname', '').strip()  # Use empty string if not provided
                user_lname = request.POST.get('user_lname', '').strip()
                email = request.POST.get('email', '').strip()
                tel = request.POST.get('tel', '').strip()

                # Update the user's data
                try:
                    user.user_fname = user_fname  # Safely update even if the field was empty before
                    user.user_lname = user_lname
                    user.email = email
                    user.tel = tel  # Assuming the 'tel' field exists in your Users model

                    # Save changes to the database
                    user.save()

                    # Send a success message
                    messages.success(request, "Profile updated successfully!")
                    return redirect('user_profile')  # Redirect to a profile page after saving
                except Exception as e:
                    # If something goes wrong, send an error message
                    messages.error(request, f"Error updating profile: {str(e)}")
                    return redirect('edit_profile')

            # For GET request, display the current data with default empty values if fields are None
            return render(request, 'accounts/edit_profile.html', {
                'username': request.user.username,
                'user_id': request.user.user_id,
                'user_fname': request.user.user_fname or '',  # Use empty string if first_name is None
                'user_lname': request.user.user_lname or '',   # Use empty string if last_name is None
                'email': request.user.email or '',
                'tel': request.user.tel or ''  # Use empty string if tel is None
            })
    else:
        return redirect('login')  # Redirect to login page if not authenticated

def user_profile(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()  # Adjust the condition as needed

        return render(request, 'accounts/user_profile.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count  # Pass the count of supervised texts
        })
    else:
        return redirect('login')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        print(f"Attempting login for username: {username}")

        if not username or not password:
            return render(request, 'login.html', {'error_message': "Both fields are required."})

        # Authenticate Users
        user = authenticate(request, username=username, password=password, backend='users.backends.CustomUserBackend')
        if user is not None and isinstance(user, Users):
            print("User logged in successfully")
            auth_login(request, user)
            return redirect('accounts/mainlogin')
        
        # Authenticate Admins
        admin = authenticate(request, username=username, password=password, backend='users.backends.CustomAdminBackend')
        if admin is not None and isinstance(admin, Admins):
            print("Admin logged in successfully")
            auth_login(request, admin)
            return redirect('accounts/mainlogin')

        print("Invalid username or password.")
        return render(request, 'login.html', {'error_message': "Invalid username or password."})

    return render(request, 'login.html')  # Return the login page if the request is GET
    
def admin_profile(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # Now guaranteed to be an instance of Admins

        return render(request, 'accounts/admin_profile.html', {
            'username': admin.admin_username,  # Use admin-specific fields
            'user_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name
        })
    # Redirect to login if not authenticated or not an Admins instance
    return redirect('login')

def admin_edit_profile(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # Now guaranteed to be an instance of Admins

        if request.method == 'POST':
            # Fetch data from the form
            admin_fname = request.POST.get('user_fname', '').strip()
            admin_lname = request.POST.get('user_lname', '').strip()
            admin_email = request.POST.get('email', '').strip()
            admin_tel = request.POST.get('tel', '').strip()

            # Update the admin's data
            try:
                admin.admin_name = admin_fname
                admin.admin_lname = admin_lname
                admin.admin_email = admin_email
                admin.admin_tel = admin_tel

                # Save changes to the database
                admin.save()

                # Send a success message
                messages.success(request, "Profile updated successfully!")
                return redirect('admin_profile')  # Redirect to a profile page after saving
            except Exception as e:
                # If something goes wrong, send an error message
                messages.error(request, f"Error updating profile: {str(e)}")
                return redirect('admin_edit_profile')

        # For GET request, display the current data
        return render(request, 'accounts/admin_edit_profile.html', {
            'username': admin.admin_username,
            'user_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name
        })

    # Redirect to login if not authenticated or not an Admins instance
    return redirect('login')

def admin_approved1(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user

        # Get unique users who have entries in ProposedText
        user_ids_with_proposed_texts = ProposedText.objects.values_list('user_id', flat=True).distinct()
        users_with_proposed_texts = Users.objects.filter(user_id__in=user_ids_with_proposed_texts)
        

        return render(request, 'accounts/admin_approved1.html', {
            'username': admin.admin_username,
            'admin_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name,
            'users_with_proposed_texts': users_with_proposed_texts
        })

    return redirect('login')

def admin_approved2(request, user_id=None):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # The logged-in admin
        
        if user_id:
            user = get_object_or_404(Users, user_id=user_id)
            proposed_texts = ProposedText.objects.filter(user=user, word_status="รออนุมัติ")
        else:
            user = None
            proposed_texts = ProposedText.objects.filter(word_status="รออนุมัติ")

        proposed_text_count = proposed_texts.count()
        print(proposed_texts)  # Debugging line to check what is being passed

        return render(request, 'accounts/admin_approved2.html', {
            'admin_username': admin.admin_username,
            'admin_id': admin.admin_id,
            'user': user,
            'proposed_texts': proposed_texts,
            'proposed_text_count': proposed_text_count,
        })

    return redirect('login')

def update_text_status(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        text_id = request.POST.get('text_id')
        status = request.POST.get('status')

        proposed_text = get_object_or_404(ProposedText, id=text_id)

        # Update the word status
        proposed_text.word_status = status
        proposed_text.save()

        # If the text is approved and word_class_type is null, add it to annotated_text
        if status == "อนุมัติ" and proposed_text.word_class_type is None:
            annotated_text = AnnotatedText(
                annotated_task_id=proposed_text.id,  # Use appropriate task ID
                annotated_class=None,  # Set the class as needed; might require additional logic
                annotated_type="your_type",  # Replace with appropriate value (if applicable)
                annotated_text=proposed_text.word_text,  # Assuming this field is present
                text_id=proposed_text  # Foreign key relation
            )
            annotated_text.save()

        return redirect('admin_approved2', user_id=proposed_text.user.user_id)  # Redirect back to the admin approved page

    return redirect('login')

def update_text_status(request):
    if request.method == 'POST' and request.user.is_authenticated:
        text_id = request.POST.get('text_id')
        status = request.POST.get('status')

        # Update the status of the proposed text
        proposed_text = get_object_or_404(ProposedText, text_id=text_id)
        proposed_text.word_status = status
        
        # Set the admin who approved or rejected the proposed text
        proposed_text.admin = request.user  # Assuming request.user is an instance of Admins
        proposed_text.save()

        # Redirect back to the 'admin_approved2' view with the user_id
        user_id = proposed_text.user.user_id  # Assuming you want to redirect to the user who proposed the text
        return redirect('admin_approved2_with_user_id', user_id=user_id)

    # Redirect to a different page if not authenticated
    return redirect('login')

@login_required
def admin_edit_user(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user

        # Get the search query from the request
        search_query = request.GET.get('search', '').strip()  # Use .strip() to remove extra whitespace

        # Filter users based on the search query if provided
        if search_query:
            users = Users.objects.filter(username__icontains=search_query)
        else:
            users = Users.objects.all()

        return render(request, 'accounts/admin_edit_user.html', {
            'admin_username': admin.admin_username,
            'admin_id': admin.admin_id,
            'users': users,
            'search_query': search_query,  # Pass the current search query back to the template
        })

    return redirect('login')

def admin_edit_user2(request, user_id):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        # Fetch the user to edit using user_id
        user_to_edit = get_object_or_404(Users, user_id=user_id)

        if request.method == 'POST':
            # Fetch data from the form
            user_fname = request.POST.get('user_fname', '').strip()
            user_lname = request.POST.get('user_lname', '').strip()
            email = request.POST.get('email', '').strip()
            tel = request.POST.get('tel', '').strip()

            # Update the user's data
            try:
                user_to_edit.user_fname = user_fname
                user_to_edit.user_lname = user_lname
                user_to_edit.email = email
                user_to_edit.tel = tel

                # Save changes to the database
                user_to_edit.save()

                # Send a success message
                messages.success(request, "User profile updated successfully!")
                return redirect('admin_edit_user')  # Redirect back to edit page or to user list

            except Exception as e:
                # If something goes wrong, send an error message
                messages.error(request, f"Error updating profile: {str(e)}")
                return redirect('admin_edit_user2', user_id=user_to_edit.user_id)

        # For GET request, display the current data
        return render(request, 'accounts/admin_edit_user2.html', {
            'admin_username': request.user.admin_username,
            'admin_id': request.user.admin_id,
            'user_to_edit': user_to_edit,  # Pass the user data to the template
        })

    return redirect('login')  # Redirect to login page if not authenticated

def admin_assign_data(request, task_id):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        if request.method == 'GET':
            # Retrieve the list of user IDs from the query parameters
            user_ids = request.GET.get('user_ids')
            if user_ids:
                user_ids_list = user_ids.split(',')  # Convert to a list of user IDs

                try:
                    # Retrieve the task object by task_id
                    task = Task.objects.get(task_id=task_id)
                    
                    # Retrieve the texts associated with the task
                    task_texts = AnnotatedText.objects.filter(task_id=task_id).values_list('annotated_text', flat=True)

                    # Iterate over each user and each text in the task to create entries
                    for user_id in user_ids_list:
                        user = Users.objects.get(user_id=user_id)  # Retrieve the user object
                        try:
                            user = Users.objects.get(pk=user_id)  # Get the user object
                            # Create UserTask instance
                            user_task = UserTask.objects.create(
                                user=user,
                                task=task,
                                assigned_date=timezone.now(),
                                latest_assign_date=timezone.now(),
                                user_task_id=generate_user_task_id()  # Call your ID generation function
                            )
                        except Users.DoesNotExist:
                            print(f'User with id {user_id} does not exist.')
                        for text in task_texts:
                            # Generate a unique annotated_id and create an entry for each text-user combination
                            annotated_id = generate_unique_annotated_id()
                            AnnotatedText.objects.create(
                                annotated_id=annotated_id,
                                task_id=task,  # Use 'task_id' as per the model definition
                                user=user,  # Assign the user to this entry
                                annotated_text=text,  # Assign the text
                                annotated_class=0,
                                annotated_type="รอกำกับ",
                                text_id=None,
                            )

                    return redirect('admin_mng_datasets1')

                except Task.DoesNotExist:
                    return redirect('admin_mng_datasets1')

            return redirect('admin_mng_datasets1')

    return redirect('login')

def assign_user_tasks(request):
    if request.method == 'GET':
            user_ids = request.GET.get('user_ids', '').split(',')  # Get user IDs from query params
            task_id = request.GET.get('task_id')

            if task_id and user_ids:
                try:
                    task = Task.objects.get(pk=task_id)  # Get the task object
                except Task.DoesNotExist:
                    return render(request, 'error.html', {'message': 'Task does not exist'})

                for user_id in user_ids:
                    try:
                        user = Users.objects.get(pk=user_id)  # Get the user object
                        # Create UserTask instance
                        user_task = UserTask.objects.create(
                            user=user,
                            task=task,
                            assigned_date=timezone.now(),
                            latest_assign_date=timezone.now(),
                            user_task_id=generate_user_task_id()  # Call your ID generation function
                        )
                    except Users.DoesNotExist:
                        print(f'User with id {user_id} does not exist.')

                return redirect('success_page')  # Redirect after processing
            else:
                return render(request, 'error.html', {'message': 'No users or task selected'})
    return redirect('login')

def calculate_fleiss_kappa(annotated_texts):
    # Use a set to track unique annotated texts that have a user_id
    unique_annotated_texts = {}
    
    for text in annotated_texts:
        if text.user_id is not None:
            unique_annotated_texts[text.annotated_text] = text  # Keep the reference to the text

    # Convert back to a list from the dictionary values
    filtered_annotated_texts = list(unique_annotated_texts.values())
    
    print(f"DEBUG: Filtered annotated texts count (with user_id, unique annotated_text): {len(filtered_annotated_texts)}")  # Debug statement

    # Create a count matrix
    class_counts = {}
    
    for text in filtered_annotated_texts:
        # Initialize class count if not already present
        if text.annotated_class not in class_counts:
            class_counts[text.annotated_class] = {}
        if text.annotated_text not in class_counts[text.annotated_class]:
            class_counts[text.annotated_class][text.annotated_text] = 0
        class_counts[text.annotated_class][text.annotated_text] += 1

    print(f"DEBUG: Class counts: {class_counts}")  # Debug statement

    # Count of unique annotated texts
    N = len(unique_annotated_texts)  # Count of unique annotated texts
    num_classes = len(class_counts)

    print(f"DEBUG: Total number of unique annotations (N): {N}")  # Updated debug statement
    print(f"DEBUG: Number of unique classes: {num_classes}")  # Debug statement

    if N < 2:  # Not enough data to calculate kappa
        print("DEBUG: Not enough annotated texts to calculate kappa.")
        return 0.0

    # Create a matrix where rows are annotated texts and columns are classes
    rating_matrix = []
    
    for text in unique_annotated_texts.keys():
        row = []
        for class_id in range(num_classes):
            count = class_counts.get(class_id, {}).get(text, 0)
            row.append(count)
            print(f"DEBUG: Annotated text '{text}', Class {class_id}: {count}")  # Debug statement
        rating_matrix.append(row)

    print(f"DEBUG: Rating matrix: {rating_matrix}")  # Debug statement

    # Calculate P_o (observed agreement)
    P_o = sum(sum(n_i * (n_i - 1) for n_i in row) for row in rating_matrix) / (N * (N - 1)) if N > 1 else 0
    print(f"DEBUG: Observed agreement (P_o): {P_o}")  # Debug statement

    # Calculate P_e (expected agreement)
    total_per_class = [sum(row[i] for row in rating_matrix) for i in range(num_classes)]
    print(f"DEBUG: Total counts per class: {total_per_class}")  # Debug statement
    
    if N == 0:
        P_e = 0
    else:
        P_e = sum((n_i / N) ** 2 for n_i in total_per_class)

    print(f"DEBUG: Expected agreement (P_e): {P_e}")  # Debug statement

    # Calculate Fleiss' Kappa
    if (1 - P_e) != 0:
        kappa = (P_o - P_e) / (1 - P_e)
    else:
        kappa = 1.0  # If expected agreement is zero, return 1 (perfect agreement)

    # Ensure kappa is always a positive value
    kappa = abs(kappa)  # Use absolute value to ensure positivity

    print(f"DEBUG: Fleiss' Kappa value: {kappa}")  # Debug statement
    return kappa


def admin_kappa(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # Now guaranteed to be an instance of Admins

        # Retrieve all tasks
        tasks = Task.objects.all()
        
        task_data = []
        for task in tasks:
            # Retrieve annotated texts for each task
            annotated_texts = AnnotatedText.objects.filter(task_id=task, user__isnull=False)
            kappa_score = calculate_fleiss_kappa(annotated_texts)  # Calculate kappa score for the task
            
            # Update the task's kappa score in the database
            task.kappa_score = kappa_score
            task.save()

            task_data.append({
                'task': task,
                'kappa_score': kappa_score
            })

        return render(request, 'accounts/admin_kappa.html', {
            'username': admin.admin_username,
            'user_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name,
            'task_data': task_data  # Pass the task data to the template
        })
    
    # Redirect to login if not authenticated or not an Admins instance
    return redirect('login')

def admin_mng_datasets1(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # Now guaranteed to be an instance of Admins
        
        # Retrieve tasks associated with the admin or all tasks as needed
        tasks = Task.objects.all()  # Retrieve all tasks or filter as necessary
        
        # Retrieve all users for the dropdown
        users = Users.objects.all()  # Fetch all users; modify if needed
        
        filtered_proposed_texts = ProposedText.objects.filter(
            word_class_type__isnull=True,
            word_status="อนุมัติ"
        )
        return render(request, 'accounts/admin_mng_datasets1.html', {
            'username': admin.admin_username,
            'user_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name,
            'tasks': tasks,
            'users': users,  # Pass users to the template
            'proposed_texts': filtered_proposed_texts  # Pass tasks to the template
        })
    
    # Redirect to login if not authenticated or not an Admins instance
    return redirect('login')

def admin_add_userText(request):
    if request.user.is_authenticated and isinstance(request.user, Admins):
        admin = request.user  # Guaranteed to be an instance of Admins

        # Retrieve ProposedText entries where word_class_type is null and word_status is "อนุมัติ"
        filtered_proposed_texts = ProposedText.objects.filter(
            word_class_type__isnull=True,
            word_status="อนุมัติ"
        )

        return render(request, 'accounts/admin_add_userText.html', {
            'username': admin.admin_username,
            'user_id': admin.admin_id,
            'email': admin.admin_email,
            'tel': admin.admin_tel,
            'user_lname': admin.admin_lname,
            'user_fname': admin.admin_name,
            'proposed_texts': filtered_proposed_texts,  # Pass filtered proposed texts
        })
    # Redirect to login if not authenticated or not an Admins instance
    return redirect('login')

@login_required
def admin_add_datasets(request):
    print("User authenticated:", request.user.is_authenticated)  # Debugging
    print("User type:", type(request.user))  # Debugging

    if request.user.is_authenticated and isinstance(request.user, Admins):
        if request.method == 'POST':
            # Extract form data
            task_name = request.POST.get('task_name')
            created_date = request.POST.get('created_date')
            due_date = request.POST.get('due_date')
            annotated_texts = request.POST.get('annotated_texts')
            annotated_ids = request.POST.get('annotated_ids')

            # Parse JSON data from strings
            try:
                annotated_texts_list = json.loads(annotated_texts) if annotated_texts else []
                annotated_ids_list = json.loads(annotated_ids) if annotated_ids else []
            except json.JSONDecodeError as e:
                print("Error decoding JSON:", e)
                return JsonResponse({'success': False, 'error': 'Invalid JSON format'})

            # Verify lengths of lists match
            if len(annotated_texts_list) != len(annotated_ids_list):
                print("Mismatch between lengths of annotated_texts and annotated_ids")
                return JsonResponse({'success': False, 'error': 'Length mismatch'})

            # Generate new task and annotated texts
            try:
                task_id = generate_task_id()
                task = Task.objects.create(
                    task_id=task_id,
                    task_name=task_name,
                    created_date=created_date,
                    due_date=due_date,
                    admin=request.user,
                    kappa_score=0.0,
                    task_status=0,
                )

                # Save each annotated text entry
                for idx, annotated_text in enumerate(annotated_texts_list):
                    annotated_id = generate_unique_annotated_id()  # Ensure unique annotated_id
                    AnnotatedText.objects.create(
                        annotated_id=annotated_id,
                        annotated_text=annotated_text,
                        task_id=task,
                        annotated_class=0,
                        annotated_type="รอกำกับ",
                        text_id=None,
                    )

                return redirect('admin_mng_datasets1')

            except Exception as e:
                print("Error creating task or annotated text:", e)
                return JsonResponse({'success': False, 'error': 'Database error'})

        # For GET request, retrieve proposed texts and render the form
        filtered_proposed_texts = ProposedText.objects.filter(
            word_class_type__isnull=True,
            word_status="อนุมัติ"
        )
        return render(request, 'accounts/admin_add_datasets.html', {
            'proposed_texts': filtered_proposed_texts  # Pass the proposed texts to the template
        })

    # Redirect if user not authenticated or not an Admin
    return redirect('login')


def mainlogin(request):
    # Debugging statement to check if the user is authenticated
    print(f"User session set: {request.user.is_authenticated}")
    print("Checking authentication for user.")
    
    if request.user.is_authenticated:
        # Check if the user is an instance of Users or Admins
        if isinstance(request.user, Users):
            print(f"Authenticated user: {request.user.username}")  # Debugging line
            return render(request, 'accounts/mainlogin.html', {
                'username': request.user.username,
                'user_role': 'user'
                
            })
        elif isinstance(request.user, Admins):
            print(f"Authenticated admin: {request.user.admin_username}")  # Debugging line
            return render(request, 'accounts/mainlogin.html', {
                'username': request.user.admin_username,
                'user_role': 'admin'
            })

    print("User is not authenticated. Redirecting to login.")
    return redirect('login')
    

def annotatepage(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()  # Adjust the condition as needed

        return render(request, 'accounts/annotatepage.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count  # Pass the count of supervised texts
        })
    else:
        return redirect('login')

def userannotatehist(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()  # Adjust the condition as needed

        return render(request, 'accounts/userannotatehist.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count  # Pass the count of supervised texts
        })
    else:
        return redirect('login')

def usersannotating(request, task_id, current_index):
    if request.user.is_authenticated:
        try:
            task = Task.objects.get(pk=task_id)  # Get the task object
            
            # Fetch the annotated texts for this task and the logged-in user
            annotated_texts = AnnotatedText.objects.filter(task_id=task, user=request.user)  # Filter by user
            
            # Ensure current_index is within the bounds of annotated_texts
            current_index = int(current_index)  # Convert to int for proper indexing
            if current_index < 0 or current_index >= len(annotated_texts):
                current_index = 0  # Reset to 0 if out of bounds
            
            current_text = annotated_texts[current_index] if annotated_texts else None

            proposed_text_count = ProposedText.objects.filter(user=request.user).count()
            supervised_text_count = ProposedText.objects.filter(user=request.user, word_status='กำกับแล้ว').count()

            return render(request, 'accounts/usersannotating.html', {
                'task_id': task.task_id,
                'task_name': task.task_name,
                'assigned_users': UserTask.objects.filter(task=task),
                'proposed_text_count': proposed_text_count,
                'supervised_text_count': supervised_text_count,
                'current_text': current_text,
                'current_index': current_index + 1,  # Pass the current index + 1 to display as 1-based index
                'annotated_texts': annotated_texts  # Pass all annotated texts if needed
            })
        except Task.DoesNotExist:
            raise Http404("Task does not exist")
    else:
        return redirect('login')

def annotateselect(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()

        # Fetch tasks assigned to the current user
        user_tasks = UserTask.objects.filter(user=user)  # Assuming `user` is a ForeignKey in UserTask

        # Set a default current index
        current_index = 0  # Adjust if needed, 0 for the first item

        # Check if all annotations are completed
        all_annotations_completed = request.session.pop('all_annotations_completed', False)  # Get and remove the flag

        return render(request, 'accounts/annotateselect.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count,  # Pass the count of supervised texts
            'user_tasks': user_tasks,  # Pass the user's tasks to the template
            'current_index': current_index,  # Pass the current index to the template
            'all_annotations_completed': all_annotations_completed  # Pass the completion flag
        })
    else:
        return redirect('login')
    
@csrf_exempt
def update_annotation(request, annotated_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            annotated_class = data.get('annotated_class')
            annotated_type = data.get('annotated_type')

            # Find the annotation by id
            annotation = AnnotatedText.objects.get(annotated_id=annotated_id)

            # Update fields
            annotation.annotated_class = annotated_class
            annotation.annotated_type = annotated_type
            annotation.save()  # Save changes to the database

            return JsonResponse({"success": True, "message": "Annotation updated successfully."})
        except AnnotatedText.DoesNotExist:
            return JsonResponse({"success": False, "error": "Annotated text not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Invalid request method"})

@csrf_exempt  # Add this if you are not using CSRF tokens in AJAX requests
def update_annotated_class(request, annotated_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)  # Get the JSON data
            annotated_class = data.get('annotated_class')
            annotated_type = data.get('annotated_type')  # Get annotated_type from the data
            annotated_text = AnnotatedText.objects.get(annotated_id=annotated_id)
            
            annotated_text.annotated_class = annotated_class  # Update the class value
            annotated_text.annotated_type = annotated_type  # Update the type value
            annotated_text.save()  # Save the changes

            return JsonResponse({'success': True}, status=200)
        except AnnotatedText.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'AnnotatedText not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

def confirm_annotation(request, task_id, current_index):
    print(f"DEBUG: confirm_annotation called with task_id={task_id}, current_index={current_index}")

    if request.method == 'POST':
        # Adjusting for 1-based index by converting it to 0-based
        current_index = int(current_index) - 1  # Convert to 0-based index
        annotated_texts = AnnotatedText.objects.filter(task_id=task_id, user=request.user)  # Filter by user
        annotated_count = annotated_texts.count()
        print(f"DEBUG: Number of annotated texts found for user: {annotated_count}")

        # Ensure the current_index is valid
        if 0 <= current_index < annotated_count:
            current_text = annotated_texts[current_index]
            print(f"DEBUG: Current text to be confirmed: {current_text.annotated_text}")

            # Check if there is a next annotation
            if current_index + 1 < annotated_count:
                print("DEBUG: Proceeding to next annotation.")
                return redirect('confirm_annotation', task_id=task_id, current_index=current_index + 1)  # Increment for the next 1-based index
            else:
                print("DEBUG: Reached the end of annotations, redirecting to annotateselect.")
                return redirect('annotateselect')
        else:
            print(f"DEBUG: current_index {current_index} is out of range (0 to {annotated_count - 1}).")

    # If it's not a POST request, or if something goes wrong, redirect back to the user's annotating page
    return redirect('usersannotating', task_id=task_id, current_index=current_index)  # Convert back to 1-based index for redirection


def forgotpass(request):
    if request.method == "POST":
        email = request.POST.get('email')
        logger.debug(f'Received password reset request for email: {email}')  # Debug line
        
        associated_user = User.objects.filter(email=email).first()
        
        if associated_user:
            logger.debug(f'User found: {associated_user.username}')  # Debug line
            subject = "Password Reset Request"
            email_template = 'accounts/password_reset_email.html'
            context = {
                "email": associated_user.email,
                "domain": request.META['HTTP_HOST'],  # Domain from the current request
                "site_name": 'Your Website',
                "uid": urlsafe_base64_encode(force_bytes(associated_user.pk)),
                "user": associated_user,
                "token": default_token_generator.make_token(associated_user),
                "protocol": 'https' if request.is_secure() else 'http',
            }
            try:
                email_body = render_to_string(email_template, context)
                logger.debug(f'Email body rendered: {email_body}')  # Debug line
                send_mail(subject, email_body, settings.EMAIL_HOST_USER, [associated_user.email])
                messages.success(request, 'A password reset link has been sent to your email.')
                logger.debug('Email sent successfully')  # Debug line
            except Exception as e:
                logger.error(f'Error sending email: {str(e)}')  # Log the error
                messages.error(request, f'Error sending email: {str(e)}')  # Feedback to user
        else:
            messages.error(request, 'No user is associated with this email address.')  # Feedback if user not found
            logger.debug('No user found for the provided email address')  # Debug line

    return render(request, 'forgotpass.html')

def texttopost(request):

    if request.user.is_authenticated:
        if request.method == 'POST':
            proposed_text = request.POST.get('user_proposed_text', '').strip()  # Get input and strip whitespace
            word_class_str = request.POST.get('word_class', '0')  # Default to '0'
            word_status = request.POST.get('word_status','รออนุมัติ')
            # Validate word_class input
            word_class = int(word_class_str) if word_class_str.isdigit() else 0  # Safely convert to int

            if not proposed_text:  # Check if proposed_text is empty
                # You can add an error message or handle it as needed
                error_message = "กรุณากรอกคำที่คุณคิดว่าเป็นการบูลลี่ทางไซเบอร์"  # Example message in Thai
                return render(request, 'accounts/texttopost.html', {
                    'username': request.user.username,
                    'error_message': error_message,
                })

            text_id = generate_text_id()  # Generate the unique text_id

            bully_text = ProposedText(
                user=request.user,
                text_id=text_id,
                proposed_text=proposed_text,
                word_class=word_class,
                word_status=word_status,
            )

            try:
                bully_text.save()  # Attempt to save the proposed text
                return redirect('texttopost')
            except Exception as e:
                # Log the exception or handle it as needed
                error_message = f"An error occurred while saving: {str(e)}"
                return render(request, 'accounts/texttopost.html', {
                    'username': request.user.username,
                    'error_message': error_message,
                })

        return render(request, 'accounts/texttopost.html', {
            'username': request.user.username,
        })
    else:
        return redirect('login')

@login_required
def texttopostFile(request):
    if request.user.is_authenticated:
        if request.method == 'POST' and request.FILES.get('file'):
            upload_file = request.FILES['file']
            user = request.user._wrapped if hasattr(request.user, '_wrapped') else request.user
            
            file_name = upload_file.name
            file_type = upload_file.content_type.split('/')[-1]  
            file_size = float(upload_file.size)  
            upload_id = generate_upload_id()
            
            try:
                # Create ProposedFile instance first
                proposed_file = ProposedFile.objects.create(
                    upload_id=upload_id,
                    file_name=file_name,
                    file_type=file_type,
                    user=user,
                    file_size=file_size,
                    file_data=upload_file.read(),
                    uploaded_date=now(),
                    file_path=upload_file.name
                )

                upload_file.seek(0)  # Go back to the beginning of the file

                existing_ids = set(str(text_id) for text_id in ProposedText.objects.values_list('text_id', flat=True))
                max_count = max((int(text_id[3:]) for text_id in existing_ids if text_id.startswith("201")), default=0)

                print(f"Starting max_count: {max_count}")
                print(f"Existing IDs: {existing_ids}")

                if upload_file.name.endswith('.csv'):
                    csv_reader = csv.reader(upload_file.read().decode('utf-8').splitlines())
                    next(csv_reader)  # Skip the header
                    for row in csv_reader:
                        if len(row) < 3:  # Check if row has enough columns
                            print(f"Skipping row due to insufficient columns: {row}")
                            continue

                        word = row[0].strip()  # Ensure word is stripped of whitespace
                        word_class_value = row[1].strip()
                        word_class_type = row[2].strip()

                        if not word_class_value:  
                            print(f"Invalid word_class value: empty - skipping this row: {row}")
                            continue
                        
                        try:
                            word_class = int(word_class_value)  # Convert to integer
                        except ValueError:
                            print(f"Invalid word_class value: {word_class_value} - skipping this row: {row}")
                            continue

                        # Unique ID generation loop
                        while True:
                            max_count += 1
                            text_id = f"201{max_count:07d}"

                            # Check for uniqueness before attempting insertion
                            if text_id not in existing_ids:
                                print(f"Generated unique text_id: {text_id}")
                                break  # Exit while loop if unique
                            else:
                                print(f"Generated text_id {text_id} already exists. Regenerating...")

                        try:
                            with transaction.atomic():  # Ensure atomicity
                                # Check again for existing text_id before creating
                                if ProposedText.objects.filter(text_id=text_id).exists():
                                    print(f"Duplicate entry for text_id {text_id} found before insert - skipping this row.")
                                    continue  # Skip if it exists

                                # Create ProposedText entry
                                ProposedText.objects.create(
                                    user=user,
                                    proposed_text=word,
                                    word_class=word_class,
                                    word_status="รออนุมัติ",
                                    word_class_type=word_class_type,
                                    text_id=text_id,
                                    upload_id=proposed_file  # Make sure you're passing the instance here
                                )
                                print(f"Successfully created ProposedText with text_id: {text_id}")

                        except IntegrityError as e:
                            print(f"Error inserting text_id {text_id}: {e}")
                            continue  # Skip this entry if a duplicate text_id is found

                elif upload_file.name.endswith('.xml'):
                    xml_data = upload_file.read()
                    root = ET.fromstring(xml_data)

                    for row in root.findall('row'):
                        word_elem = row.find('ข้อความ')
                        word_class_elem = row.find('เป็นคำบูลลี่หรือไม่_ไม่เป็น_0_เป็น_1')
                        word_class_type_elem = row.find('ประเภทของคำบูลลี่')

                        # Safely get the text or use a default value if None
                        word = word_elem.text.strip() if word_elem is not None and word_elem.text else ''
                        word_class_value = word_class_elem.text.strip() if word_class_elem is not None and word_class_elem.text else ''
                        word_class_type = word_class_type_elem.text.strip() if word_class_type_elem is not None and word_class_type_elem.text else ''

                        if not word_class_value:  
                            print(f"Invalid word_class value: empty - skipping this row: {row}")
                            continue

                        try:
                            word_class = int(word_class_value)  # Convert to integer
                        except ValueError:
                            print(f"Invalid word_class value: {word_class_value} - skipping this row: {row}")
                            continue

                        # Unique ID generation loop
                        while True:
                            max_count += 1
                            text_id = f"201{max_count:07d}"

                            # Check for uniqueness before attempting insertion
                            if text_id not in existing_ids:
                                print(f"Generated unique text_id: {text_id}")
                                break  # Exit while loop if unique
                            else:
                                print(f"Generated text_id {text_id} already exists. Regenerating...")

                        try:
                            with transaction.atomic():  # Ensure atomicity
                                # Check again for existing text_id before creating
                                if ProposedText.objects.filter(text_id=text_id).exists():
                                    print(f"Duplicate entry for text_id {text_id} found before insert - skipping this row.")
                                    continue  # Skip if it exists

                                # Create ProposedText entry
                                ProposedText.objects.create(
                                    user=user,
                                    proposed_text=word,
                                    word_class=word_class,
                                    word_status="รออนุมัติ",
                                    word_class_type=word_class_type,
                                    text_id=text_id,
                                    upload_id=proposed_file  # Make sure you're passing the instance here
                                )
                                print(f"Successfully created ProposedText with text_id: {text_id}")

                        except IntegrityError as e:
                            print(f"Error inserting text_id {text_id}: {e}")
                            continue  # Skip this entry if a duplicate text_id is found

                return redirect("texttopostFile")
                
            except Exception as e:
                print(f"Error while creating ProposedText or ProposedFile: {e}")

        return render(request, 'accounts/texttopostFile.html', {
            'username': request.user.username,
        })

    return render(request, 'accounts/texttopostFile.html', {
        'username': request.user.username,
    })

def txtverify(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()  # Adjust the condition as needed

        return render(request, 'accounts/txtverify.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count  # Pass the count of supervised texts
        })
    else:
        return redirect('login')

def txtverifyFile(request):
    if request.user.is_authenticated:
        user = request.user

        # Count the texts where the current user has proposed
        proposed_text_count = ProposedText.objects.filter(user=user).count()

        # Count texts that the user supervised (assuming some field tracks this, like word_status)
        supervised_text_count = ProposedText.objects.filter(user=user, word_status='กำกับแล้ว').count()  # Adjust the condition as needed

        return render(request, 'accounts/txtverifyFile.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_text_count': proposed_text_count,  # Pass the count of proposed texts
            'supervised_text_count': supervised_text_count  # Pass the count of supervised texts
        })
    else:
        return redirect('login')

def registration(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        confirm_email = request.POST.get('confirm-email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        tel = request.POST.get('telephone-number')

        # Check if the passwords match
        if password != confirm_password:
            return render(request, 'registration.html', {
                'error_message': "รหัสผ่านไม่ตรงกัน",
                'success_message': None
            })

        # Check if the emails match
        if email != confirm_email:
            return render(request, 'registration.html', {
                'error_message': "อีเมลไม่ตรงกัน",
                'success_message': None
            })

        # Check if username, email, or telephone number already exists
        if user_map.objects.filter(username=username).exists():
            return render(request, 'registration.html', {
                'error_message': "ชื่อผู้ใช้นี้มีอยู่แล้ว",
                'success_message': None
            })

        if user_map.objects.filter(email=email).exists():
            return render(request, 'registration.html', {
                'error_message': "อีเมลนี้มีอยู่แล้ว",
                'success_message': None
            })

        if user_map.objects.filter(tel=tel).exists():
            return render(request, 'registration.html', {
                'error_message': "หมายเลขโทรศัพท์นี้มีอยู่แล้ว",
                'success_message': None
            })

        user_id = generate_user_id()  # Replace with your user ID generation logic

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create a new user entry using the 'create' method
        user_map.objects.create(
            user_id=user_id,
            username=username,
            email=email,
            password=hashed_password.decode('utf-8'),
            tel=tel,
            user_role="user"
        )
        
        return render(request, 'registration.html', {
            'error_message': None,
            'success_message': "สมัครสมาชิกเรียบร้อยแล้ว"
        })

    return render(request, 'registration.html', {
        'error_message': None,
        'success_message': None
    })

def user_propose_history(request):
    if request.user.is_authenticated and isinstance(request.user, Users):
        user = request.user

        # Fetch proposed texts and related user information
        proposed_texts = ProposedText.objects.filter(user=user).select_related('user').order_by('text_id')

        return render(request, 'accounts/user_propose_history.html', {
            'username': user.username,
            'user_id': user.user_id,
            'email': user.email,
            'tel': user.tel,
            'user_lname': user.user_lname,
            'user_fname': user.user_fname,
            'proposed_texts': proposed_texts,
        })

    return redirect('login')

def generate_user_id():
    while True:
        new_id = '164' + str(random.randint(1000000, 9999999))  # Generate a random ID with '164' prefix
        if not user_map.objects.filter(user_id=new_id).exists():  # Check if it exists
            return new_id

def generate_text_id():
    count = ProposedText.objects.count() + 1  # Start counting from 1
    text_id = f"201{count:07d}"  # Generate ID in the format 2010000001, etc.
    return text_id

def generate_upload_id() -> str:
    # Get the current year
    current_year = now().year
    year_prefix = str(current_year)[-4:]  # Get the last four digits of the year
    
    # Get the last upload number for the current year
    last_upload = ProposedFile.objects.filter(upload_id__startswith=year_prefix).order_by('-upload_id').first()
    
    if last_upload:
        # Extract the last five digits and increment
        last_number = int(last_upload.upload_id[-5:]) + 1
    else:
        last_number = 1  # Start from 1 if no uploads found
    
    # Format the new upload ID, ensuring it has 5 digits
    upload_id = f"{year_prefix}{last_number:05d}"  # Pad with zeros to ensure 5 digits
    
    # Optional: Add a limit to the last_number to prevent overflow
    if last_number > 99999:
        raise ValueError("Exceeded maximum upload ID limit for the year.")
        
    return upload_id

def generate_unique_annotated_id():
    while True:
        annotated_id = random.randint(1000000, 9999999)  # Generate a 7-digit number
        if not AnnotatedText.objects.filter(annotated_id=annotated_id).exists():  # Ensure uniqueness
            return annotated_id

def generate_task_id():
    while True:
        # Generate a random 6-digit number
        task_id = str(random.randint(100000, 999999))
        
        # Check if the generated task_id already exists in the database
        if not Task.objects.filter(task_id=task_id).exists():
            return task_id  # Return the unique task_id


def generate_user_task_id():
    while True:
        # Generate a random 6-digit number
        user_task_id = str(random.randint(100000, 999999))
        # Check if it already exists in the UserTask table
        if not UserTask.objects.filter(user_task_id=user_task_id).exists():
            return user_task_id