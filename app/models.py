from django.db import models
import uuid, os
import random, datetime
from utils import rsaEncrypt
from time import strftime, localtime

# Create your models here.

rsaUtil = rsaEncrypt.RsaUtil()

ENV_PROFILE = os.getenv("ENV")
if ENV_PROFILE == "pro":
    from NetOpsAPI import pro_settings as config
elif ENV_PROFILE == "test":
    from NetOpsAPI import test_settings as config
else:
    from NetOpsAPI import settings as config


def newguid():
    return str(uuid.uuid1())


def currentTime():
    return strftime('%Y-%m-%d %H:%M:%S', localtime())


# 网络服务API密钥
def apiNewSecret():
    return rsaUtil.encrypt_by_public_key(str(uuid.uuid1()))


def getAppid():
    return '{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now()) + ''.join(
        [str(random.randint(1, 10)) for i in range(5)])


task_status_choices = (
    (0, "待处理"),
    (1, "处理中"),
    (2, "已完成"),
    (-1, "执行失败"),
)
approve_state_choices = (
    (0, "申请中"),
    (1, "已批准"),
    (-1, "已驳回"),
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




# 网络服务API管理
class networkOpenAPI(models.Model):
    title = models.CharField(verbose_name="名称", max_length=255, blank=True, null=True, default="")
    appid = models.CharField(verbose_name="应用ID", max_length=255, blank=True, null=True, default=getAppid)
    appsecret = models.CharField(verbose_name="应用密钥", max_length=255, blank=True, null=True, default=newguid)
    callbackUrl = models.URLField(verbose_name="回调地址", max_length=255, blank=True, null=True, default="")
    ipwhitelist = models.JSONField(verbose_name="IP白名单", max_length=50000, blank=True, null=True, default=dict)
    approveState = models.CharField(max_length=255, default=0, blank=True, null=True, verbose_name="审核状态",
                                    choices=approve_state_choices)
    phone = models.CharField(verbose_name="手机通知", max_length=255, blank=True, default="")
    email = models.CharField(verbose_name="邮箱通知", max_length=255, blank=True, default="")
    enabled = models.BooleanField(max_length=255, default=False, blank=True, null=True, verbose_name="是否禁用")
    desc = models.TextField(verbose_name='备注', max_length=500000, blank=True, default="")
    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    def getAppid(self):
        return "{}".format(self.appid)

    class Meta:
        verbose_name = verbose_name_plural = '网络服务API'


# 接口场景列表
class networkOpenTemp(models.Model):
    networkopenapi = models.ForeignKey(networkOpenAPI, null=True, blank=True, on_delete=models.CASCADE,
                                       verbose_name="网络服务API", )
    deviceType = models.ForeignKey(deviceTypes, null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name="设备类型", )

    tempNumber = models.CharField(verbose_name="场景编号", max_length=255, blank=True, null=True, default=newguid)
    title = models.CharField(verbose_name="名称", max_length=255, blank=True, default="")
    cmds = models.TextField(verbose_name="CMDS", max_length=500000, blank=True, default="")
    TextFSMTemplate = models.TextField(verbose_name='TextFSM模版', max_length=500000, blank=True, default="")
    tempState = models.CharField(max_length=255, default=0, blank=True, null=True, verbose_name="审核状态",choices=approve_state_choices)
    desc = models.TextField(verbose_name='备注', max_length=500000, blank=True, default="")
    useCount = models.IntegerField(verbose_name="使用次数", default=0, blank=False, null=False)
    # 共有 私有
    # 关注
    # 点赞
    # 评论
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
    networkopentemp = models.ForeignKey(networkOpenTemp, null=True, blank=True, on_delete=models.CASCADE,
                                        verbose_name="网络服务场景", )
    ip = models.GenericIPAddressField(verbose_name="IP", max_length=255, blank=True, null=True, default="")
    username = models.CharField(verbose_name="用户名", max_length=255, blank=True, default="")
    password = models.CharField(verbose_name="密码", max_length=255, blank=True, default="")
    port = models.IntegerField(verbose_name="端口", blank=True, null=True, default=22)
    jsonResult = models.TextField(verbose_name="运行结果Json", max_length=500000, blank=True, default="[]")
    cmdInfo = models.TextField(verbose_name="运行结果", max_length=500000, blank=True, default="[]")
    taskStatus = models.CharField(verbose_name="任务状态", default=0, choices=task_status_choices, blank=False,
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


# API使用
class useInfoAPI(models.Model):
    startTime = models.CharField(verbose_name="开始时间", max_length=255, blank=True, default=currentTime)
    taskNumber = models.CharField(verbose_name="编号", max_length=255, blank=True, null=True, default=newguid)

    taskStatus = models.CharField(verbose_name="任务状态", default=0, choices=task_status_choices, blank=False,
                                  null=False, max_length=255, )
    enabled = models.BooleanField(max_length=255, default=False, blank=True, null=True, verbose_name="是否禁用")

    networkopenapi = models.ForeignKey(networkOpenAPI, null=True, blank=True, on_delete=models.CASCADE,
                                       verbose_name="网络服务API", )
    networkopentemp = models.ForeignKey(networkOpenTemp, null=True, blank=True, on_delete=models.CASCADE,
                                        verbose_name="网络服务场景", )
    networkopenapilist = models.ManyToManyField(networkOpenAPIList, blank=True,
                                                verbose_name="任务列表", )

    createTime = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    lastTime = models.DateTimeField(auto_now=True, verbose_name="修改时间")
    creator = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="创建者", )
    editor = models.CharField(max_length=255, default="", blank=True, null=True, verbose_name="修改者", )

    class Meta:
        verbose_name = verbose_name_plural = 'API使用情况'
