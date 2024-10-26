from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login
from django.db import connection
from django.contrib.auth import login as auth_login
from django.contrib import messages
from io import TextIOWrapper
from .models import user_map, Users, ProposedText, ProposedFile,Admins
import bcrypt  # Import bcrypt for password hashing
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
import xml.etree.ElementTree as ET
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import get_user
from django.db import models
import random
from django.contrib.auth.backends import BaseBackend



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


from django.contrib.auth import authenticate, login as auth_login
from .models import Users, Admins

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
            })
        elif isinstance(request.user, Admins):
            print(f"Authenticated admin: {request.user.admin_username}")  # Debugging line
            return render(request, 'accounts/mainlogin.html', {
                'username': request.user.admin_username,
            })
    
    print("User is not authenticated. Redirecting to login.")  # Debugging line
    return redirect('login')  # Redirect to login page if not authenticated

def annotatepage(request):
    return render(request, 'annotatepage.html')

def annotateselect(request):
    return render(request, 'annotateselect.html')
def forgotpass(request):
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
    return render(request, 'txtverify.html')
def txtverifyFile(request):
    return render(request, 'txtverifyFile.html')

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

