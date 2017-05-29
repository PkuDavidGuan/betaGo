# -*- coding:utf8 -*-
import itchat
from itchat.content import *
import re
import sys
from secretary import analyze,ifPersonalInfo,analyzeJunk, groupNotice

itchat.auto_login(hotReload=False)

global groupDict
groupDict = dict()

global keywords
keywords = [u'所有人', u'关玉烁', u'乐在火旁']

class msgCache:
	def __init__(self, text, author, id):
		self.text = text
		self.user = author
		self.preText = [("", ""), ("", "")]
		self.nextText = [("", ""), ("", "")]
		self.senID = id

	def addPreText(self, preText1, preText2):
		self.preText[0] = preText1
		self.preText[1] = preText2

class groupCache:
	def __init__(self, groupname):
		self.cacheList = [('', ''), ('', ''), ('', ''), ('', ''), ('', '')]
		self.pointer = 0
		self.groupname = groupname
		self.singleMsg = list()
		self.groupSenID = 0
	def addMsg(self, msg):
		self.cacheList[self.pointer] = (msg['Content'], msg['ActualNickName'])
		return self.groupSenID
	def addPointer(self):
		self.pointer = (self.pointer + 1) % 5
		self.groupSenID += 1
	def addSpecialMsg(self, msg):
		oneMsg = msgCache(msg['Content'], msg['ActualNickName'], self.groupSenID)
		preText1 = self.cacheList[(self.pointer - 2 + 5) % 5]
		preText2 = self.cacheList[(self.pointer - 1 + 5) % 5]
		oneMsg.addPreText(preText1, preText2)
		self.singleMsg.append(oneMsg)

def dealMsg(msg):
	groupname = msg['User']['NickName']
	if groupname not in groupDict.keys():
		groupDict[groupname] = groupCache(groupname)
	id = groupDict[groupname].addMsg(msg)
	for Smsg in groupDict[groupname].singleMsg:
		if Smsg.senID == id - 1:
			Smsg.nextText[0] = (msg['Content'], msg['ActualNickName'])
		elif Smsg.senID == id - 2:
			Smsg.nextText[1] = (msg['Content'], msg['ActualNickName'])
	if groupNotice(msg['Content'], keywords):
		groupDict[groupname].addSpecialMsg(msg)
	groupDict[groupname].addPointer()



def checkGroupMsg():
	returnList = []
	for key, value in groupDict.items():
		singleMsgList = value.singleMsg
		for msg in singleMsgList:
			tempText = u'您在群聊 "'+ key + u'" 中收到和您有关的消息：\n'
			cnt = 1
			if msg.preText[0][1]:
				tempText += (str(cnt) + u". from User: " + msg.preText[0][1] + u", \n   Content: " + msg.preText[0][0] + u"\n")
				cnt += 1
			if msg.preText[1][1]:
				tempText += (str(cnt) + u". from User: " + msg.preText[1][1] + u", \n   Content: " + msg.preText[1][0] + u"\n")
				cnt += 1
			tempText += (str(cnt) + u". from User: " + msg.user + u", \n   Content: " + msg.text + u"\n")
			cnt += 1
			if msg.nextText[0][1]:
				tempText += (str(cnt) + u". from User: " + msg.nextText[0][1] + u", \n   Content: " + msg.nextText[0][0] + u"\n")
				cnt += 1
			if msg.nextText[1][1]:
				tempText += (str(cnt) + u". from User: " + msg.nextText[1][1] + u", \n   Content: " + msg.nextText[1][0] + u"\n")
				cnt += 1
			returnList.append(tempText)
	return returnList

@itchat.msg_register([TEXT, MAP, CARD, NOTE, SHARING])
def text_reply(msg):
	sendBackUser = itchat.search_friends(name=sys.argv[1])
	UserID = sendBackUser[0]['UserName']

	if(msg['FromUserName'] == UserID):
		print(msg['Content'] == u'我要检查未读消息')
		if msg['Content'] == u'我要检查未读消息':
			print("Check group message")
			textList = checkGroupMsg()
			for text in textList:
				itchat.send(text, itchat.originInstance.storageClass.userName)
			groupDict.clear()
			return

		print('Master received a message from slave')
		return					# if the message is from the slave, we believe it is safe
	if msg['MsgType'] == 1:
		print('Master Recieved a text message!')
		textContent = msg['Text']
		if (msg['FromUserName'] != itchat.originInstance.storageClass.userName) and (analyze(textContent, 0)):
			itchat.send('您可能在和“%s”的聊天中被询问私人信息，请注意防范 聊天内容为：\n\n%s' % (msg['User']['NickName'], msg['Text']), UserID)
		elif (msg['FromUserName'] == itchat.originInstance.storageClass.userName) and (ifPersonalInfo(textContent)):
			itchat.send('您可能在和“%s”的聊天中泄露了私人信息，请注意防范 聊天内容为：\n\n%s\n\n请及时撤回' % (msg['User']['NickName'], msg['Text']), UserID)
	if msg['MsgType'] == 49:
		print('Master recieved a notification!')
		titleContent = msg['FileName']
		snippetContent = msg['Content']
		if analyzeJunk(titleContent) or re.findall(snippetContent):
			print('Master received an annoying notification!')
			itchat.send('您在和“%s”的聊天中收到一条垃圾推送，其标题为：\n\n%s\n\n请 \
			注意钱包安全\ue409' % (msg['User']['NickName'], titleContent), UserID)


@itchat.msg_register([TEXT, SHARING], isGroupChat=True)
def groupchat_reply(msg):
	sendBackUser = itchat.search_friends(name=sys.argv[1])
	UserID = sendBackUser[0]['UserName']
	if msg['MsgType'] == 1:
		print('Recieve a text message!')

		dealMsg(msg)

		textContent = msg['Text']
		if (msg['FromUserName'] != itchat.originInstance.storageClass.userName) and (analyze(textContent, 0)):
			itchat.send('您在群聊“%s”中被“%s”被询问私人信息，请注意防范。聊天内容为：\n\n%s\n\n请及时撤回' % (msg['User']['NickName'], msg['ActualNickName'], msg['Content']), UserID)
		elif (msg['FromUserName'] == itchat.originInstance.storageClass.userName) and ifPersonalInfo(textContent):
			itchat.send('您在群聊“%s”中向“%s”泄露了私人信息，请注意防范。聊天内容为：\
				\n\n%s\n\n请及时撤回' % (msg['User']['NickName'], msg['ActualNickName'], msg['Content']), UserID)

	if msg['MsgType'] == 49:
		print('Recieve a notification!')
		titleContent = msg['FileName']
		snippetContent = msg['Content']
		if analyzeJunk(titleContent) or re.findall(snippetContent):
			print('annoying notification detected!')
			itchat.send('您在群聊“%s”中收到“%s”的一条垃圾推送，其标题为：\n\n%s\n\n请 \
			注意钱包安全\ue409' % (msg['User']['NickName'], msg['ActualNickName'], titleContent), UserID)

itchat.run()
