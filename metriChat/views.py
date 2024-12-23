from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def success_response(request):
    return render(request, 'success.html')

@csrf_exempt
def failure_response(request):
    return render(request, 'failure.html')
