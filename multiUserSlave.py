#coding=utf8
import itchat
from itchat.content import *

newInstance = itchat.new_instance()
newInstance.auto_login(hotReload=False, statusStorageDir='newInstance.pkl')

@newInstance.msg_register(TEXT)
def reply(msg):
    return msg['Text']

newInstance.run()
