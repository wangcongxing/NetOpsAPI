from app import models
from utils import rsaEncrypt
from netmiko import ConnectHandler
from nornir_netmiko import netmiko_send_command
import os
from time import strftime, localtime
from textfsm import TextFSM
from utils.cmdb_inventory_v2 import CMDBInventory
from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir import InitNornir
import site,ast
import shutil
from nornir.core.task import Result
from nornir_utils.plugins.functions import print_result
from nornir_netmiko import netmiko_send_command

rsaUtil = rsaEncrypt.RsaUtil()
#InventoryPluginRegister.register("cmdb_inventory", CMDBInventory)

ENV_PROFILE = os.getenv("ENV")
if ENV_PROFILE == "pro":
    from NetOpsAPI import pro_settings as config
elif ENV_PROFILE == "test":
    from NetOpsAPI import test_settings as config
else:
    from NetOpsAPI import settings as config

NTC_TEMPLATES_DIR = config.initConfig["NTC_TEMPLATES_DIR"]
# 通过netmiko 获取数据 只读

class netCommandInfo():

    # 通过netmiko 获取数据 只读
    def Read_Send_Command(dev):
        nid = dev["nid"]
        taskListdetails = models.networkOpenAPIList.objects.filter(id=nid).first()
        if taskListdetails is None:
            return False
        try:
            password = rsaUtil.decrypt_by_private_key(dev["password"])

            dev_info = {
                "device_type": dev["device_type"],
                "ip": dev["ip"],
                "username": dev["username"],
                "password": password,
                "conn_timeout": 20,
                "port": 22,
                # 'global_delay_factor': 1
            }

            firstCmds = dev["firstCmds"]
            cmd = dev["cmd"]
            textfsm = dev["textfsm"]

            # Task类通过host属性，读取yaml配置，获取其中设备信息
            # 判断文件是否存在
            # 不存在创建/有直接使用
            # 3.如果自己配置的textFSM报错,则使用系统模版use_textfsm=True
            jsonResult = []
            # 自定义textFSM不为空，并且自定义文件夹存在textFSM模版
            oldResult = ""
            with ConnectHandler(**dev_info) as conn:
                print("已经成功登陆交换机" + dev_info['ip'])
                print("nid=", nid)
                # 自定TextFSM模版路径
                textFsmTemplate = os.path.join(NTC_TEMPLATES_DIR,
                                               '{}_{}.textfsm'.format(dev_info["device_type"], cmd.replace(" ", "_")))
                # 记录下来用户回溯
                resultText = []
                cmdInfo = []
                command_cmds = str(firstCmds + "," + cmd).replace("/n", ",").split(',')
                for cmd_text in command_cmds:
                    oldResult = conn.send_command_timing(cmd_text)
                    resultText.append(
                        {"time": strftime('%Y-%m-%d %H:%M:%S', localtime()),
                         "base_prompt": "<{}>".format(conn.base_prompt),
                         "cmd": "{}".format(cmd_text),
                         "result": "<{}>{}\n{}".format(conn.base_prompt, cmd_text, oldResult)})
                    cmdInfo.append(
                        "<{}>{}".format(conn.base_prompt, cmd_text) + "\n" + "<{}>{}".format(conn.base_prompt, oldResult))

                oldResult = resultText[-1]["result"]
                cmd = resultText[-1]["cmd"]

                if textfsm != "" or os.path.exists(textFsmTemplate):
                    # 1.如果配置textFSM就用配置的
                    if not os.path.exists(textFsmTemplate):
                        f = open(textFsmTemplate, mode='w+', encoding='UTF-8')
                        # open()打开一个文件，返回一个文件对象
                        f.write(textfsm)  # 写入textfsm
                        f.close()
                    # print(cmd)
                    # Task类调用run方法，执行任务，如netmiko_send_command、write_file等插件use_textfsm=True
                    # 为什么不用use_textfsm=True  自定义模版需要频繁改动index文件 风险高
                    # output = result.result
                    f = open(textFsmTemplate)
                    template = TextFSM(f)
                    jsonResult = template.ParseTextToDicts(oldResult)  # template.ParseText(oldResult)
                    taskListdetails.jsonResult = jsonResult
                    f.close()
                else:
                    # 2.如果没有配置textFSM用系统自带的,use_textfsm=True
                    results = conn.send_command_timing(cmd, use_textfsm=True)
                    taskListdetails.jsonResult = results
                conn.disconnect()
                taskListdetails.exceptionInfo = ""
                taskListdetails.cmdInfo = cmdInfo
                taskListdetails.resultText = resultText
                taskListdetails.taskStatus = "已完成"
                taskListdetails.save()

        except Exception as e:
            print("nid={},ip={}".format(nid, dev["ip"]))
            taskListdetails.exceptionInfo = e.args
            taskListdetails.save()

    # 日常维护写入配置操作
    def Write_Send_Command(nid):
        try:
            item = models.networkOpenAPIList.objects.get(id=int(nid))
            netTask = item.networkopenapi
            password = rsaUtil.decrypt_by_private_key(netTask.password)
            dev_info = {
                "device_type": netTask.deviceType.deviceKey,
                "ip": item.ip,
                "username": netTask.username,
                "password": password,
                "conn_timeout": 20,
                "port": netTask.port,
            }
            cmds = netTask.cmds
            nid = item.id
            netmaintainiplistkwargs = models.networkOpenAPIList.objects.filter(netmaintainIpList=item)
            for cmdInfo in netmaintainiplistkwargs:
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
                item.resultText = ast.literal_eval(item.resultText) + resultText
                item.taskStatus = "已完成"

        except Exception as e:
            item.taskStatus = "执行失败"
            item.exceptionInfo = e.args
        finally:
            item.save()