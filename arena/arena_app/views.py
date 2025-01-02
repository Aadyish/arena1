from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.models import User,auth
from django.contrib import messages
import stripe.error
from .models import Quiz, Sessions, Booking
from django.db.models import Q, F
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.encoding import smart_str
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from stripe import Webhook
from stripe.error import SignatureVerificationError
import logging
import re

stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)
# Create your views here.

def quiz(request):
    phone_pattern = r"^(\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}$"
    name_pattern = "^[A-Za-zÀ-ÖØ-öø-ÿ\s\-']+$"
    
    if request.method == 'POST':
        name = request.POST['fullname']
        dob = request.POST['dob']
        phone_number = request.POST['phone_number']
        gender = request.POST['gender']
        location = request.POST['location']
       
        fav_sport_list = request.POST.getlist('fav_sport')  
        fav_sport = ", ".join(set(fav_sport_list))
        
        # print(name, dob, phone_number, gender, location, fav_sport)
        
        if not all([name, dob, phone_number, gender, location, fav_sport]):
            messages.info(request, 'All fields are required.')
            return redirect('quiz')
        
        elif not re.match(name_pattern,name):
            messages.info(request, 'NAME IS INVALID')
            return redirect('quiz')
        
        elif not re.match(phone_pattern,phone_number):
            messages.info(request, 'PHONE NUMBER IS INVALID')
            return redirect('quiz')
        
        else:
            Quiz.objects.create(
            name=name,
            dob=dob,
            phone_number=phone_number,
            gender=gender,
            location=location,
            fav_sport=fav_sport
        )
        messages.success(request, 'Quiz submitted successfully!')
        print(fav_sport)
        return redirect(f'/home?location={location}&fav_sport={fav_sport}')
        
    return  render(request, 'quiz.html')

def home(request):
    
    sessions = Sessions.objects.all()
    
    # Get query parameters for filtering
    location = request.GET.get('location', '').strip()
    fav_sport = request.GET.get('fav_sport', '').strip()
    
    # Apply filtering if location and fav_sport are provided
    if location and location.lower() != "no location":
        sessions = sessions.filter(location=location)
    if fav_sport and fav_sport.lower() != "no sport":
        #sessions = sessions.filter(sport_type=fav_sport)
        fav_sport_list = fav_sport.split(', ')
        # print(f"Filtered sports list: {fav_sport_list}")
        sessions = sessions.filter(sport_type__in=fav_sport_list)
    
    
    if request.method == 'POST':
        sessions = Sessions.objects.all()
        mindate = request.POST['mindate']
        maxdate = request.POST['maxdate']
        location = request.POST['location']
        fav_sport = request.POST['fav_sport']
        
        print(mindate, maxdate, location, fav_sport)
        
        if mindate and maxdate:
            sessions = sessions.filter(time__date__range=[mindate, maxdate])  # Filter between mindate and maxdate
        elif mindate:
            sessions = sessions.filter(time__date__gte=mindate)  # Filter sessions with date >= mindate
        elif maxdate:
            sessions = sessions.filter(time__date__lte=maxdate)  # Filter sessions with date <= maxdate

        if location != "no location":
            sessions = sessions.filter(location=location)  # Filter by exact match for location

        if fav_sport != "no sport":
            sessions = sessions.filter(sport_type=fav_sport)  # Filter by exact match for sport type
    
    sessions = sessions.filter(slots_taken__lt=F('game_size'))  
    locations = Sessions.objects.values_list('location', flat=True).distinct()
    sports = Sessions.objects.values_list('sport_type', flat=True).distinct()

    return render(request, 'home.html', {
        'sessions': sessions,
        'locations': locations,
        'sports': sports,
    })


def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = auth.authenticate(username=username, password=password) 
        
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')
    else:
        return render(request, 'login.html')
   
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already used')
                return redirect('register')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'username already used ')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                return redirect('login')
        else:
            messages.info(request, 'password not the same')
            return redirect('register')
    else:
        return render(request, 'register.html')
    
def profile(request):
    sessions = Sessions.objects.all()
    bookings = Booking.objects.all()
    
    # sessions = sessions.filter(id = Booking.sessionid)
    #sessions = sessions.filter(id__in=bookings.values_list('sessionid', flat=True))
    #print("Sessions found: ", sessions)
    user = request.user
    
    # Filter bookings by the logged-in user
    bookings = Booking.objects.filter(userid=user)
    
    # Fetch sessions related to the current user's bookings
    sessions = Sessions.objects.filter(id__in=bookings.values_list('sessionid', flat=True))
    
    return render(request, 'profile.html', {'sessions': sessions})
    
def logout(request):
    auth.logout(request)
    return redirect('home')

@login_required
def create_checkout_session(request, session_id):
    print("checkout created")
    session = get_object_or_404(Sessions, pk=session_id)
    
    price_in_cents = int(session.price * 100)
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "gbp",
                "unit_amount": price_in_cents,
                "product_data": {
                    "name": session.sport_type
                },
            },
            "quantity": 1
        }],
        mode="payment",
        success_url= request.build_absolute_uri(reverse("session_success")),
        cancel_url=  request.build_absolute_uri(reverse("session_cancel")),
        metadata={"sessions_id": session_id, "user_id": request.user.id}
    )
    
    return redirect(checkout_session.url)

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body.decode("utf-8")
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    print(f"Signature header: {sig_header}")
    try:
        # Verify the webhook signature
        event = Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except SignatureVerificationError:
        logger.error("Invalid signature")
        return JsonResponse({"error": "Invalid signature"}, status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        handle_checkout_session(session)
    return JsonResponse({"status": "success"})

def handle_checkout_session(session):
    try:
        sessions_id = session["metadata"].get("sessions_id")
        user_id = session["metadata"].get("user_id")

        if not sessions_id or not user_id:
            logger.error("Missing metadata: sessions_id or user_id")
            return

        user = User.objects.get(id=user_id)
        session_instance = get_object_or_404(Sessions, id=sessions_id)
        
        session_instance.slots_taken += 1
        session_instance.save()

        Booking.objects.create(userid=user, sessionid=session_instance)
        logger.info("Booking successful for user %s and session %s", user_id, sessions_id)
    except User.DoesNotExist:
        logger.error("User with ID %s does not exist", user_id)
    except Sessions.DoesNotExist:
        logger.error("Session with ID %s does not exist", sessions_id)
    except Exception as e:
        logger.error("Error during booking creation: %s", str(e))

@login_required
def session_success(request):
    return render(request, 'success.html')
@login_required
def session_cancel(request):
    return redirect("home")
