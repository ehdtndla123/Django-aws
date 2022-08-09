from django.shortcuts import render
from django.utils import timezone

from order.models import Shop,Menu,Order,OrderFood
from django.http import HttpResponse,JsonResponse
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt
from order.serializers import ShopSerializer
from order.serializers import MenuSerializer

@csrf_exempt
def order_list(request,shop):
    if request.method=='GET':
        order_list=Order.objects.filter(shop=shop)
        return render(request,'boss/order_list.html',{'order_list':order_list})
    else:
        return HttpResponse(status=404)

@csrf_exempt
def time_input(request):
    if request.method=="POST":
        order_item=Order.objects.get(pk=int(request.POST['order_id']))
        order_item.estimated_time=int(request.POST['estimatedtime'])
        order_item.save()
        shop=order_item.shop.id
        return render(request,'boss/success.html',{'shop':int(shop)})
    else:
        return HttpResponse(status=404)