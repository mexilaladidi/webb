class OrderType():
	betone = 0
	oddeven = 1
	animal6 = 2
	animal = 3
	bigsmall = 4
	normalanimal = 5
	count = 6
	def oddstips(self, ordertype):
		if ordertype == self.animal:
			return r"猴肖100赔900"
		elif ordertype == self.normalanimal:
			return r"猴肖100赔185"

class BillType():
	TYPE = (
		(0, "充值"),
		(1, "提现"),
		(2, "给他人转账"),
		(3, "他人给你转账"),
		)
	charge = 0
	deposit = 1
	transferto = 2
	fromtransfer = 3
		

def GetProfitByLevel(level):
	if level == 0:
		return '0:41,1:1.80,2:1.80,3:11;1:9,4:1.80,5:2;1:1.85'
	elif level == 1:
		return '0:42,1:1.83,2:1.83,3:11.25;1:9,4:1.83,5:2;1:1.85'
	elif level == 2:
		return '0:41,1:1.80,2:1.80,3:11;1:9,4:1.80,5:2;1:1.85'
	elif level == 3:
		return '0:46,1:1.90,2:1.90,3:11;1:9,4:1.90,5:2;1:1.85'
	elif level == 4:
		return '0:44,1:1.85,2:1.85,3:11;1:9,4:1.85,5:2;1:1.85'
	else:
		return ''

def GetRebateProfitByLevel(level):
	if level == 0:
		return '0:0.05,1:0.015,2:0.015,3:0.01,4:0.015,5:0.01'
	elif level == 1:
		return '0:0.07,1:0.02,2:0.02,3:0.015,4:0.02,5:0.015'
	elif level == 2:
		return '0:0.1'
	elif level == 4:
		return '0:0.05,1:0.02,2:0.02,3:0.02,4:0.02,5:0.01'
	else:
		return ''

def GetBetNameByType(ordertype):
	if ordertype == OrderType.betone:
		return '特码'
	elif ordertype == OrderType.oddeven:
		return '特码单双'
	elif ordertype == OrderType.animal6:
		return '特码六肖'
	elif ordertype == OrderType.animal:
		return '特码一肖'
	elif ordertype == OrderType.bigsmall:
		return '特码大小'
	elif ordertype == OrderType.normalanimal:
		return '平特码一肖'
		

class MoneyReason():
	win = 0
	deleteorder = 1
	buy = 2
	rebate = 3
	returnrebate = 4
	recharge = 5
	deposit = 6
	transferto = 7
	fromtransfer = 8
	returndeposit = 9
	newinvite = 10

class DepositStatus:
	Status = ((1, '审核中'), (2, '处理中'), (3, '成功'), (4, '失败'))
	applystatus = 1
	def GetDepositStr(index):
		return DepositStatus.Status[index-1][1]

class ENUM():
	InviteGiftMoney = 10
	InviteLevel = 4
	InviteConsumeMoney = 500
	LoginLockCount = 5
	LoginLockSeconds = 3600