# -*- coding: utf-8 -*- 
#!/usr/bin/env python
#
#__author__= 'ihciah@gmail.com'
#__author__= 'BaiduID-ihciah'
#__author__= '13307130364@fudan.edu.cn'
#__author__= 'http://www.ihcblog.com'
VERSION='1.3'
#在保留版权的基础上可以修改、重新发布
#但不允许用于商业用途或出售等


#搭建帮助：http://www.ihcblog.com/qqrobothelp/
#如遇问题请发邮件至ihciah@gmail.com

def accountinfo():
    myqq=''#引号中填写机器人QQ号码
    mypsw=''#引号中填写机器人QQ密码
    return (myqq,mypsw)

robotname=''
#    给机器人取个名字吧！（中英文，不含符号）示例：椎名真白

sleeptime=7
#    一段时间后无人应答的休眠时间。
#    该时间以秒为单位，7表示7秒后对聊天做出响应（一旦响应，只要5分钟内有聊天，速度即提升至1s2次）
#    推荐设置7，虽然第一次聊天等待时间较长，但可大幅节约云豆消耗
#    如果你有SAE的开发者认证云豆充足，可以把这个数值减少到4或以下

adminlist=['287280953']
#    adminlist为管理员列表，示例：adminlist=['10000','12345','287280953']
#    查看可用的管理员指令，请使用管理员账号回复“管理员帮助”

supadminlist=['287280953']
#     adminlist为超级管理员列表，示例supadminlist=['10000','12345','287280953']
#     查看可用的管理员指令，请使用管理员账号回复“管理员帮助”



#------以下的三项设置请无视---------
adminemail='ihciah@gmail.com'
#    QQ下线后会自动向该邮箱发送邮件，你可以把它设置为QQ邮箱或者有短信提醒的189、126邮箱等，方便您随时监控
#    【注意】该功能默认关闭。要开启请添加Cron任务，详情请Email至ihciah@gmail.com

gmailacc=''
gmailpsw=''
#    发送邮件使用的Gmail邮箱，若不需邮件提醒功能可不填写