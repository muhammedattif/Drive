from django.shortcuts import render

# Error view
def error(request):
    return render(request, 'error.html')