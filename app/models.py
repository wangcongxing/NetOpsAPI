from django.db import models
import uuid, os
import random,datetime

# Create your models here.

ENV_PROFILE = os.getenv("ENV")
if ENV_PROFILE == "pro":
    from NetOpsAPI import pro_settings as config
elif ENV_PROFILE == "test":
    from NetOpsAPI import test_settings as config
else:
    from NetOpsAPI import settings as config


def newguid():
    return str(uuid.uuid1())


def getnumber():
    return '{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now()) + ''.join(
        [str(random.randint(1, 10)) for i in range(5)])


task_status_choices = (
    (0, "待处理"),
    (1, "处理中"),
    (2, "已完成"),
    (-1, "执行失败"),
)

device_state_choices = (
    (0, "禁用"),
    (1, "启用"),
)


def newImageName(instance, filename):
    # 日期目录和 随机文件名
    ext = str(filename.split('.')[-1]).upper()
    exts = ['PNG', 'JPG', 'GIF', ]
    if ext not in exts:
        ext = "PNG"

    filename = os.path.join(config.MEDIA_ROOT, 'nas/NetOpsOpenApi/deviceTypes/{}.{}'.format(uuid.uuid4().hex, ext))
    return filename


# 设备类型
class deviceTypes(models.Model):
    deviceKey = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="设备Key", )
    deviceValue = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="设备类型", )
    devlogo = models.ImageField(upload_to=newImageName, blank=True, null=True, verbose_name="设备LOGO", )

    deviceState = models.CharField(max_length=255, default="0", blank=True, null=True, verbose_name="是否禁用",
                                   choices=device_state_choices)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '网络设备类型'

    def __str__(self):
        self.deviceValue


# 网络设备登录用户
class loginUserInfo(models.Model):
    username = models.CharField(verbose_name="用户", max_length=255, blank=True, null=True, default="")
    password = models.CharField(verbose_name="密码", max_length=255, blank=True, null=True, default="")
    userstate = models.BooleanField(verbose_name="登录权限只读/写入", blank=True, null=True, default=False)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '网络设备登录用户'


# 网络服务API管理
class networkOpenAPI(models.Model):
    number = models.CharField(verbose_name="编号", max_length=255, blank=True, null=True, default=getnumber)
    title = models.CharField(verbose_name="名称", max_length=255, blank=True, null=True, default="")
    appid = models.CharField(verbose_name="应用ID", max_length=255, blank=True, null=True, default="")
    appsecret = models.CharField(verbose_name="应用密钥", max_length=255, blank=True, null=True, default="")
    redirectUrl = models.URLField(verbose_name="回调地址", max_length=255, blank=True, null=True, default="")
    ipwhitelist = models.TextField(verbose_name="IP白名单", max_length=255, blank=True, null=True, default="")
    phone = models.CharField(verbose_name="手机通知", max_length=255, blank=True, default="")
    email = models.CharField(verbose_name="邮箱通知", max_length=255, blank=True, default="")
    enabled = models.BooleanField(max_length=255, default=False, blank=True, null=True, verbose_name="是否禁用")
    desc = models.TextField(verbose_name='备注', max_length=500000, blank=True, default="")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '网络服务API'


# 接口场景列表
class networkOpenTemp(models.Model):
    title = models.CharField(verbose_name="名称", max_length=255, blank=True, default="")
    tempstate = models.BooleanField(verbose_name="操作范围(只读/写入)", blank=True, null=True, default=False)
    cmds = models.TextField(verbose_name="CMDS", max_length=500000, blank=True, default="")
    desc = models.TextField(verbose_name='备注', max_length=500000, blank=True, default="")
    useCount = models.IntegerField(verbose_name="使用次数", default=0, blank=False, null=False)
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '接口场景'


# 任务列表
class networkOpenAPIList(models.Model):
    networkopenapi = models.ForeignKey(networkOpenAPI, null=True, blank=True, on_delete=models.CASCADE,
                                       verbose_name="网络服务API", )
    startTime = models.CharField(verbose_name="开始时间", max_length=255, blank=True, default="")
    ip = models.GenericIPAddressField(verbose_name="IP", max_length=255, blank=True, null=True, default="")
    resultText = models.TextField(verbose_name="运行结果Json", max_length=500000, blank=True, default="[]")
    cmdInfo = models.TextField(verbose_name="运行结果", max_length=500000, blank=True, default="[]")
    taskStatus = models.CharField(verbose_name="任务状态", default="待处理", choices=task_status_choices, blank=False,
                                  null=False, max_length=255, )
    exceptionInfo = models.TextField(verbose_name="异常信息", max_length=500000, blank=True, default="")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '任务列表'


# 扩展参数

class networkOpenAPIListKwargs(models.Model):
    networkopenapilist = models.ForeignKey(networkOpenAPIList, null=True, blank=True, on_delete=models.CASCADE,
                                           verbose_name="任务列表", )
    key = models.CharField(verbose_name="参数名称", max_length=255, blank=True, null=True, default="")
    value = models.CharField(verbose_name="参数值", max_length=255, blank=True, null=True, default="")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = '扩展参数'
