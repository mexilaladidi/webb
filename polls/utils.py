from .models import OpenNum, UserInfo, BetOrder, InvitionCode
from .logutil import *
from .enums import *
import random, datetime, math
from django.utils import timezone

def CalUser(UserName):
	TotalBuy = 0
	TotalWon = 0
	Orders = BetOrder.objects.filter(username = UserName, hascount = True)
	for v in Orders:
		TotalBuy = TotalBuy + v.totalmoney
		TotalWon = TotalWon + v.wonmoney
		if v.rebate != "":
			num, money = v.rebate.split(":")
			money = float(money)
			TotalWon = TotalWon + money
	print(TotalBuy, TotalWon)

def Consume(UserName, totalmoney):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return UserData.MoneyChange(-totalmoney, MoneyReason.buy)
	except Exception as e:
		LogErr("Consume Err"+str(e))

def CanOrder():
	try:
		HasNewOneOpen = OpenNum.objects.filter(result = "").order_by('vol')[0].HasOpenYet()
		return not HasNewOneOpen
	except:
		return False

def GetVol():
	try:
		obj = OpenNum.objects.filter(result = "").order_by('vol')[0]
		return obj.vol
	except:
		return -1

def GetVolAndTime():
	try:
		obj = OpenNum.objects.filter(result = "").order_by('vol')[0]
		return obj.vol, obj.opentime
	except:
		return -1, -1

def GetLastOpenVol():
	try:
		Vol = OpenNum.objects.all().exclude(result = "").order_by('-vol')[0].vol
		return Vol
	except:
		return -1

def GetUserMoney(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return UserData.money + UserData.giftmoney
	except Exception as e:
		LogErr("GetUserMoney Err" + e)
		return -1

def GetUserCanUseMoney(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return UserData.money + UserData.giftmoney + UserData.credit
	except Exception as e:
		LogErr("GetUserCanUseMoney Err" + e)
		return -1

def GetUserGroup(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return UserData.group
	except Exception as e:
		LogErr("GetUserGroup Err" + e)
		return -1

def GetDeposit(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return max(UserData.money, 0)
	except Exception as e:
		LogErr("GetDeposit Err" + e)
		return -1

def GetConsume(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return max(UserData.totalbuy, 0)
	except Exception as e:
		LogErr("GetConsume Err" + e)
		return -1

def GetCredit(UserName):
	try:
		UserData = UserInfo.objects.filter(username = UserName)[0]
		return max(UserData.credit, 0)
	except Exception as e:
		LogErr("GetUserMoney Err" + e)
		return -1


animal = ['鸡', '猴','羊','马','蛇','龙','兔','虎','牛','鼠','猪','狗',]	
def GetAnimalName(num):
	global animal
	return animal[num%len(animal)]

def LogErr(s):
	print(s)

def InvitionCodeValid(code, username = None):
	try:
		obj = InvitionCode.objects.filter(code = code)[0]
		if obj.IsUsed():
			return False, 0, 0
		else:
			if username != None:
				obj.Use(username)
			return True, obj.level, obj.giftmoney, obj.credit, obj.group
	except Exception as err:
		LogErr(err)
		return False, 0
g_OrderName = ['特码', '特码单双', '特码6肖', '特码肖', '特码大小数', '平特肖']
def GetOrdertypeName(ordertype):
	global g_OrderName
	return g_OrderName[ordertype]

def GetZeroNum(s):
	if len(s) == 1:
		return '0'+s
	else:
		return s

def IsCountFail(lastTime):
	timepass = timezone.now() - lastTime
	totalseconds = timepass.days*86400+timepass.seconds
	if totalseconds < ENUM.LoginLockSeconds:
		return True
	else:
		return False

def GetUnlockTime(lastTime):
	timepass = timezone.now() - lastTime
	totalseconds = timepass.days*86400+timepass.seconds
	return math.ceil((ENUM.LoginLockSeconds - totalseconds)/60)

def IsLock(UserData):
	timepass = timezone.now() - UserData.loginfailtime
	totalseconds = timepass.days*86400+timepass.seconds

	if UserData.loginfailcount >= ENUM.LoginLockCount and totalseconds < ENUM.LoginLockSeconds:
		return True
	else:
		return False

def Risk(bet = None, vol = None, runtimes = 10000):
	addmoney = None
	result = {}
	subtract = {}
	for i in range(1,50):
		result[i] = 0.0
		subtract[i] = 0
	if bet == None:
		if vol == None:
			vol = GetVol()
		orders = BetOrder.objects.filter(vol = vol)
		addmoney = 0
		for v in orders:
			if v.ordertype == 0:
				addmoney = addmoney + v.totalmoney*0.9
				for tempstr in v.nums.split(','):
					num, money = tempstr.split(':')
					num = int(num)
					money = int(money)
					result[num] = result[num] + money
					subtract[num] = subtract[num] + money
			if v.ordertype == 1:
				addmoney = addmoney + v.totalmoney*0.97
				for tempstr in v.nums.split(','):
					num, money = tempstr.split(':')
					num = int(num)
					money = int(money)
					subtractMoney = money
					money = money * 0.8 / 40
					if num == 1:
						for i in range(1,50,2):
							result[i] = result[i] + money 
							subtract[i] = subtract[i] + subtractMoney
					else:
						for i in range(2,49,2):
							result[i] = result[i] + money
							subtract[i] = subtract[i] + subtractMoney
			if v.ordertype == 2:
				addmoney = addmoney + v.totalmoney*0.97
				i = 0
				money = 0
				findMoney = 0
				for tempstr in v.nums.split(','):
					i = i + 1
					if i < 7:
						if int(tempstr) == 1:
							findMoney = 1
						continue
					money = int(tempstr)
					money = money *0.8 /40
				i = 0
				for tempstr in v.nums.split(','):
					i = i + 1
					if i < 7:
						for j in range(int(tempstr), 49, 12):
							result[j] = result[j] + money
							subtract[j] = subtract[j] + v.totalmoney
			if v.ordertype == 3:
				addmoney = addmoney + v.totalmoney*0.97
				for tempstr in v.nums.split(','):
					num, money = tempstr.split(':')
					num = int(num)
					findMoney = 0
					if num == 1:
						findMoney = 1
					money = int(money)
					subtractMoney = money
					money = money/4*(4/(4+findMoney))
					for j in range(num, 49, 12):
						result[j] = result[j] + money
						subtract[j] = subtract[j] + subtractMoney
			if v.ordertype == 4:
				addmoney = addmoney + v.totalmoney*0.97
				for tempstr in v.nums.split(','):
					num, money = tempstr.split(':')
					num = int(num)
					money = int(money)
					subtractMoney = money
					money = money*0.8/40
					if num == 1:
						for j in range(1,25):
							result[j] = result[j] + money
							subtract[j] = subtract[j] + subtractMoney
					else:
						for j in range(25,50):
							result[j] = result[j] + money
							subtract[j] = subtract[j] + subtractMoney
		bet = {}
		for v in result.items():
			bet[v[0]] = round(v[1]+0.0001, 2)
	totalmoney = 0
	if addmoney != None:
		totalmoney = addmoney
	else:
		for v in bet.values():
			totalmoney = totalmoney + v
	winmoney = []
	startMoney = 120000
	losstime = 0
	for i in range(1, runtimes):
		money = startMoney
		for k in range(1, 152):
			j = random.randint(1,49)
			money = money + totalmoney
			money = money - bet.get(j)*40 - subtract.get(j)
			if money <= 0:
				losstime = losstime + 1
				break
		winmoney.append(money)
	winmoney = sorted(winmoney)
	for i in range(0, len(winmoney)):
		if winmoney[i] > startMoney-1000:
			return bet, i/runtimes
	return bet, 100

	# print("losstime", losstime)
	# for i in range(1,100):
	# 	print(i , winmoney[i*int(runtimes/100)])
		



