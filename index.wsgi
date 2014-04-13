# -*- coding: utf-8 -*- 
#!/usr/bin/env python
#
#__author__= 'ihciah@gmail.com'
#__author__= 'BaiduID-ihciah'
#__author__= '13307130364@fudan.edu.cn'
#__author__= 'http://www.ihcblog.com'
#在保留版权的基础上可以修改、重新发布
#但不允许用于商业用途或出售等
import tornado.wsgi,urllib2,cookielib,urllib,json,base64
import MySQLdb,time,re,math,pylibmc
import sae.const
from sae.taskqueue import Task
from sae.taskqueue import TaskQueue
from sae.taskqueue import add_task
from sae.mail import send_mail
import logging
import sys,myconfig


def smartmode():
  return 1
def strc(ihc1,ihc2,ihc3):
  istart = ihc1.find(ihc2)+ len(ihc2)
  if ihc1.find(ihc2)==-1:
    return ''
  iend = ihc1.find(ihc3, istart)
  if iend==-1:
    iend=len(ihc1)-1
  return ihc1[istart:iend]
def gettime():
  return int(time.time()-1355588543)
def getmydb():
  mydb = MySQLdb.connect(
      host   = sae.const.MYSQL_HOST,
      port   = int(sae.const.MYSQL_PORT),
      user   = sae.const.MYSQL_USER,
      passwd = sae.const.MYSQL_PASS,
      db = sae.const.MYSQL_DB,
      charset = 'utf8')
  return mydb
def getchaturl(sid):
  (myqq,mypsw)=myconfig.accountinfo()
  return 'http://q16.3g.qq.com/g/s?aid=nqqchatMain&sid='+sid+'&myqq='+myqq
def login():
  (myqq,mypsw)=myconfig.accountinfo()
  ua='Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
  cookie=cookielib.CookieJar()
  opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
  opener.addheaders = [('User-Agent', ua)]
  urllib2.install_opener(opener)
  #第一步get到posturl
  first=urllib2.urlopen('http://pt.3g.qq.com/s?aid=nLogin3gqq').read()
  posturl=strc(first,'''<br /><FORM action="''','"')
  #第二步POST
  data=urllib.urlencode({'aid':'nLoginHandle',
                        'lloginType':'1',
                        'modifySKey':'0',
                        'q_from':'',
                        'login_url':'bs?aid=nLoginnew&q_from=3GQQ',
                        'pwd':mypsw,
                        'toQQchat':'true',
                        'bid_code':'3GQQ',
                        'qq':myqq,
                        'i_p_w':'qq|pwd|'})
  second=opener.open(posturl,data)
  newcontent=second.read()
  newurl=second.geturl()
  if newcontent.find('3g.qq.com/g/s')!=-1:
    return strc(newurl,'pid=','&')
  #提取、返回sid
  else:
    return 0
def exe(qq,s):
  r=''
  s=s.replace('^S',' ').replace('^H','\n')
  exec('''a=int(time.strftime('%y%d%m'))+int(time.strftime('%y'))+int(time.strftime('%d'))+int(time.strftime('%m'))^Hb=0^Hfor^Si^Sin^Sqq:^H^S^Sb+=int(i)^Hr='您的今日人品为:'+str(math.sin(a*int(b))*50+50)[:5]''')
  return r
def createtable(k):
  #1:systeminfo存储该QQ相关信息
  #2:answer存储问题及回答
  #3:robotchatter存储聊天者相关信息
  #4:robotjoke用于消费积分后购买物品
  mydb = getmydb()
  cursor = mydb.cursor()
  if k==1:
    cmd = """create table if not exists systeminfo (
           uid int(5) not null,
           lastlogin int(25),
           sid char(250),
           primary key (uid))"""
  elif k==2:
    cmd = """create table if not exists answer (
           q char(250) not null,
           a char(250) not null,
           qq char(50))"""
  elif k==3:
    cmd = """create table if not exists robotchatter (
           qq char(50) not null,
           coin int(15),
           contri int(15),
           primary key (qq))"""
  elif k==4:
    cmd = """create table if not exists robotshop (
           name char(50),
           shop char(255),
           price int(5) not null)"""
  cursor.execute(cmd)
  mydb.close()
def writeinfo(sid):
  mydb = getmydb()
  cursor = mydb.cursor()
  lastlogin=gettime()
  if str(cursor.execute("select * from systeminfo where uid=1"))=="0":
    cursor.execute("insert into systeminfo (uid,lastlogin,sid) values (1,%d,'%s')" %(lastlogin,sid))
  else:
    cursor.execute("update systeminfo set lastlogin=%d,sid='%s' where uid=1" %(lastlogin,sid))
  mydb.close()
def getinfo():
  mydb = getmydb()
  cursor = mydb.cursor()
  cursor.execute('select * from systeminfo where uid=1')
  result=cursor.fetchone()
  info={}
  if result is not None:
    info['sid']=result[2]
    info['lastlogin']=result[1]
    mydb.close()
    return info
  else:
    return None
def getsid():
  cache = pylibmc.Client()
  sid=cache.get('sid')
  if sid is None:
    info=getinfo()
    cache.add('sid', info['sid'])
  try:
    a=info['sid']
  except:
    info=getinfo()
  return info['sid']
def qqb(qq):
  cache = pylibmc.Client()
  qqb=cache.get(str(qq)+'b')
  if qqb is None:
    cache.add(str(qq)+'b', 1,86400)
  else:
    cache.incr(str(qq)+'b',delta=1)
  return cache.get(str(qq)+'b')
def qqc(qq):
  cache = pylibmc.Client()
  qqb=cache.get(str(qq)+'b')
  if qqb is None:
    cache.add(str(qq)+'b', 0,86400)
  else:
    cache.set(str(qq)+'b', 0)
def updateqqa(qq,msg):
  cache = pylibmc.Client()
  qqa=cache.get(str(qq)+'a')
  retu=1
  if qqa is None:
    cache.add(str(qq)+'a', msg,86400)
    qqc(qq)
  else:
    if qqa==msg:
      ti=qqb(qq)
      if ti>10:
        retu=0
    else:
      qqc(qq)
      cache.set(str(qq)+'a', msg)
  return retu
def chg():
  sid=getsid()
  url='http://q32.3g.qq.com/g/s?sid=%s'%sid
  data=urllib.urlencode({'s':'10',
                         'aid':'chgStatus'})
  try:
    urllib.urlopen(url,data)
  except:
    a=1
def emotion(msg):
  b=['/:)','/pz','/se','/fd','/dy','/ll','/hx','/bz','/shui','/dk','/gg','/fn',
     '/tp','/cy','/jy','/ng','/kuk','/feid','/zk','/tu','/tx','/ka','/baiy','/am',
     '/jie','/kun','/jk','/lh','/hanx','/db','/fendou','/zhm','/yiw','/xu','/yun','/zhem',
     '/shuai','/kl','/qiao','/zj','/ch','/kb','/gz','/qd','/huaix','/zhh','/yhh','hq',
     '/bs','/wq','/kk','/yx','/qq','/xia','/kel','/cd','/xig','/pj','/lq','/pp',
     '/kf','/fan','/zt','/mg','/dx','/sa','/xin','/xs','/dg','/shd','/zhd','/dao',
     '/zq','/pch','/bb','/yl','/ty','/lw','/yb','/qiang','/ruo','/ws','/sl','/bq',
     '/gy','/qt','/cj','/aini','/bu','/hd','/aiq','/fw','/tiao','/fd','/oh','/zhq',
     '/kt','/ht','/tsh','/hsh','/jd','/jw','/xw','/zuotj','/youtj']
  while msg.find('（imgsrchttp://')!=-1 and msg.find('alt图片/）')!=-1:
    emo=strc(msg,'（imgsrc','alt图片/）')
    emo='（imgsrc'+emo+'alt图片/）'
    smile=strc(emo,'images/emo2009/','。gifalt')
    try:
      smile=b[int(smile)]
    except:
      smile=''
    msg=msg.replace(emo,smile)
  return msg

def incr(cursor,qq,coin,contri):
  if str(cursor.execute("SELECT * FROM robotchatter WHERE qq='%s' LIMIT 1" %qq))=='0':
    cursor.execute("insert into robotchatter (qq,coin,contri) values ('%s',0,0)" %qq)
  cursor.execute("update robotchatter set coin=coin+%s,contri=contri+%s where qq='%s'" \
                 %(str(coin),str(contri),qq))
def remark(score):
  score=int(score)
  if score==1:
    r='高居榜首哦'
  elif score<=3:
    r='恭喜进入前三强,继续努力吧/fendou'
  elif score<=10:
    r='前十名哦!继续努力!/fendou'
  elif score<=50:
    r='嘿嘿,前50嘛!继续努力吧/fendou'
  elif score<=100:
    r='前100名哦/hd'
  else:
    r='嗯,还没进前百强呢!/kel'
  return r
def getchat(self,html):
  (myqq,mypsw)=myconfig.accountinfo()
  if sys.getdefaultencoding() != 'UTF-8':
    reload(sys)
    sys.setdefaultencoding('UTF-8')
  state=strc(html,'/qbar/qbar_qqui_','.gif')
  self.write(state)###
  if state=='':
      self.write(html)
  if state=='online' or state=='hide':
    if state=='hide':
      chg()
    return 1
  if state=='QQMsg':
    #-----------------------urllib相关初始化
    ua='Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1'
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    opener.addheaders = [('User-Agent', ua)]
    urllib2.install_opener(opener)
    #----------------------
    mysid=getsid()
    chaturl='http://q32.3g.qq.com/g/s?sid=%s&3G_UIN=%s&saveURL=0&aid=nqqChat' %(mysid,myqq)
    chat=opener.open(chaturl).read()
    msg=strc(chat,'<div class="main-module bm-blue">','iv>')
    #消息特使符号过滤
    msg=strc(msg,'<p>','</p>').replace(' ','').replace("'",'').replace('"','').replace('\n','').replace(' ','').replace('</p>','').replace('<br/>','').replace('.','。').replace('=','').replace('%','').replace('*','').replace('chr','').replace('?','？')
    msg=msg.replace('&apos;','').replace('(','（').replace('<','（').replace('[','（').replace('{','（').replace(')','）').replace('>','）').replace(']','）').replace('}','）')
    low=msg.lower()
    flag=0
    if low.find('select')!=-1 or low.find('where')!=-1 or low.find('from')!=-1 or low.find('drop')!=-1 or low.find('delete')!=-1:
      flag=1#攻击探测
      logging.exception('日志-攻击探测-'+qq+':'+msg)
    msg=emotion(msg)
    qq=strc(chat,'name="u" value="','"/>').replace(' ','')
    #self.write('以下为网页内容')###调试
    #self.write(chat)###调试
    cache = pylibmc.Client()
    #更新最后聊天时间
    cache.set('lastchat', gettime())
    
    ca=cache.get(qq)
    #self.write('以下为msg内容')###调试
    #self.write(msg)###调试
    if flag==1:
      sendmsg(qq,'探测到您的指令中包含对系统造成威胁的词汇，'+myconfig.robotname+'已自动忽略处理！如果您发现本系统漏洞，欢迎与ihciah@gmail#com沟通，不胜感谢！',opener)
      return 1
    if updateqqa(qq,msg)==0:
      self.write('已处理自动回复')###调试
      return 1
    if chat.find('把您加入他的好友列表')!=-1:
      sendmsg(qq,'我是'+myconfig.robotname+',很高兴认识你!如果要教我请回复"学习",回复"帮助"可以查看全部指令',opener)
      return 1
    if msg.replace(' ','')=="":
      return 1
    if qq in myconfig.adminlist:
      #普通管理员区
      #管理员命令区,优先于常规问答
      if msg in ['管理员命令','管理员帮助','管理员指令']:
        adminhelp='\n管理员支持以下命令:\n括号里指命令后直接跟着的东西(Q指问题,A指回答),不打空格不打括号\n比如 QUERYQUESTION你好\n\n\
QUERYQQ(QQ)查询QQ对应信息\nQUERYQUESTION(Q)查询特定问题\nQUERYANSWER(A)查询特定回答\n\
DELONE(A)删除单个特定回答\nDELALL(A)删除全部特定回答(慎用,用前请查询以防勿删)\nBy Ihc~'
        if qq in myconfig.supadminlist:
          adminhelp='欢迎您,超级管理员Ihc!'+adminhelp+'\n超级管理员命令:\nDELByQQ(QQ):\n删除某QQ全部条目,慎用\nTOP:\n查看排名前十\nNEW:\n查看最新20条指令\n时间:\n查看最后登录时间'
          sendmsg(qq,adminhelp,opener)
        return 1
      if msg[:13]=='QUERYQUESTION' or msg[:7]=='QUERYQQ' or msg[:11]=='QUERYANSWER' or msg[:6]=='DELALL' or msg[:6]=='DELONE' or msg[:7]=='DELByQQ' or msg=='TOP' or msg=='NEW':
        logging.exception('日志-管理-'+qq+':'+msg)
        mydb = getmydb()
        cursor = mydb.cursor()
      if msg[:7]=='DELByQQ':
        if qq in ['adminQQ']:
          ts=cursor.execute("DELETE FROM answer WHERE qq='%s'" %msg[7:])
          sendmsg(qq,msg[7:]+'的相关词条已全部删除!本指令请慎用!',opener)
          mydb.close()
          return 1
        else:
          mydb.close()
      if msg[:6]=='DELONE':
        ts=cursor.execute("SELECT * FROM answer WHERE a='%s'" %msg[6:])
        if ts==1:
          result=cursor.fetchone()
          dqq=result[2]
          if dqq in myconfig.adminlist and qq!='adminQQ' and qq!=dqq:
            sendmsg(qq,'管理员间无法互相删除',opener)
          else:
            cursor.execute("DELETE FROM answer WHERE a='%s' LIMIT 1" %msg[6:])
            admin='当前该回答有一条,已删除一条,QQ:'+dqq
            sendmsg(qq,admin,opener)
          mydb.close()
          return 1
        elif ts==0:
          sendmsg(qq,'咕~在数据库里没找到这条回答\n(╯﹏╰）',opener)
          mydb.close()
          return 1
        else:
          sendmsg(qq,'查询到记录%d条,请使用删除多条功能.要查看所有对应问题及QQ，请使用QUERYANSWER命令' %ts,opener)
          mydb.close()
          return 1
      elif msg[:6]=='DELALL':
        ts=cursor.execute("SELECT * FROM answer WHERE a='%s'" %msg[6:])
        if ts<20 and ts!=0:
          cursor.execute("DELETE FROM answer WHERE a='%s' LIMIT 20" %msg[6:])
          admin='当前该回答有'+str(ts)+'条,已全部删除'
          sendmsg(qq,admin,opener)
          mydb.close()
          return 1
        elif ts==0:
          admin='咕~在数据库里没找到这样的回答\n(╯﹏╰）'
          sendmsg(qq,admin,opener)
          mydb.close()
        else:
          sendmsg(qq,'查询到记录%d条,大于20条,出于安全考虑,无法删除\n%>_<%' %ts,opener)
          mydb.close()
          return 1
      elif msg[:7]=='QUERYQQ':
        dqq=msg[7:]
        ts=cursor.execute("SELECT * FROM answer WHERE qq='%s'" %dqq)
        admin=''
        if ts>10:
          admin+='.数据过多,输出最后10条.'
          cursor.execute("SELECT * FROM answer WHERE qq='%s' LIMIT %d,10" %(dqq,ts-10))
        results=cursor.fetchall()
        if ts==0:
          admin='咕~未查询到该QQ相关数据\n(～ o ～)Y'
        else:
          for i in results:
            admin=admin+'\n'+'Question:'+i[0]+';Answer:'+i[1]
          cursor.execute("SELECT * FROM robotchatter WHERE qq='%s'" %dqq)
          result=cursor.fetchone()
          contri=str(result[2])
          rank=str(cursor.execute("SELECT * FROM robotchatter WHERE contri>%s" %contri)+1)
          admin='查询到'+str(ts)+'个词条.该用户贡献值:'+contri+',排行'+rank+'名,硬币:'+str(result[1])+admin
        if dqq in myconfig.adminlist and qq!='adminQQ' and qq!=dqq:
          admin='管理员间无法互相查询'
        sendmsg(qq,admin,opener)
        mydb.close()
        return 1
      elif msg[:11]=='QUERYANSWER':
        ts=cursor.execute("SELECT * FROM answer WHERE a='%s'" %msg[11:])
        admin='查询到%d条数据.' %ts
        if ts>10:
          admin+='数据过多,输出最后10条.'
          cursor.execute("SELECT * FROM answer WHERE qq='%s' LIMIT %d,10" %(msg[11:],ts-10))
        results=cursor.fetchall()
        for i in results:
          admin=admin+'\n'+'Question:'+i[0]+';QQ:'+i[2]
        if ts==0:
          admin=admin='咕~未查询到该回答相关数据\n╮(╯▽╰)╭'
        sendmsg(qq,admin,opener)
        mydb.close()
        return 1
      elif msg[:13]=='QUERYQUESTION':
        ts=cursor.execute("SELECT * FROM answer WHERE q='%s'" %msg[13:])
        admin='查询到%d条数据.' %ts
        if ts>10:
          admin+='数据过多,输出最后10条.'
          cursor.execute("SELECT * FROM answer WHERE q='%s' LIMIT %d,10" %(msg[13:],ts-10))
        results=cursor.fetchall()
        for i in results:
          admin=admin+'\n'+'Answer'+i[1]+';QQ'+i[2]
        if ts==0:
          admin='咕~未查询到该问题相关数据\n(ˇˍˇ）~'
        sendmsg(qq,admin,opener)
        mydb.close()
        return 1
      elif msg=='TOP' and qq in myconfig.supadminlist:
        ts=cursor.execute("SELECT * FROM robotchatter ORDER BY contri DESC LIMIT 15")
        results=cursor.fetchall()
        admin=''
        n=1
        for i in results:
          admin=admin+'第'+str(n)+'名:'+i[0]+';贡献:'+str(i[2])+';硬币:'+str(i[1])+'\n'
          n+=1
        sendmsg(qq,admin,opener)
        mydb.close()
        return 1
      elif msg=='NEW' and qq in myconfig.supadminlist:
        ts=cursor.execute("SELECT * FROM answer")
        if ts>20:
          cursor.execute("SELECT * FROM answer LIMIT %d,20" %(ts-20))
        results=cursor.fetchall()
        admin=''
        for i in results:
          admin=admin+'Q:'+i[0]+';A:'+i[1]+';QQ:'+i[2]+'\n'
        sendmsg(qq,admin,opener)
        mydb.close()
        return 1
      elif msg=='时间' and qq in myconfig.supadminlist:
        mydb = getmydb()
        cursor = mydb.cursor()
        cursor.execute('select * from systeminfo where uid=1')
        result=cursor.fetchone()
        cache = pylibmc.Client()
        outtime=gettime()-int(result[1])
        outtime=str(outtime/86400)
        sendmsg(qq,'上次登录是%s天前.\n%s.sinaapp.com/s?q=anyway\n点击可重新登录'%(sae.const.APP_NAME,outtime),opener)
        mydb.close()
        return 1
      
    if ca is None and msg!='' and msg!='<textarearows="':
      if msg not in ['学习','指令数','我的贡献','我的硬币','我的排名','笑话','贡献值','硬币','硬币数','我的金币','金币','金币数','测试','小测试','商店']:
        mydb = getmydb()
        cursor = mydb.cursor()
        msg=msg.replace('？','').replace('。','')
        if str(cursor.execute("SELECT * FROM answer WHERE q='%s' ORDER BY RAND() LIMIT 1" %msg))=='0':
          if smartmode()==0:
            resu=sendmsg(qq,'该问题还未学习,请回复"学习"教教'+myconfig.robotname+'吧~',opener)
          else:
            #----------------
            #调用SAE分词服务---
            _SEGMENT_BASE_URL = 'http://segment.sae.sina.com.cn/urlclient.php'
            payload = urllib.urlencode([('context', msg),])
            args = urllib.urlencode([('word_tag', 1), ('encoding', 'UTF-8'),])
            url = 'http://segment.sae.sina.com.cn/urlclient.php?' + args
            saj = urllib2.urlopen(url, payload).read()
            saj = eval(saj)
            mysqlque="""SELECT * FROM  `answer` WHERE  """
            impwords=[]
            for i in saj:
              if i.has_key('word_tag'):
                #121 POSTAG_ID_R_D    副词性代词(“怎么”)
                #122 POSTAG_ID_R_M    数词性代词(“多少”)
                #123 POSTAG_ID_R_N    名词性代词(“什么”“谁”)
                #124 POSTAG_ID_R_S    处所词性代词(“哪儿”)
                #125 POSTAG_ID_R_T    时间词性代词(“何时”)
                #126 POSTAG_ID_R_Z    谓词性代词(“怎么样”)
                #95  POSTAG_ID_N      名词
                #200 POSTAG_ID_SP     不及物谓词(主谓结构“腰酸”“头疼”)
                if int(i['word_tag']) in [121,122,123,124,125,126,95,200]:
                  impwords.append(i['word'])
            if len(impwords)==0:
              resu=sendmsg(qq,'该问题还未学习,请回复"学习"教教我吧~',opener)
            else:
              for i in impwords:
                mysqlque=mysqlque+""" `q` LIKE  '%"""+i+"""%' AND """
              mysqlque=mysqlque+""" 1=1 ORDER BY RAND() LIMIT 1"""
              if str(cursor.execute(mysqlque))=='0':
                resu=sendmsg(qq,'该问题还未学习,请回复"学习"教教我吧~',opener)
              else:
                result=cursor.fetchone()
                sendmsg(qq,result[1],opener)
                incr(cursor,qq,'1','0')#属性值增加
                mydb.close()
                return 1
              

          incr(cursor,qq,'0','0')#新增聊天者
          mydb.close()
          return 1
        else:
          result=cursor.fetchone()
          sendmsg(qq,result[1],opener)
          incr(cursor,qq,'1','0')#属性值增加
          mydb.close()
          return 1
      if msg=='指令数':
        mydb = getmydb()
        cursor = mydb.cursor()
        cmdcount=str(cursor.execute("SELECT * FROM answer WHERE 1"))
        sendmsg(qq,'现有指令数%s'%cmdcount,opener)
        incr(cursor,qq,'1','0')#属性值增加
        mydb.close()
        return 1
      if msg=='笑话':
        mydb = getmydb()
        cursor = mydb.cursor()
        if str(cursor.execute("SELECT * FROM robotshop WHERE name='joke' ORDER BY RAND() LIMIT 1"))=='0':
          sendmsg(qq,'该商品数量为零,无法购买!',opener)
        else:
          result=cursor.fetchone()
          price=int(result[2])
          cursor.execute("SELECT * FROM robotchatter WHERE qq='%s'" %qq)
          res=cursor.fetchone()
          coinnow=res[1]
          joke=str(result[1])+'(已扣除'+str(price)+'个硬币,剩余'+str(coinnow-price)+'个)'
          if coinnow<price:
            joke='硬币不足,请教教我或者多和我聊天吧!(回复 我的硬币 可以查看硬币数)'
          else:
            incr(cursor,qq,'-'+str(price),'0')#属性值减少
          sendmsg(qq,joke,opener)
        mydb.close()
        return 1
      if msg=='商店':
        sendmsg(qq,'回复指令购买:\n--笑话($5)\n--小测试($8)',opener)
      if msg in ['小测试','测试']:
        mydb = getmydb()
        cursor = mydb.cursor()
        price=8
        cursor.execute("SELECT * FROM robotchatter WHERE qq='%s'" %qq)
        res=cursor.fetchone()
        coinnow=res[1]
        a=int(time.strftime('%y%d%m'))+int(time.strftime('%y'))+int(time.strftime('%d'))+int(time.strftime('%m'))
        b=0
        for i in qq:
          b+=int(i)
        r=str(math.sin(a*int(b))*50+50)[:5]
        test='您今日人品为'+r+';(已扣除'+str(price)+'个硬币,剩余'+str(coinnow-price)+'个)'
        if coinnow<price:
          test='硬币不足,请教教我或者多和我聊天吧!(回复 我的硬币 可以查看硬币数)'
        else:
          incr(cursor,qq,'-'+str(price),'0')#属性值减少
        sendmsg(qq,test,opener)
        mydb.close()
        return 1
      if msg in ['我的贡献','我的排名','贡献值']:
        mydb = getmydb()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM robotchatter WHERE qq='%s'" %qq)
        result=cursor.fetchone()
        contri=str(result[2])
        myrank=str(cursor.execute("SELECT * FROM robotchatter WHERE contri>%s" %contri)+1)
        friend=str(cursor.execute("SELECT * FROM robotchatter"))
        if cursor.execute("SELECT * FROM robotchatter WHERE contri >%s ORDER BY contri ASC LIMIT 1" %contri)==1:
          r=cursor.fetchone()
          minus=r[2]-int(contri)
          mycontri='您现在的贡献值为'+contri+',在我的'+friend+'个朋友中排第'+myrank+'名,'+remark(myrank)+',距离上一名还差'+str(minus)+'贡献值,提升排行要多多教我啦!'
        else:
          mycontri='您现在的贡献值为'+contri+',在我的'+friend+'个朋友中排第'+myrank+'名,'+remark(myrank)+',提升排行要多多教我啦!'
        sendmsg(qq,mycontri,opener)
        incr(cursor,qq,'0','0')#属性值不变
        mydb.close()
        return 1
      if msg in ['我的硬币','硬币','硬币数','我的金币','金币','金币数']:
        mydb = getmydb()
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM robotchatter WHERE qq='%s'" %qq)
        result=cursor.fetchone()
        coin=str(result[1])
        m='您的硬币数为'+coin+',跟我聊天硬币加1,教我会加15哦!(悄悄的说一句,回复 笑话 可以购买笑话看~)'
        sendmsg(qq,m,opener)
        incr(cursor,qq,'0','0')#属性值不变
        mydb.close()
        return 1
      if msg=='学习':
        cache.add(qq,'1',1800)
        sendmsg(qq,'请输入问题',opener)
        #self.write('E')###
        return 1
    else:
      if ca=='1':
        if msg in ['学习','你是谁','指令数','帮助','我的贡献','我的硬币','我的排名','笑话','贡献值','硬币','硬币数','我的金币','金币数','金币']:
          sendmsg(qq,'该问题暂时不能学习，请重新输入问题吧！',opener)
          #self.write('F')###
          return 1
        else:
          cache.set(qq, msg,1800)
          sendmsg(qq,'请输入回答',opener)
          #self.write('G')###
          return 1
      else:
        question=ca.replace('？','').replace('。','')
        answer=msg
        mydb = getmydb()
        cursor = mydb.cursor()
        cursor.execute("insert into answer (q,a,qq) values ('%s','%s','%s')" %(question,answer,qq))
        cache.delete(qq)
        sendmsg(qq,'学习成功!您的问题是 %s;您的回答是 %s 回复“我的贡献”可以查看您的贡献哦！' %(question,answer),opener)
        incr(cursor,qq,'15','1')#属性值增加
        mydb.close()
        return 1
        

def sendmsg(qq,msg,opener):
  sid=getsid()
  url='http://q16.3g.qq.com/g/s?sid='+sid
  data=urllib.urlencode({'msg':msg,
                         'u':qq,
                         'saveURL':'0',
                         'do':'send',
                         'on':'1',
                         'saveURL':'0',
                         'aid':'发送',
                         'num':qq,
                         'do':'sendsms'})
  return opener.open(url,data).read()

def checkme():
  (myqq,mypsw)=myconfig.accountinfo()
  chkurl = 'http://wpa.qq.com/pa?p=1:'+myqq+':1'
  a = urllib2.urlopen(chkurl)
  length=a.headers.get("content-length")
  a.close()
  if length=='2329':
    return 'online'
  else:
    return 'offline'
def checkstate():
  if checkme()=='offline':
    if checkme()=='offline':
      sae.mail.send_mail(myconfig.adminemail, 'QQRobot is offline', 'QQRobot is offline',
        ('smtp.gmail.com', 587, myconfig.gmailacc, myconfig.gmailpsw, True))
      logging.exception('日志-每小时检查，下线了')
      

class Cron(tornado.web.RequestHandler):
  def get(self):
    (myqq,mypsw)=myconfig.accountinfo()
    ua='Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36'
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    opener.addheaders = [('User-Agent', ua)]
    opener.addheaders = [('Host', 'q16.3g.qq.com')]
    opener.addheaders = [('DNT', '1')]
    opener.addheaders = [('Accept-Encoding', 'gzip,deflate,sdch')]
    opener.addheaders = [('Accept-Language', 'zh-CN,zh;q=0.8')]
    urllib2.install_opener(opener)
    r=getsid()
    url=getchaturl(r)
    homepage=opener.open(url).read()
    #self.write(homepage)###
    if homepage.find('如果不能自动跳转请点击')!=-1:
      url=strc(homepage,'击<a href="','">这里')
      homepage=urllib2.urlopen(url).read()
      if homepage.find('/qbar/qbar_qqui_')!=-1:
        getchat(self,homepage)
      else:
        if homepage.find('重新登')!=-1:
          self.write(homepage)
        self.write(homepage)
    if homepage.find('sid已经过期')!=-1:
      #self.write('sid已过期')
      url='http://q16.3g.qq.com/g/s?aid=nqqchatMain&sid=%s&myqq=%s'%(r,myqq)
      homepage=urllib2.urlopen(url).read()
      url='http://pt.3g.qq.com/s?aid=nLogin3gqqbysid&3gqqsid=%s'%r
      homepage=urllib2.urlopen(url).read()

      if homepage.find('/qbar/qbar_qqui_')!=-1:
        getchat(self,homepage)
    if homepage.find('/qbar/qbar_qqui_')!=-1:
      getchat(self,homepage)
    time.sleep(0.5)
    #加长延时
    #性能优化(20131203)
    #通过Memcache记录最后聊天时间,若5分钟内无人聊天，则再休眠sleeptime秒。
    mc = pylibmc.Client()
    if not mc.get('lastchat'):
      mc.set('lastchat', gettime())
    if gettime()-mc.get('lastchat')>300:
      time.sleep(myconfig.sleeptime)
    
    
    #urllib2.urlopen('http://appid.sinaapp.com/cron')
    #更改调用机制只需注释本句，并修改计划任务，每分钟执行一次/task，再将sleeptime改为0.3
    #调用机制1：间隔0.3秒，通过Taskqueue调用，/task每分钟一次，一次push/cron250次
    #调用机制2：间隔1秒，自身调用
    self.write('OK')
class Create(tornado.web.RequestHandler):
  def get(self):
    createtable(1)
    createtable(2)
    createtable(3)
    createtable(4)
    self.write('创建表成功')
    info=getinfo()
    if info is None:
      mysid='ini'
      writeinfo(mysid)
      cache = pylibmc.Client()
      info=getinfo()
      sid=cache.get('sid')
      if sid is None:
        cache.add('sid', mysid)
      else:
        cache.set('sid', mysid)
      self.write('Cache,Database已更新')
      self.write(sid)
      self.write('初始化成功')
      logging.exception('日志-数据库初始化')
class Setsid(tornado.web.RequestHandler):
  def get(self):
    mysid = self.get_argument('sid','')
    if mysid!='':
      self.write('GET参数已获取<br>')
      writeinfo(mysid)
      cache = pylibmc.Client()
      info=getinfo()
      sid=cache.get('sid')
      if sid is None:
        cache.add('sid', mysid)
      else:
        cache.set('sid', mysid)
      self.write('Cache,Database已更新<br>')
      logging.exception('日志-Renew SID')
      #self.write(mysid)
    else:
      self.write('GET参数失败<br>')
class Jump(tornado.web.RequestHandler):
  def get(self):
    self.redirect('http://pt.3g.qq.com/')
class Task(tornado.web.RequestHandler):
  def get(self):
    myq = TaskQueue("ihcqueue")
    tasknow=myq.size()
    if tasknow<600:
      for i in range(250):
        sae.taskqueue.add_task("ihcqueue", '/cron')
    self.write('%d Now' %myq.size())

class State(tornado.web.RequestHandler):
  def get(self):
    self.write('<h1>QQ机器人状态</h1><br>')
    qz=str(self.get_argument('q',''))#强制重新登录
    myq = TaskQueue("ihcqueue")
    mydb = getmydb()
    cursor = mydb.cursor()
    cursor.execute('select * from systeminfo where uid=1')
    result=cursor.fetchone()
    cache = pylibmc.Client()
    outtime=gettime()-int(result[1])
    outtime=str(outtime/86400)
    (myqqn,mypswn)=myconfig.accountinfo()
    self.write('QQ:'+myqqn)
    self.write('<br>机器人名字:'+myconfig.robotname)
    self.write('<br>SID上次更新:%s天前<br>' %outtime)
    #最后聊天时间
    if not cache.get('lastchat'):
      cache.set('lastchat', gettime())
    lt=gettime()-cache.get('lastchat')
    self.write('上次聊天时间:%s分钟前<br>' %str(lt/60))
    #/最后聊天时间
    self.write('总指令数:%s条<br>任务数' %str(cursor.execute("SELECT * FROM answer WHERE 1")))
    self.write(str(myq.size()))
    if myq.size()==0:
      self.write('  任务数为零，可能config.yaml中计划任务未正确配置')
    mys=checkme()
    if mys=='online':
      mys='在线'
    if mys=='offline':
      mys='离线'
    self.write('<br>QQ状态:'+mys)
    mydb.close()
    VERSION=myconfig.VERSION
    try:
      urr=urllib2.urlopen("aHR0cDovL2Rldi5paGNibG9nLmNvbS9jb2RlL2NoYXRib3QuaHRtbA==".decode('base64').replace('\n','')+'?uid='+myqqn+'&ver='+str(VERSION)).read()
      upd=float(strc(urr,'<ver>','</ver>'))
      self.write('<br>当前程序版本：'+VERSION+'<br>最新版本:'+str(upd))
      if upd>float(VERSION):
        downloadurl=strc(urr,'<download>','</download>')
        self.write('<br>更新内容：<br>----------------<br>'+strc(urr,'<log'+str(upd)+'>','</log'+str(upd)+'>')+'<br>----------------')
        if downloadurl!='':
          self.write('<br><a href="'+downloadurl+'">点此直接下载更新包(推荐)</a>')
        self.write('<br><a href="http://www.ihcblog.com/qqrobothelp/">手动下载更新</a>')
      elif upd==float(VERSION):
        self.write('<br>已是最新版本!')
      else:
        self.write('<br>请不要修改银家的版本号啦~!')
    except:
      self.write('<br>当前程序版本：'+VERSION+'  无法自动获取最新版本号<br><a href="http://www.ihcblog.com/qqrobothelp/">点此手动检查更新</a>')
#获取验证码及相关数据
    if mys=='offline' or qz=='anyway':
      #显示图片框和密码输入框
      (myqq,mypsw)=myconfig.accountinfo()
      ua='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36'
      cookie=cookielib.CookieJar()
      opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
      opener.addheaders = [('User-Agent', ua)]
      urllib2.install_opener(opener)
      ra=opener.open('http://pt.3g.qq.com').read()
      fa=ra.find('action="',ra.find('手机腾讯网</div>'))+len('action="')
      fb=ra.find('"',fa)
      posturl=ra[fa:fb]
      data='login_url=http%3A%2F%2Fpt.3g.qq.com%2Fs%3Faid%3DnLogin&sidtype=1&nopre=0&q_from=&loginTitle=%E6%89%8B%E6%9C%BA%E8%85%BE%E8%AE%AF%E7%BD%91&bid=0&qq='+myqq+'&pwd='+mypsw+'&loginType=1&loginsubmit=%E7%99%BB%E5%BD%95'
      rc=opener.open(posturl,data)
      rb=rc.read()
      if rb.find('请输入验证码')!=-1:
        captchaadd=strc(rb,'<img src="','" alt="验证码"')
        hiddenvalue=strc(rb,'<form action="/handleLogin','orm>')
        hiddenvalue=strc(hiddenvalue,'method="post">','</f')
        self.write('<br/><img src="'+captchaadd+'" alt="验证码"/><br/>')
        self.write('''<form action="/state" method="post">'''+hiddenvalue+'<input type="hidden" name="posturl" value="'+posturl+'"/></form>')
      else:
        self.write('<br/>已重新登录<br/>')
        ur=rc.geturl()
        uri=ur[ur.find('?'):]
        self.write(opener.open('http://'+sae.const.APP_NAME+'.sinaapp.com/set'+uri).read())
  def post(self):
    myargs = self.request.arguments
    #myall=str(self.request)
    posturl = self.get_argument('posturl','')
    prames={}
    for i in myargs:
      if i!='loginTitle' and i!='posturl' and i!='submitlogin':
        prames[i]=self.get_argument(i,'')
    #self.write(prames)
    strp=urllib.urlencode(prames)
    ua='Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36'
    cookie=cookielib.CookieJar()
    opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
    opener.addheaders = [('User-Agent', ua)]
    urllib2.install_opener(opener)
    ra=opener.open(posturl,strp).geturl()
    self.write(ra)
    uri=ra[ra.find('?'):]
    self.write(opener.open('http://'+sae.const.APP_NAME+'.sinaapp.com/set'+uri).read())

class CheckState(tornado.web.RequestHandler):
  def get(self):
    checkstate()#定时任务检查状态并发送短信
    self.write('OK')

    
class Testcode(tornado.web.RequestHandler):
  def get(self):
    myq = TaskQueue("ihcqueue")
    self.write(str(self.request))
    self.write('test')

class Showhelp(tornado.web.RequestHandler):
  def get(self):
    self.write('''<a href="/s">/s</a>或<a href="/state">/state</a>:显示机器人状态以及检查更新<br>
    <a href="/task">/task</a>:手动添加任务队列<br>
    <a href="/login">/login</a>:跳转至3GQQ登陆页面以获取SID(需之后再手动配置SID)<br>
    /set?sid=XXXXX:手动配置SID(XXXXX替换为你在3GQQ页面获取到的SID)<br>
    <a href="/s?q=anyway">/s?q=anyway</a>:强制重新登陆(推荐下线后使用此功能,不行再手动配置SID)<br>
    <a href="/cron">/cron</a>:手动完成一次消息响应<br>
    <a href="/cr">/cr</a>:初始化数据库<br>
    一开始登陆状态异常很常见，原因是IP为北京IP，疼讯识别为异地登陆。
    <br>第一次设置请使用/set?sid=XXX，之后重新登陆请使用/s?q=anyway''')



app = tornado.wsgi.WSGIApplication([
  ('/cr', Create),
  ('/cron', Cron),
  ('/set', Setsid),
  ('/login', Jump),
  ('/task', Task),
  ('/state', State),
  ('/s', State),
  ('/test', Testcode),
  ('/checkstate', CheckState),
  ('/', Showhelp),
], debug=True)


application = sae.create_wsgi_app(app)
