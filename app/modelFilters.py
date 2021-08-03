from django_filters import rest_framework as filters
import django_filters
from app import models


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


class useInfoAPItFilter(filters.FilterSet):
    # 模糊过滤
    taskNumber = django_filters.CharFilter(field_name="taskNumber", lookup_expr='icontains')

    class Meta:
        model = models.useInfoAPI
        fields = ["taskNumber", ]
