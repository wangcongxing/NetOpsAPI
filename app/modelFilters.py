from django_filters import rest_framework as filters
import django_filters
from app import models


class loginUserInfoFilter(filters.FilterSet):
    # 模糊过滤
    username = django_filters.CharFilter(field_name="username", lookup_expr='icontains')

    class Meta:
        model = models.loginUserInfo
        fields = ["username", ]


class networkOpenAPIFilter(filters.FilterSet):
    # 模糊过滤
    deviceType = django_filters.CharFilter(field_name="deviceType", )
    number = django_filters.CharFilter(field_name="number", lookup_expr='icontains')
    title = django_filters.CharFilter(field_name="title", lookup_expr='icontains')
    appid = django_filters.CharFilter(field_name="appid", lookup_expr='icontains')
    desc = django_filters.CharFilter(field_name="desc", lookup_expr='icontains')

    class Meta:
        model = models.networkOpenAPI
        fields = ["deviceType", 'number', 'title', "appid", "desc"]


class deviceTypesFilter(filters.FilterSet):
    # 模糊过滤
    id = django_filters.CharFilter(field_name="id", )
    deviceState = django_filters.CharFilter(field_name="deviceState", )
    deviceValue = django_filters.CharFilter(field_name="deviceValue", lookup_expr='icontains')

    class Meta:
        model = models.deviceTypes
        fields = ['id', 'deviceValue', 'deviceState']


class networkOpenTempFilter(filters.FilterSet):
    # 模糊过滤
    title = django_filters.CharFilter(field_name="title", lookup_expr='icontains')
    desc = django_filters.CharFilter(field_name="desc", lookup_expr='icontains')

    class Meta:
        model = models.networkOpenTemp
        fields = ['title', "desc", ]

class networkOpenAPIListFilter(filters.FilterSet):
    # 模糊过滤
    netmaintain = django_filters.CharFilter(field_name="netmaintain", )
    ip = django_filters.CharFilter(field_name="ip", lookup_expr='icontains')

    class Meta:
        model = models.networkOpenAPIList
        fields = ["netmaintain", 'ip', ]
