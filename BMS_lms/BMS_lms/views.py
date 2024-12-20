from lib2to3.fixes.fix_input import context
import math
from django.contrib.admin import action
from django.http import JsonResponse
from django.shortcuts import redirect,render
from django.template.context_processors import request
from app.models import Categories,Course,Level,Video,UserCourse,Payment
from django.views.decorators.csrf import csrf_exempt
from unicodedata import category
from django.template.loader import render_to_string
from django.db.models import Sum
from django.contrib import messages
import razorpay
from  time import time
from .settings import *

client = razorpay.Client(auth=(KEY_ID,KEY_SECERET))



def BASE(request):
    return render(request,'base.html')


def HOME(request):
    category =Categories.objects.all().order_by('id')[0:5]
    course = Course.objects.filter(status = 'PUBLISH').order_by('-id')

    context = {
        'category' : category,
        'course' : course,
    }
    return render(request,'Main/home.html', context)


def SINGLE_COURSE(request):
    category = Categories.get_all_category(Categories)
    level = Level.objects.all()
    course = Course.objects.all()
    FreeCourse_count = Course.objects.filter(price=0).count()
    PaidCourse_count = Course.objects.filter(price__gte=1).count()
    context= {
        'category' : category,
        'level' : level,
        'course' : course,
        'FreeCourse_count' : FreeCourse_count,
        'PaidCourse_count' : PaidCourse_count,
    }
    return render(request,'Main/single_course.html',context)

def filter_data(request):
    category = request.GET.getlist('category[]')
    level = request.GET.getlist('level[]')
    price = request.GET.getlist('price[]')


    if price == ['PriceFree']:
        course = Course.objects.filter(price=0)
    elif price == ['PricePaid']:
        course = Course.objects.filter(price__gte=1)
    elif price == ['PriceAll']:
        course = Course.objects.all()
    elif category:
        course = Course.objects.filter(category__id__in = category).order_by('-id')
    elif level:
        course = Course.objects.filter(level__id__in = level).order_by('-id')
    else:
        course = Course.objects.all().order_by('-id')

    context = {
        'course' : course
    }
    t = render_to_string('ajax/course.html', context)
    return JsonResponse({'data' : t})


def CONTACT_US(request):
    category = Categories.get_all_category(Categories)

    context = {
        'category' : category,
    }
    return render(request,'Main/contact_us.html',context)


def ABOUT_US(request):
    category = Categories.get_all_category(Categories)

    context = {
        'category': category,
    }
    return render(request,'Main/about_us.html',context)


def SEARCH_COURSE(request):
    category = Categories.get_all_category(Categories)

    query = request.GET['query']
    course = Course.objects.filter(title__icontains = query )

    context = {
        'course' : course,
        'category': category,
    }
    return render(request,'search/search.html', context)


def COURSE_DETAILS(request, slug):
    category = Categories.get_all_category(Categories)
    time_duration = Video.objects.filter(course__slug = slug).aggregate(sum=Sum('time_duration'))
    course_id = Course.objects.get(slug=slug)

    try:
        check_enroll = UserCourse.objects.get(user=request.user,course = course_id)
    except UserCourse.DoesNotExist:
        check_enroll = None

    course = Course.objects.filter(slug = slug)
    if course.exists():
        course = course.first()
    else:
        return redirect('404')

    context = {
        'course' : course,
        'category': category,
        'time_duration' : time_duration,
        'check_enroll' : check_enroll,
    }
    return render(request,'course/course_details.html',context)


def PAGE_NOT_FOUND(request):
    category = Categories.get_all_category(Categories)

    context = {
        'category': category,
    }
    return render(request,'error/404.html',context)


def CHECKOUT(request,slug):
    course = Course.objects.get(slug = slug)
    action = request.GET.get('action')
    order = None


    if course.price == 0:
        course = UserCourse(
            user = request.user,
            course = course,
        )
        course.save()
        messages.success(request,'Enrolled Course Sucessfully!!!')
        return redirect('my_course')
    elif action == 'create_payment':
        if request.method == "POST":
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')

            amountd = (course.price - (course.price * course.discount / 100) )
            amount = (math.floor(amountd) * 100 )
            currency = "INR"
            notes = {
                "name" : f' {first_name}  {last_name}',
                "email" : email,
            }
            receipt = f"BMS-EL-{int(time())}"
            order = client.order.create(
                {
                    'receipt' : receipt,
                    'notes' : notes,
                    'amount' : amount,
                    'currency' : currency,
                }
            )

            payment = Payment(
                course = course,
                user = request.user,
                order_id = order.get('id')
            )
            payment.save()


    context = {
        'course' : course,
        'order' : order,
    }

    return render(request,'checkout/checkout.html',context)


def MY_COURSE(request):
    course = UserCourse.objects.filter(user = request.user)
    category = Categories.get_all_category(Categories)

    context = {
        'course' : course,
        'category': category,
    }
    return render(request,'course/my-course.html',context)


@csrf_exempt
def VERIFY_PAYMENT(request):
    if request.method == "POST":
        data = request.POST

        try:
            # Verifying the payment signature
            client.utility.verify_payment_signature(data)

            # Fetching required fields
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')  # corrected variable

            # Fetching the payment instance
            payment = Payment.objects.get(order_id=razorpay_order_id)
            payment.payment_id = razorpay_payment_id
            payment.status = True

            # Saving user course details
            usercourse = UserCourse(
                user=payment.user,
                course=payment.course,
            )
            usercourse.save()
            payment.user_course = usercourse
            payment.save()

            # Redirect to 'my_course' without context (use session, query params if needed)
            return redirect('my_course')

        except Payment.DoesNotExist:
            return render(request, 'verify_payments/fail.html', {'error': 'Payment not found.'})
        except Exception as e:
            return render(request, 'verify_payments/fail.html', {'error': str(e)})


def WATCH_COURSE(request,slug):
    course = Course.objects.filter(slug = slug)
    lecture = request.GET.get('lecture')
    video = Video.objects.get(id = lecture)

    if course.exists():
        course = course.first()
    else:
        return redirect('404')

    context = {
        'course' : course,
        'video' :video,
        'lecture' : lecture,
    }
    return render(request,'course/watch-course.html',context)

































# @csrf_exempt
# def VERIFY_PAYMENT(request):
#     if request.method == "POST":
#         data = request.POST
#
#         try:
#             client.utility.verify_payment_signature(data)
#             razorpay_order_id = data['razorpay_order_id']
#             razorpay_payment_id = data['razor_payment_id']
#
#             payment = Payment.objects.get(order_id = razorpay_order_id)
#             payment.payment_id = razorpay_payment_id
#             payment.status = True
#
#             usercourse = UserCourse(
#                 user = payment.user,
#                 course = payment.course,
#             )
#             usercourse.save()
#             payment.user_course = usercourse
#             payment.save()
#
#             context = {
#                 'data' : data,
#                 'payment' : payment,
#             }
#             return redirect('my_course',context)
#         except:
#             return render(request,'verify_payments/fail.html' )
