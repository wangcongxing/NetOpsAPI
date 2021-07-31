from rest_framework.routers import DefaultRouter
from django.urls import path, include
from app import views, modeExport

router = DefaultRouter()  # 可以处理视图的路由器
router.register(r'deviceTypes', views.deviceTypesViewSet)  # 设备类型管理
router.register(r'deviceTypesExport', modeExport.deviceTypesExport)  # 设备类型导出
router.register(r'networkOpenAPI', views.networkOpenAPIViewSet)  # OpenAPI管理

urlpatterns = [
    # 默认数据初始化
    path('initInfo', views.InitInfo.as_view()),
    # 获取token
    path('getToken', views.GetAccessToken.as_view()),

]

urlpatterns += router.urls
