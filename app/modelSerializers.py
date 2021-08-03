from rest_framework import viewsets, serializers, status
import requests, os, json
from app import models
from django.db import transaction
import ast
from utils import rsaEncrypt
import datetime
import random
from django.db.models import Q

rsaUtil = rsaEncrypt.RsaUtil()
ENV_PROFILE = os.getenv("ENV")
if ENV_PROFILE == "pro":
    from NetOpsAPI import pro_settings as config
elif ENV_PROFILE == "test":
    from NetOpsAPI import test_settings as config
else:
    from NetOpsAPI import settings as config


# 设备类型
class deviceTypesSerializer(serializers.ModelSerializer):
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    lastTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.deviceTypes
        fields = ["id", "deviceKey", "deviceValue", "deviceState", "createTime", "lastTime", "creator", "editor"]
        # depth = 1


# 网络服务API管理
class networkOpenAPISerializer(serializers.ModelSerializer):
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    lastTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    def create(self, validated_data):
        password = validated_data.get("phone", "")
        if password != "":
            validated_data.update({"phone": str(rsaUtil.encrypt_by_public_key(password), 'utf-8')})
        loginuserinfo = super().create(validated_data)
        return loginuserinfo

    class Meta:
        model = models.networkOpenAPI
        fields = ["id", "getAppid", "title", "redirectUrl", "ipwhitelist", "phone", "email",
                  "desc",
                  "enabled",
                  "createTime", "lastTime", "creator", "editor"]
        depth = 1


class networkOpenTempSerializer(serializers.ModelSerializer):
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    lastTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    def create(self, validated_data):
        validated_data.update({"networkopenapi_id": int(self.initial_data["nid"])})
        validated_data.update({"deviceType_id": int(self.initial_data["tid"])})

        tempTask = super().create(validated_data)
        return tempTask

    def update(self, instance, validated_data):
        validated_data.update({"networkopenapi_id": int(self.initial_data["nid"])})
        validated_data.update({"deviceType_id": int(self.initial_data["tid"])})
        tempTask = super().update(instance, validated_data)
        return tempTask

    class Meta:
        model = models.networkOpenTemp
        fields = ["id", "title", "cmds", "TextFSMTemplate", "desc", "useCount", "createTime",
                  "lastTime", "creator",
                  "editor"]

        depth = 1


class networkOpenAPIListSerializer(serializers.ModelSerializer):
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    lastTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    executionInfo = serializers.SerializerMethodField()

    def get_executionInfo(self, obj):
        if obj.networkopenapi is None:
            return []
        cmds = obj.netmaintain.cmds
        networkopenapilistkwargs = models.networkOpenAPIListKwargs.objects.filter(netmaintainIpList=obj)
        for cmdInfo in networkopenapilistkwargs:
            cmds = str(cmds).replace(cmdInfo.key, cmdInfo.value)
        cmds = str(cmds).replace("\n", ",").replace("；", ",").replace(";", ",").split(",")  # 根据回撤逗号分割

        return cmds

    class Meta:
        model = models.networkOpenAPIList
        fields = ["id", "ip", "executionInfo", "resultText", "cmdInfo", "exceptionInfo",
                  "createTime", "lastTime", "creator", "editor"]


class useInfoAPISerializer(serializers.ModelSerializer):
    createTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    lastTime = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    class Meta:
        model = models.useInfoAPI
        fields = ["id", "taskNumber",
                  "createTime", "lastTime", "creator", "editor"]
