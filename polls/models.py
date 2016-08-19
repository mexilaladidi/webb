from django.db import models
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .enums import OrderType, GetProfitByLevel, GetRebateProfitByLevel, MoneyReason, BillType, DepositStatus
from .logutil import LogErr
import random
from .lock import g_lock
import re

class UserInfo(models.Model):
	username = models.CharField(max_length=20, verbose_name = "用户名")
	password = models.CharField(max_length=20, verbose_name = "密码")
	bindcard = models.CharField(max_length=512, verbose_name = "银行卡",default = "", blank = True)
	level = models.IntegerField(default=0, verbose_name = "级别")
	money = models.FloatField(default=0.0, verbose_name = "账户余额")
	credit = models.FloatField(default=0.0, verbose_name = "可透支额度")
	giftmoney = models.FloatField(default=0.0, verbose_name = "赠金")
	group = models.IntegerField(default=0, verbose_name = "组别")
	profit = models.CharField(max_length=128, verbose_name = "profit", blank = True, default = '')
	rebateprofit = models.CharField(max_length=128, verbose_name = "rebateprofit", blank = True, default = '')
	profitusername = models.CharField(max_length=20, verbose_name = "提成至用户", default = "", blank = True)
	totalbuy = models.IntegerField(default=0, verbose_name = "已消费")

	loginfailcount = models.IntegerField(default=0, verbose_name = "登录失败次数")
	loginfailtime = models.DateTimeField(default = timezone.now, verbose_name = "上次失败时间")


	def __str__(self):
		return self.username

	def GetProfit(self, ordertype):
		for v in self.profit.split(','):
			profitcfg = v.split(';')
			bet_type, betprofit = profitcfg[0].split(':')
			bet_type = int(bet_type)
			if bet_type == ordertype:
				profitmap = {0:float(betprofit)}
				for i in range(1, len(profitcfg)):
					tag, pft = profitcfg[i].split(':') 
					profitmap[int(tag)] = float(pft)
				return profitmap
		return 0

	def GetRebateProfit(self, ordertype):
		for v in self.rebateprofit.split(','):
			bet_type, rebatprofit = v.split(':')
			bet_type = int(bet_type)
			if bet_type == ordertype:
				return float(rebatprofit)
		return 0

	def ConutRebate(self, ordertype, money):
		try:
			profitUser = UserInfo.objects.filter(username = self.profitusername)[0]
			RebateMoney = self.GetRebateProfit(ordertype) * money
			RebateMoney = round(RebateMoney+0.0001, 2)
			profitUser.MoneyChange(RebateMoney, MoneyReason.rebate)
			try:
				invitioncode = InvitionCode.objects.get(username = self.username)
				invitioncode.rebate = invitioncode.rebate + RebateMoney
				invitioncode.save() 
			except:
				pass
			return self.profitusername, RebateMoney
		except Exception as e:
			LogErr("[Model Error]"+str(e))
			return "", 0

	def RecoveryRebate(self, ordertype, money):
		try:
			profitUser = UserInfo.objects.filter(username = self.profitusername)[0]
			RebateMoney = self.GetRebateProfit(ordertype) * money
			RebateMoney = round(RebateMoney+0.0001, 2)
			profitUser.MoneyChange(-RebateMoney, MoneyReason.returnrebate)
			try:
				invitioncode = InvitionCode.objects.get(username = self.username)
				invitioncode.rebate = invitioncode.rebate - RebateMoney
				invitioncode.save() 
			except:
				pass
		except Exception as e:
			LogErr("[Model Error]"+str(e))

	def MoneyChange(self, money, reason):
		if money < 0:
			if money + self.giftmoney < 0:
				self.giftmoney = 0
				money = money + self.giftmoney
				self.money = UserInfo.objects.get(id = self.id).money + money
			else:
				self.giftmoney = self.giftmoney + money  
		else:
			self.money = UserInfo.objects.get(id = self.id).money + money
		if self.money + self.credit < 0:
			LogErr("money not enough")
			return False
		self.save()
		return True

	def InitProfit(self):
		self.profit = GetProfitByLevel(self.level)
		self.rebateprofit = GetRebateProfitByLevel(self.level)

	def save(self, *args, **kwargs):
		self.money = round(self.money+0.0001, 2)
		super(UserInfo, self).save(*args, **kwargs)

class BetOrder(models.Model):
	username = models.CharField(max_length=20)
	vol = models.IntegerField(default=0)
	wonmoney = models.FloatField(default = 0)
	ordertime = models.DateTimeField(default = timezone.now)
	totalmoney = models.IntegerField(default=0)
	ordertype = models.IntegerField(default=0)
	hascount = models.BooleanField(default=False)
	nums = models.CharField(max_length=512, default = "")
	rebate = models.CharField(max_length=32, default = "", blank = True)
	
	def Count(self, result):
		WonMoney = 0
		UserData = UserInfo.objects.filter(username = self.username)[0]
		moneycount = self.GetWinCount(self.ordertype, result)
		if len(moneycount) > 0:
			ProfitCfg = UserData.GetProfit(self.ordertype)
			if ProfitCfg != 0:
				for item in moneycount.items():
					actor = ProfitCfg.get(item[0])
					if actor == None:
						WonMoney = WonMoney + ProfitCfg[0] * item[1]
					else:
						WonMoney = WonMoney + actor * item[1]
		UserData.MoneyChange(WonMoney, MoneyReason.win)
		UserData.totalbuy = UserData.totalbuy + self.totalmoney
		UserData.save()
		profitName, rebateMoney = UserData.ConutRebate(self.ordertype, self.totalmoney)
		self.rebate = profitName+':'+str(rebateMoney)
		self.hascount = True
		self.wonmoney = WonMoney
		self.save()

	def Recovery(self):
		if self.hascount:
			self.hascount = False
			UserData = UserInfo.objects.filter(username = self.username)[0]
			UserData.money = UserData.money - self.wonmoney
			UserData.totalbuy = UserData.totalbuy - self.totalmoney
			UserData.save()
			UserData.RecoveryRebate(self.ordertype, self.totalmoney)
			self.rebate = ""
			self.save()

	def GetWinCount(self, ordertype, result):
		returnmoney = {}
		if ordertype == OrderType.betone:
			for v in self.nums.split(","):
				num, money = v.split(':')
				num = int(num)
				if num == result[7]:
					returnmoney[0] = int(money)
					break
		elif ordertype == OrderType.oddeven:
			for v in self.nums.split(","):
				num, money = v.split(':')
				num = int(num)
				if num % 2 == result[7] % 2:
					returnmoney[0] = int(money)
					break
		elif ordertype == OrderType.animal6:
			i = 0
			bingo = False
			for v in self.nums.split(","):
				i = i + 1
				if i == 7 and bingo:
					returnmoney[0] = int(v)
					break
				elif int(v) % 12 == result[7] % 12:
					bingo = True
		elif ordertype == OrderType.animal:
			for v in self.nums.split(','):
				num, money = v.split(':')
				if int(num) % 12 == result[7] % 12:
					returnmoney[int(num) % 12] = int(money)
		elif ordertype == OrderType.bigsmall:
			for v in self.nums.split(','):
				num, money = v.split(':')
				if num == "1" and result[7] < 25:
					returnmoney[1] = int(money)
				if num == "2" and result[7] >= 25:
					returnmoney[2] = int(money)
		elif ordertype == OrderType.normalanimal:
			for v in self.nums.split(','):
				num, money = v.split(':')
				haswinanimal = set()
				for i in range(1,8):
					winanimal = result[i] % 12
					if winanimal not in haswinanimal:
						haswinanimal.add(winanimal)
						if int(num) % 12 == winanimal:
							returnmoney[winanimal] = int(money)
		return returnmoney

	def delete(self, *args, **kwargs):
		try:
			if not OpenNum.objects.filter(vol = self.vol)[0].HasOpenYet():
				UserInfo.objects.filter(username = self.username)[0].MoneyChange(self.totalmoney, MoneyReason.deleteorder)
				super(BetOrder, self).delete(*args, **kwargs)
				return True
			else:
				return False
		except Exception as e:
			LogErr("delete order err" + str(e))

class OpenNum(models.Model):
	BET_TYPE = (
		(0, "liuhe"),
		)
	bettype = models.IntegerField(default=0, choices = BET_TYPE) 
	vol = models.IntegerField(default=0)
	result = models.CharField(max_length=32, default = "", blank = True)
	opentime = models.DateTimeField(default = timezone.now)

	class Meta:
		ordering = ["-vol"]

	def __str__(self):
		return str(self.vol)+"期"

	def save(self, *args, **kwargs):
		try:
			g_lock.acquire()
			result = [0]
			resultStr = ""
			if self.result != "":
				for v in re.split("\D+", self.result):
					result.append(int(v))
					resultStr = resultStr + str(int(v))+','
			resultStr = resultStr[:-1]
			self.result = resultStr
			super(OpenNum, self).save(*args, **kwargs)
			for order in BetOrder.objects.filter(vol = self.vol):
				if len(result) == 8:
					order.Recovery()
					order.Count(result)
				else:
					order.Recovery()
		except Exception as e:
			LogErr(str(e))
		finally:
			g_lock.release()
		if len(result) == 8:
			dayOfWeek = timezone.localtime(self.opentime).weekday()+1
			nextOpen = OpenNum.objects.filter(vol = self.vol+1)
			if len(nextOpen) == 0:
				nextOpen = OpenNum()
				nextOpen.bettype = self.bettype
				nextOpen.vol = self.vol+1
				nextOpen.result = ""
				if dayOfWeek == 2 or dayOfWeek == 4 or dayOfWeek == 7:
					nextOpen.opentime = self.opentime+timedelta(days=2)
				elif dayOfWeek == 6:
					nextOpen.opentime = self.opentime+timedelta(days=3)
				else:
					nextOpen.opentime = self.opentime+timedelta(days=2)
				nextOpen.save()

	def HasOpenYet(self):
		return self.opentime <= timezone.now()

class InvitionCode(models.Model):
	bindusername = models.CharField(max_length=20, verbose_name = "利益用户", blank = True, default = "")
	username = models.CharField(max_length=20, verbose_name = "用户名", blank = True, default = "")
	code = models.CharField(max_length=20, verbose_name = "邀请码", blank = True, default = "")
	used = models.BooleanField(default = False)
	level = models.IntegerField(default = 0)
	giftmoney = models.IntegerField(default = 0)
	credit = models.IntegerField(default = 0)
	group = models.IntegerField(default=0, verbose_name = "组别")
	rebate = models.FloatField(default=0, verbose_name = "已获得提成")
	time = models.DateTimeField(default = timezone.now)

	def IsUsed(self):
		return self.used == True

	def Use(self, username):
		try:
			user = UserInfo.objects.filter(username = username)[0]
			if self.bindusername == "":
				user.profitusername = user.username
			else:
				user.profitusername = self.bindusername
			user.save()
			self.username = username
			self.used = True
			self.save()
			return True
		except:
			LogErr("use InvitionCode err")
			return False

	def __str__(self):
		return self.code

	def save(self, *args, **kwargs):
		if self.used == False:
			if self.code == "" or len(InvitionCode.objects.filter(code = self.code).exclude(id = self.id)) != 0:
				trytimes = 1
				while trytimes < 200:
					randomcode = ""
					for i in range(1, 7):
						randomcode = randomcode + random.choice('0123456789')
					if len(InvitionCode.objects.filter(code = randomcode)) == 0:
						self.code = randomcode
						break
					trytimes = trytimes + 1
				if trytimes == 200:
					self.code = ''
		super(InvitionCode, self).save(*args, **kwargs)

class Bill(models.Model):
	username = models.CharField(max_length=20, verbose_name = "用户名")
	money = models.FloatField(default = 0)
	time = models.DateTimeField(default = timezone.now)
	billtype =  models.IntegerField(default=0, choices = BillType.TYPE)
	operateuser = models.CharField(max_length=20, verbose_name = "操作用户")

	def __str__(self):
		return self.username

class Deposit(models.Model):
	username = models.CharField(max_length=20, verbose_name = "用户名")
	money = models.FloatField(default = 0)
	time = models.DateTimeField(default = timezone.now)
	status = models.IntegerField(default=0, choices = DepositStatus.Status)
	bankcard = models.CharField(max_length=128, verbose_name = "银行卡信息")
	hasreturn = models.BooleanField(default = False)

	def save(self, *args, **kwargs):
		if self.hasreturn == False and self.status == 4:
			self.hasreturn = True
			try:
				User = UserInfo.objects.get(username = self.username)
				User.MoneyChange(self.money, MoneyReason.returndeposit)
			except:
				pass
		super(Deposit, self).save(*args, **kwargs)


	def delete(self, *args, **kwargs):
		super(Deposit, self).delete(*args, **kwargs)
		try:
			User = UserInfo.objects.get(username = self.username)
			User.MoneyChange(self.money, MoneyReason.returndeposit)
		except:
			pass

