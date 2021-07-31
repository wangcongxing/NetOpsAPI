from django.db import transaction
from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework import viewsets, serializers, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from app import models, modelFilters, modelSerializers, modelPermission
from utils import APIResponseResult
from utils.CustomViewBase import CustomViewBase
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from rest_framework.views import APIView
import os, uuid, time
from rest_framework_jwt.settings import api_settings
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from textfsm import TextFSM
from netmiko import ConnectHandler
import json
from datetime import datetime, timedelta
from django.db import transaction
from rest_framework import generics, mixins, views, viewsets
from django_filters import rest_framework as filters
import ast
import site
import shutil
from nornir.core.task import Result
from nornir import InitNornir
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir.core.task import Result
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command
from utils.cmdb_inventory_v2 import CMDBInventory
import os
from tempfile import TemporaryFile
from io import BytesIO
from urllib.parse import quote
import ast
import django_excel as excel
import xlwt, openpyxl
from django.http import HttpResponse
from netmiko import ConnectHandler
from django.db.models import Q
from time import strftime, localtime
from netmiko import SSHDetect, Netmiko
from getpass import getpass
import ast
from utils import rsaEncrypt, NetCommand
from concurrent.futures import ThreadPoolExecutor
import requests

# 密码加解密
rsaUtil = rsaEncrypt.RsaUtil()
# Nornir 执行对象
netCommand = NetCommand.netCommandInfo()

ENV_PROFILE = os.getenv("ENV")
if ENV_PROFILE == "pro":
    from NetOpsAPI import pro_settings as config
elif ENV_PROFILE == "test":
    from NetOpsAPI import test_settings as config
else:
    from NetOpsAPI import settings as config

NTC_TEMPLATES_DIR = config.initConfig["NTC_TEMPLATES_DIR"]


# Create your views here.
# 获取当前netmiko支持的设备类型
def getDeviceType():
    jsonResult = []
    try:
        dev_info = {
            "device_type": "none",
            "ip": "127.0.0.1",
            "username": "",
            "password": "",
            "port": 22
        }
        with ConnectHandler(**dev_info) as conn:
            output = conn.send_command("display version")  # display lldp neighbor verbose
            print(output)
    except Exception as e:
        cliText = e.args[0]
        f = open(os.path.join(NTC_TEMPLATES_DIR, "get_device_types.textfsm"))
        template = TextFSM(f)
        jsonResult = template.ParseText(cliText)
    return jsonResult


# 默认数据初始化
class InitInfo(APIView):
    authentication_classes = ()
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        # 新建超级用户
        superUser, ctime = User.objects.update_or_create(
            defaults={'username': 'admin', 'is_staff': True, 'is_active': True, 'is_superuser': True,
                      'first_name': '管理员',
                      'password': make_password("admin@123")}, username='admin')
        superUser = superUser.username
        jsonResult = getDeviceType()
        for item in jsonResult:
            d, c = models.deviceTypes.objects.update_or_create(
                defaults={"deviceKey": item[0], "deviceValue": item[0],
                          'creator': superUser, 'editor': superUser},
                deviceKey=item[0])
        # 从venv ntc_templates复制模版文件到 项目目录 textfsm_templates
        textfsm_ntc_templates = site.getsitepackages()[0] + "/textfsm_templates/templates"
        if os.path.exists(textfsm_ntc_templates):
            for tfile in os.listdir(textfsm_ntc_templates):
                shutil.copyfile(textfsm_ntc_templates + "/" + tfile, os.path.join(NTC_TEMPLATES_DIR, tfile))
        return HttpResponse("<h1>NetOpsOpenApi 数据库初始化成功</h1>")


# 设备类型管理
class deviceTypesViewSet(CustomViewBase):
    queryset = models.deviceTypes.objects.all().order_by('-id')
    serializer_class = modelSerializers.deviceTypesSerializer
    filter_class = modelFilters.deviceTypesFilter
    ordering_fields = ('-deviceState',)  # 排序
    permission_classes = [modelPermission.deviceTypesPermission]
    # 指定默认的排序字段
    ordering = ('-deviceState',)

    # 修改状态
    @action(methods=['put'], detail=False, url_path='resetEnabled')
    def resetEnabled(self, request, *args, **kwargs):
        nid = request.data.get('nid', None)
        if nid is None:
            return APIResponseResult.APIResponse(-1, '请求发生错误,请稍后再试!')
        deviceType = models.deviceTypes.objects.filter(id=nid).first()
        if deviceType is None:
            return APIResponseResult.APIResponse(-2, '请求数据不存在,请稍后再试!')
        deviceType.deviceState = 0 if int(deviceType.deviceState) else 1
        deviceType.save()
        return APIResponseResult.APIResponse(0, "已启用" if deviceType.deviceState else "已禁用")


# 登录用户管理
class loginUserInfoViewSet(CustomViewBase):
    queryset = models.loginUserInfo.objects.all().order_by('-id')
    serializer_class = modelSerializers.loginUserInfoSerializer
    filter_class = modelFilters.loginUserInfoFilter
    permission_classes = [modelPermission.loginUserInfoPermission]


# 网络服务API管理

class GetAccessToken(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        # username可能携带的不止是用户名，可能还是用户的其它唯一标识 手机号 邮箱
        print(request.GET)
        appid = request.data.get('appid', None)
        appsecret = request.data.get('appsecret', None)
        if appid is None or appsecret is None:
            return APIResponseResult.APIResponse(-1, 'appid或密钥不能为空!')

        token = ""
        return APIResponseResult.APIResponse(0, 'ok', results={
            'expires_in': 3600,
            'access_token': token
        })


class networkOpenAPIViewSet(CustomViewBase):
    queryset = models.networkOpenAPI.objects.all().order_by('-id')
    serializer_class = modelSerializers.networkOpenAPISerializer
    filter_class = modelFilters.networkOpenAPIFilter
    ordering_fields = ('id',)  # 排序

    permission_classes = [modelPermission.networkOpenAPIPermission]

    # 修改状态
    @action(methods=['put'], detail=False, url_path='resetEnabled')
    def resetEnabled(self, request, *args, **kwargs):
        nid = request.data.get('nid', None)
        if nid is None:
            return APIResponseResult.APIResponse(-1, '请求发生错误,请稍后再试!')
        netTask = models.networkOpenAPI.objects.filter(id=nid).first()
        if netTask is None:
            return APIResponseResult.APIResponse(-2, '请求数据不存在,请稍后再试!')
        netTask.enabled = False if netTask.enabled else True
        netTask.save()
        return APIResponseResult.APIResponse(0, "已启用" if netTask.enabled else "已禁用")

    # 日常维护
    @action(methods=['get'], detail=False, url_path='run')
    def run(self, request, *args, **kwargs):
        # 如果nid不为None 则重新执行
        nid = request.GET.get("nid", None)
        if nid is None:
            netmaintainIpLists = models.networkOpenAPIList.objects.filter(taskStatus=0).order_by("createTime")[0:3]
        else:
            netmaintainIpLists = models.networkOpenAPIList.objects.filter(netmaintain__startTime__lte=strftime(
                '%Y-%m-%d %H:%M:%S', localtime()),
                netmaintain__enabled=True,
                id=int(nid)).order_by('-lastTime', )

        runInfo = []
        runInfo.append({"start": strftime('%Y-%m-%d %H:%M:%S', localtime())})
        devs = []

        runInfo.append({"end": strftime('%Y-%m-%d %H:%M:%S', localtime())})
        return APIResponseResult.APIResponse(0, "开始运行执行中...", runInfo)


# 接口场景列表
class networkOpenTempViewSet(CustomViewBase):
    queryset = models.networkOpenTemp.objects.all().order_by('-useCount', '-id', )
    serializer_class = modelSerializers.networkOpenTempSerializer
    filter_class = modelFilters.networkOpenTempFilter
    ordering_fields = ['useCount', '-id', ]  # 排序
    permission_classes = [modelPermission.networkOpenTempPermission]


class networkOpenAPIListViewSet(CustomViewBase):
    queryset = models.networkOpenAPIList.objects.all().order_by('-id', )
    serializer_class = modelSerializers.networkOpenAPIListSerializer
    filter_class = modelFilters.networkOpenAPIListFilter
    ordering_fields = ['startTime', '-id', ]  # 排序
    permission_classes = [modelPermission.networkOpenAPIListPermission]
