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
from django_celery_beat.models import PeriodicTask, IntervalSchedule
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
from utils import rsaEncrypt
from concurrent.futures import ThreadPoolExecutor
import requests

# 密码加解密
rsaUtil = rsaEncrypt.RsaUtil()

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

        # 新建调度任务
        # 调度任务
        # 创建10秒的间隔 interval 对象
        schedule, created = IntervalSchedule.objects.update_or_create(
            defaults={'every': 10, 'period': IntervalSchedule.SECONDS}, id=1)
        # 无参函数定时任务
        PeriodicTask.objects.update_or_create(defaults={'interval': schedule, 'name': '无参函数定时任务',
                                                        'task': 'celery_tasks.tasks.updateTaskState',
                                                        # 'expires': (datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                                                        }, name='无参函数定时任务')
        # 创建带参数的任务
        PeriodicTask.objects.update_or_create(defaults={'interval': schedule, 'name': '有参函数定时任务',
                                                        'task': 'celery_tasks.tasks.my_task1',
                                                        'args': json.dumps([10, 20, 30]),
                                                        # 'expires': (datetime.now()+timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                                                        }, name='有参函数定时任务')

        # 创建系统自带模版
        # 根据设备类型key
        # 场景市场

        return HttpResponse("<h1>NetOpsOpenApi 数据库初始化成功</h1>")


class TokenJWTAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request, *args, **kwargs):
        # username可能携带的不止是用户名，可能还是用户的其它唯一标识 手机号 邮箱
        print(request.GET)
        username = request.data.get('username', None)
        password = request.data.get('password', None)
        if username is None or password is None:
            return APIResponseResult.APIResponse(-1, '用户名或密码不能为空!')
        user = User.objects.filter(username=username).first()
        if user is None:
            return APIResponseResult.APIResponse(-2, '用户名或密码输入有误')
        # 获得用户后，校验密码并签发token
        if not user.check_password(password):
            return APIResponseResult.APIResponse(-3, '密码错误')
        # 更新最后一次登录时间
        user.last_login = datetime.now()
        user.save()
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        return APIResponseResult.APIResponse(0, 'ok', results={
            'username': user.username,
            'access_token': token
        })


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


class networkOpenAPIViewSet(CustomViewBase):
    queryset = models.networkOpenAPI.objects.all().order_by('-id')
    serializer_class = modelSerializers.networkOpenAPISerializer
    filter_class = modelFilters.networkOpenAPIFilter
    ordering_fields = ('id',)  # 排序

    permission_classes = [modelPermission.networkOpenAPIPermission]

    # 禁用/启用
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


# 场景超市
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


def Write_Send_Command(nid):
    print("nid=", nid)
    try:
        item = models.networkOpenAPIList.objects.get(id=int(nid))
        password = rsaUtil.decrypt_by_private_key(item.password)
        taskTemp = item.networkopentemp
        dev_info = {
            "device_type": taskTemp.deviceType.deviceKey,
            "ip": item.ip,
            "username": item.username,
            "password": password,
            "conn_timeout": 20,
            "port": item.port,
        }
        cmds = taskTemp.cmds
        nid = item.id
        networkopenapilistkwargs = models.networkOpenAPIListKwargs.objects.filter(networkopenapilist=item)
        for cmdInfo in networkopenapilistkwargs:
            cmds = str(cmds).replace(cmdInfo.key, cmdInfo.value)
        cmds = str(cmds).replace("\n", ",").replace(";", ",").split(",")  # 根据回撤逗号分割
        print("cmds=", cmds)
        resultText = []
        cmdInfo = []
        with ConnectHandler(**dev_info) as conn:
            print("已经成功登陆交换机" + dev_info['ip'])
            print("nid=", nid)
            for cmd in cmds:
                result = conn.send_command_timing(str(cmd).strip())
                resultText.append(
                    {"time": strftime('%Y-%m-%d %H:%M:%S', localtime()),
                     "cmd": "<{}>{}".format(conn.base_prompt, cmd),
                     "result": "<{}>{}".format(conn.base_prompt, result)})
                cmdInfo.append(
                    "<{}>{}".format(conn.base_prompt, cmd) + "\n" + "<{}>{}".format(conn.base_prompt, result))
            conn.disconnect()

            item.exceptionInfo = ""
            item.cmdInfo = "\n".join(cmdInfo)
            item.jsonResult = ast.literal_eval(item.jsonResult) + resultText
            item.taskStatus = 2

    except Exception as e:
        item.taskStatus = -1
        item.exceptionInfo = e.args
    finally:
        item.save()


class useInfoAPIViewSet(CustomViewBase):
    queryset = models.useInfoAPI.objects.all().order_by('-id', )
    serializer_class = modelSerializers.useInfoAPISerializer
    filter_class = modelFilters.useInfoAPItFilter
    ordering_fields = ['-id', ]  # 排序
    permission_classes = [modelPermission.useInfoAPIPermission]

    # 提交任务 Async
    @action(methods=['get', 'post'], detail=False, url_path='postTask')
    def postTask(self, request, *args, **kwargs):
        # 任务类型 0 异步方法 1同步方法
        taskState = int(request.data.get("taskState", 0))
        # 应用appid
        appid = request.data.get("appid", "")
        # 应用密钥
        appsecret = request.data.get("appsecret", "")
        # 登录设备用户名
        username = request.data.get("username", "")
        # 登录设备密码
        password = str(rsaUtil.encrypt_by_public_key(request.data.get("password", "")), 'utf-8')
        # 登录设备端口
        port = request.data.get("port", 22)
        # 模版编号
        tempnumber = request.data.get("tempnumber", "")
        # 扩展参数
        listkwargs = request.data.get("listkwargs", [])
        startTime = request.data.get("startTime", strftime('%Y-%m-%d %H:%M:%S', localtime()))
        # 获得客户端请求IP
        ip = ""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]  # 所以这里是真实的ip
        else:
            ip = request.META.get('REMOTE_ADDR')  # 这里获得代理ip
        if appid == "" or appsecret == "" or username == "" or password == "" or listkwargs is [] or tempnumber == "":
            return APIResponseResult.APIResponse(-1,
                                                 "appid={},appsecret={},username={},password={},tempnumber={},listIp={},输入有误".format(
                                                     appid, appsecret, username, password, tempnumber, listkwargs))
        networkopenapi = models.networkOpenAPI.objects.filter(appid=appid, appsecret=appsecret, enabled=False).first()
        if networkopenapi is None:
            return APIResponseResult.APIResponse(-2, "appid={},appsecret={}输入有误请检查".format(appid, appsecret))
        if int(networkopenapi.approveState) != 1:
            return APIResponseResult.APIResponse(-3,
                                                 "appid或appsecret有误,审核状态为:{}".format(str(
                                                     models.approve_state_choices[int(networkopenapi.approveState)][
                                                         1])))
        # 判断请求是否IP白名单
        ipwhitelist = networkopenapi.ipwhitelist
        ipFlag = list(x for x in ipwhitelist if x["ip"] == ip)
        if len(ipFlag) == 0:
            return APIResponseResult.APIResponse(-4, "当前客户端ip:{},未在api白名单中设置".format(ip))

        networkopentemp = models.networkOpenTemp.objects.filter(networkopenapi=networkopenapi,
                                                                tempNumber=tempnumber).first()
        useinfoapi = models.useInfoAPI.objects.create(networkopenapi=networkopenapi, networkopentemp=networkopentemp,
                                                      startTime=startTime, )

        netTaskList = {}
        listkwargs = ast.literal_eval(listkwargs)
        listkwargs = list(x for x in listkwargs if x["ip"] != '')
        for item in listkwargs:
            netip = str(item["ip"]).strip()
            if netip in netTaskList.keys():
                cmds = netTaskList[netip]
                netTaskList[netip] = cmds + [{"key": str(item["key"]).strip(), "value": str(item["value"])}]
            else:
                cmds = []
                cmds.append({"key": str(item["key"]).strip(), "value": str(item["value"]).strip()})
                netTaskList.update({netip: cmds})

        for key, items in netTaskList.items():
            networkopenapilist = models.networkOpenAPIList.objects.create(networkopenapi=networkopenapi,
                                                                          networkopentemp=networkopentemp,
                                                                          ip=key,
                                                                          username=username,
                                                                          password=password, port=port,
                                                                          creator=useinfoapi.creator,
                                                                          editor=useinfoapi.editor)

            for cmdKwargs in items:
                models.networkOpenAPIListKwargs.objects.create(networkopenapilist_id=networkopenapilist.id,
                                                               key=cmdKwargs["key"],
                                                               value=cmdKwargs["value"],
                                                               creator=useinfoapi.creator,
                                                               editor=useinfoapi.editor)
            # 绑定关系
            useinfoapi.networkopenapilist.add(networkopenapilist)

            # 同步方法立即运行
            resultInfo = {"taskNumber": useinfoapi.taskNumber}
            if taskState == 1:
                resultInfo.update({"start": strftime('%Y-%m-%d %H:%M:%S', localtime())})
                useinfoapis = models.useInfoAPI.objects.filter(taskNumber=useinfoapi.taskNumber, )
                for useInfo in useinfoapis:
                    networkopenapilist = useInfo.networkopenapilist.all().filter(taskStatus=0)
                    for item in networkopenapilist:
                        Write_Send_Command(item.id)
                resultInfo.update({"end": strftime('%Y-%m-%d %H:%M:%S', localtime())})

        return APIResponseResult.APIResponse(0, "success", resultInfo)

    # 运行API提交的任务
    @action(methods=['get'], detail=False, url_path='run')
    def run(self, request, *args, **kwargs):
        # nid是 useinfoapi taskNumber 列 则重新执行startTime__lte=strftime('%Y-%m-%d %H:%M:%S', localtime())
        nid = request.GET.get("nid", None)
        if nid is None:
            useinfoapis = models.useInfoAPI.objects.filter(enabled=True, taskStatus=0,
                                                           startTime__lte=strftime('%Y-%m-%d %H:%M:%S',
                                                                                   localtime())).order_by("createTime")[
                          0:3]
        else:
            useinfoapis = models.useInfoAPI.objects.filter(taskNumber=nid, enabled=True, )
            if useinfoapis is None:
                return APIResponseResult.APIResponse(0, "任务不存在,请检查参数是否有误...", )
            # 将当前任务对应的执行状态全部更新为待处理
            useinfoapis[0].networkopenapilist.all().update(taskStatus=0)
        runInfo = []
        runInfo.append({"start": strftime('%Y-%m-%d %H:%M:%S', localtime())})

        for useInfo in useinfoapis:
            networkopenapilist = useInfo.networkopenapilist.all().filter(taskStatus=0)
            with ThreadPoolExecutor(max_workers=30) as executor:
                for item in networkopenapilist:
                    infos = {item.id}
                    executor.map(Write_Send_Command, infos)
        runInfo.append({"end": strftime('%Y-%m-%d %H:%M:%S', localtime())})
        return APIResponseResult.APIResponse(0, "开始运行执行中...", runInfo)

    # 运行结果
    @action(methods=['get'], detail=False, url_path='runResult')
    def runResult(self, request, *args, **kwargs):
        nid = request.GET.get("nid", 0)
        if nid == 0:
            return APIResponseResult.APIResponse(-1, "参数有无请稍后再试")
        # 查询任务当前状态
        useinfoapi = models.useInfoAPI.objects.filter(taskNumber=nid).first()
        if useinfoapi is None:
            return APIResponseResult.APIResponse(-2, "任务不存在或已删除")
        networkopenapi = useinfoapi.networkopenapi
        networkopentemp = useinfoapi.networkopentemp
        networkopenapilist = useinfoapi.networkopenapilist.all()

        downloadResult = {}
        for item in networkopenapilist:
            if item.ip in downloadResult.keys():
                newResult = downloadResult[item.ip]
                newResult.append({"cmds": networkopentemp.cmds,
                                  "cmdInfo": item.cmdInfo,
                                  "jsonResult": item.jsonResult,
                                  "exceptionInfo": item.exceptionInfo,
                                  "createTime": item.createTime,
                                  "lastTime": item.createTime, })
                downloadResult[item.ip] = newResult
            else:
                downloadResult.update({item.ip: [
                    {"cmds": networkopentemp.cmds,
                     "cmdInfo": item.cmdInfo,
                     "jsonResult": item.jsonResult,
                     "exceptionInfo": item.exceptionInfo,
                     "createTime": item.createTime,
                     "lastTime": item.createTime, }]})
        # 设备总数
        sumCount = len(networkopenapilist)
        # 待处理
        pending = len(networkopenapilist.filter(taskStatus=0))
        # 已完成
        success = len(networkopenapilist.filter(taskStatus=2))
        # 执行失败
        errors = len(networkopenapilist.filter(taskStatus=-1))

        taskInfo = {"name": networkopenapi.title, "sumCount": str(sumCount) + "台", "pending": str(pending) + "台",
                    "success": str(success) + "台",
                    "errors": str(errors) + "台",
                    "progress": '{:.0%}'.format((success + errors) / sumCount), "results": downloadResult}
        return APIResponseResult.APIResponse(0, 'success', taskInfo,
                                             http_status=status.HTTP_200_OK, )
