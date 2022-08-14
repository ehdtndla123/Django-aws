from django.shortcuts import render
from user.models import User
from user.serializers import UserSerializer

from django.utils import timezone
from django.http import JsonResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def user(request):
    if request.method=='GET':
        # shop=Shop.objects.all()
        # serializer=ShopSerializer(shop,many=True)
        # return JsonResponse(serializer.data,safe=False)
        user=User.objects.all()
        return render(request,'user/user_list.html',{'user_list':user})
    elif request.method=='POST':
        data=JSONParser().parse(request)
        serializer=UserSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data,status=201)
        return JsonResponse(serializer.errors,status=400)

@csrf_exempt
def login(request):
    if request.method=="POST":
        name=request.POST['name']
        try:
            request.session['user_id']=User.objects.all().get(name=name).id
            return render(request,'user/success.html')
        except:
            return render(request,'user/fail.html')
    elif request.method=='GET':
        return render(request,'user/login.html')