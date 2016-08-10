from django.db import models
from django.utils import timezone

class UserInfo(models.Model):
	username = models.CharField(max_length=20, verbose_name = "用户名")
	password = models.CharField(max_length=20, verbose_name = "密码")
	level = models.IntegerField(default=0, verbose_name = "级别")
	money = models.FloatField(default=0.0, verbose_name = "可修改账户余额")
	truemoney = models.FloatField(default=0.0, verbose_name = "当前账户余额")
	profit = models.FloatField(default=0.0, verbose_name = "反水")
	HasCalTrueMoney = False
	def __str__(self):
		return self.username

	def GetBetOneProfit(self):
		return 41

	def CalTrueMoney(self):
		from .utils import GetLastOpenVol
		global CountDelayVol
		LastVol = GetLastOpenVol()
		truemoney = self.money
		for vol in range(LastVol-CountDelayVol+1, LastVol+1):
			OpenResult = OpenNum.objects.filter(vol = vol)[0].result
			for order in BetOneOrder.objects.filter(vol = vol, username = self.username):
				truemoney = truemoney + self.GetBetOneProfit() * order.GetWinCount(OpenResult) + round(order.totalmoney * self.profit, 2)
		self.truemoney = truemoney
		self.HasCalTrueMoney = True

	def save(self, *args, **kwargs):
		if not self.HasCalTrueMoney:
			self.CalTrueMoney()
		super(UserInfo, self).save(*args, **kwargs)

class BaseOrder(models.Model):
	username = models.CharField(max_length=20)
	vol = models.IntegerField(default=0)
	hascount = models.BooleanField(default = False)
	ordertime = models.DateTimeField(default = timezone.now)
	totalmoney = models.IntegerField(default=0)

	class meta:
		abstract = True


class BetOneOrder(BaseOrder):
	nums = models.CharField(max_length=4096, default = "")

	def count(self, result):
		if self.hascount == True:
			return
		else:
			self.hascount = True
			self.save()
			UserData = UserInfo.objects.filter(username = self.username)[0]
			UserData.money = UserData.money + UserData.GetBetOneProfit() * self.GetWinCount(result) + round(UserData.profit * self.totalmoney, 2)
			UserData.save()

	def GetWinCount(self, result):
		for v in self.nums.split(","):
			num, money = v.split(':')
			num = int(num)
			if num == result:
				return int(money)
		return 0

CountDelayVol = 2
class OpenNum(models.Model):
	vol = models.IntegerField(default=0)
	result = models.IntegerField(default=0)
	opentime = models.DateTimeField(default = timezone.now)

	class Meta:
		ordering = ["-vol"]

	def __str__(self):
		return str(self.vol)+"期"

	def save(self, *args, **kwargs):
		super(OpenNum, self).save(*args, **kwargs)
		global CountDelayVol
		CountResult = OpenNum.objects.filter(vol = self.vol-CountDelayVol)[0].result

		for order in BetOneOrder.objects.filter(vol = self.vol - CountDelayVol, hascount = False):
			order.count(CountResult)

		for UserData in UserInfo.objects.all():
			UserData.CalTrueMoney()
			UserData.save()


	def HasOpenYet(self):
		return self.opentime <= timezone.now()
