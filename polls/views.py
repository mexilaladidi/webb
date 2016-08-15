from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import timezone

from .models import OpenNum, UserInfo, BetOrder, Bill, Deposit, InvitionCode
from django.template import loader
from django.http import Http404
from django.shortcuts import render, redirect
from .forms import SignupForm, LoginForm, BetOneForm, OddEvenForm, AnimalForm, Animal6Form, BigSmallForm, NormalAnimalForm, UserMgrForm, BuyCountForm, TransferForm, DepositForm
from .utils import *
from .enums import OrderType, GetProfitByLevel, GetRebateProfitByLevel,GetBetNameByType, MoneyReason, BillType, DepositStatus, ENUM
from .lock import g_lock

def tips(request, tips_msg, back_url):
	username = None
	try:
		username = request.session['username']
	except KeyError:
		pass
	return render(request, r'polls/tips.html', {'tips':tips_msg, 'backurl':back_url, 'username':username})

def index(request):
	username = None
	try:
		username = request.session['username']
	except KeyError:
		pass
	profits = None
	if username == None:
		profits = GetProfitByLevel(4)
	else:
		profits = UserInfo.objects.get(username = username).profit
	profit_map = {}
	for v in profits.split(','):
		ordertype, pft = v.split(';')[0].split(':')
		profit_map[int(ordertype)] = float(pft)
	BetName = []
	if username:
		for ordertype in range(0,6):
			data = {}
			data['name'] = GetBetNameByType(ordertype) + r'  100赔'
			data['type'] = ordertype
			data['money'] = int(profit_map[ordertype] * 100)
			BetName.append(data)
			

	return render(request, r'polls/index.html', {'username':username, 'betlist':BetName})

def signup(request):
	if request.method == 'POST':
		form = SignupForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['UserName']
			password = form.cleaned_data['PassWord']
			invitioncode = form.cleaned_data['InvitionCode']
			Exist, level, giftmoney, credit, group = InvitionCodeValid(invitioncode)
			if Exist:
				queryset = UserInfo.objects.filter(username = username)
				if len(queryset) != 0:
					return render(request, r'polls/signup.html', {'signupform': SignupForm(), 'errmsg':'用户名存在'})
				else:
					NewUser = UserInfo(username = username, password = password, money = giftmoney, level = level, credit = credit, group = group)
					NewUser.InitProfit()
					NewUser.save()
					InvitionCodeValid(invitioncode, username)
					request.session['username'] = username
					return redirect('/')
			else:
				return render(request, r'polls/signup.html', {'signupform': form, 'errmsg':'邀请码不存在'})

		else:
			return render(request, r'polls/signup.html', {'signupform': SignupForm(), 'errmsg':'输入不合法'})
	else:		
		return render(request, r'polls/signup.html', {'signupform': SignupForm(), 'shit':'shit'})

def login(request):
	if request.method == 'POST':
		form = LoginForm(request.POST)
		if form.is_valid():
			username = form.cleaned_data['UserName']
			password = form.cleaned_data['PassWord']
			queryset = UserInfo.objects.filter(username = username)
			if len(queryset) != 0:
				UserData = queryset[0]
				if not IsLock(UserData) and UserData.password == password:
					request.session['username'] = username
					return redirect('/')
				else:
					try:
						g_lock.acquire()
						if IsCountFail(UserData.loginfailtime):
							if  UserData.loginfailcount >= ENUM.LoginLockCount:
								minute = str(GetUnlockTime(UserData.loginfailtime))
								return render(request, r'polls/login.html', {'loginform': LoginForm(), 'errmsg':r'账户已被锁定，请'+minute+r'分钟后再试'})
							else:
								UserData.loginfailcount = UserData.loginfailcount + 1
								UserData.loginfailtime = timezone.now()
								UserData.save()
						else:
							UserData.loginfailcount = 1
							UserData.loginfailtime = timezone.now()
							UserData.save()
					except:
						pass
					finally:
						g_lock.release()

		return render(request, r'polls/login.html', {'loginform': LoginForm(), 'errmsg':'用户名或密码错误'})
	else:
		return render(request, r'polls/login.html', {'loginform': LoginForm()})

def logout(request):
	try:
		del request.session['username']
	except KeyError:
		pass
	return redirect('/')


def CountPrice(ordertype, form):
	TotalPrice = 0
	if ordertype == OrderType.betone:
		for i in range (1, 50):
			price = int(form.cleaned_data['num'+str(i)])
			if price > 0:
				TotalPrice = TotalPrice + price
	elif ordertype == OrderType.oddeven:
		for i in range (1, 3):
			price = int(form.cleaned_data['num'+str(i)])
			if price > 0:
				TotalPrice = TotalPrice + price
	elif ordertype == OrderType.animal6:
		TotalPrice = int(form.cleaned_data['money'])
	elif ordertype == OrderType.animal:
		for i in range(1, 13):
			price = int(form.cleaned_data['num'+str(i)])
			TotalPrice = TotalPrice + price
	elif ordertype == OrderType.bigsmall:
		for i in range(1, 3):
			price = int(form.cleaned_data['num'+str(i)])
			TotalPrice = TotalPrice + price
	elif ordertype == OrderType.normalanimal:
		for i in range(1, 13):
			price = int(form.cleaned_data['num'+str(i)])
			TotalPrice = TotalPrice + price

	return TotalPrice

def CreateOrder(ordertype, username, forms, totalPrice):
	order = BetOrder(
		username = username,
		totalmoney = totalPrice,
		vol = GetVol(),
		ordertype = ordertype,
		)
	nums = ""
	if ordertype == OrderType.betone:
		buyMoney = []
		for i in range (1, 50):
			price = int(forms.cleaned_data['num'+str(i)])
			buyMoney.append(price)
		for i in range(0, 49):
			if buyMoney[i] > 0:
				nums = nums + str(i+1)+":"+str(buyMoney[i])+","
		nums = nums[:-1]
	elif ordertype == OrderType.oddeven:
		buyMoney = []
		for i in range (1, 3):
			price = int(forms.cleaned_data['num'+str(i)])
			buyMoney.append(price)
		for i in range(0, 2):
			if buyMoney[i] > 0:
				nums = nums + str(i+1)+":"+str(buyMoney[i])+","
		nums = nums[:-1]
	elif ordertype == OrderType.animal6:
		Count = 0
		for i in range(1, 13):
			if forms.cleaned_data['num'+str(i)]:
				Count = Count + 1
				nums = nums + str(i) + "," 
		if Count != 6:
			return False, "请选择六个"
		nums = nums + str(forms.cleaned_data['money'])
	elif ordertype == OrderType.animal:
		for i in range(1, 13):
			money = forms.cleaned_data['num'+str(i)]
			if money > 0:
				nums = nums + str(i)+":"+str(money)+","
		nums = nums[:-1]
	elif ordertype == OrderType.bigsmall:
		for i in range(1, 3):
			money = forms.cleaned_data['num'+str(i)]
			if money > 0:
				nums = nums + str(i)+":"+str(money)+","
		nums = nums[:-1]
	elif ordertype == OrderType.normalanimal:
		for i in range(1, 13):
			money = forms.cleaned_data['num'+str(i)]
			if money > 0:
				nums = nums + str(i)+":"+str(money)+","
		nums = nums[:-1]

	order.nums = nums
	order.save()
	return True, order

def GetFormByType(ordertype, parm = None):
	forms = None
	if ordertype == OrderType.betone:
		forms = BetOneForm
	elif ordertype == OrderType.oddeven:
		forms = OddEvenForm
	elif ordertype == OrderType.animal6:
		forms = Animal6Form
	elif ordertype == OrderType.animal:
		forms = AnimalForm
	elif ordertype == OrderType.bigsmall:
		forms = BigSmallForm
	elif ordertype == OrderType.normalanimal:
		forms = NormalAnimalForm

	if parm == None:
		return forms()
	else:
		return forms(parm)

def GetDisplayOrderInfo(Order):
	OrderContent = {}
	OrderContent["username"] = Order.username
	OrderContent["ordertime"] = Order.ordertime
	OrderContent["totalmoney"] = Order.totalmoney
	OrderContent["wonmoney"] = Order.wonmoney
	OrderContent["hascount"] = Order.hascount
	OrderContent["vol"] = Order.vol
	OrderContent["id"] = Order.id
	OrderContent["ordertypename"] = GetOrdertypeName(Order.ordertype)
	contentstr = ""
	if Order.ordertype == OrderType.betone:
		for v in Order.nums.split(","):
			num, money = v.split(':')
			if len(num) == 1:
				num = r'0'+num
			contentstr = contentstr + num+" = "+money+"元, "
		contentstr = contentstr[:-2]
	elif Order.ordertype == OrderType.oddeven:
		for v in Order.nums.split(","):
			num, money = v.split(':')
			num = int(num)
			if num % 2 == 1:
				contentstr = contentstr + "单数 = "+money+"元 "
			else:
				contentstr =  contentstr + "双数 = "+money+"元 "
	elif Order.ordertype == OrderType.animal6:
		i = 0
		for v in Order.nums.split(","):
			i = i + 1
			num = int(v)
			if i <= 6:
				contentstr = contentstr + GetAnimalName(num)+" "
			else:
				contentstr =  contentstr + v +"元"
	elif Order.ordertype == OrderType.bigsmall:
		for v in Order.nums.split(','):
			num, money = v.split(':')
			tempstr = "小数 = "
			if num == "2":
				tempstr = "大数 = "
			contentstr = contentstr + tempstr + money+"元  "
	elif Order.ordertype == OrderType.animal:
		for v in Order.nums.split(','):
			num, money = v.split(':')
			contentstr = contentstr + GetAnimalName(int(num))+money+"元  "
	elif Order.ordertype == OrderType.normalanimal:
		for v in Order.nums.split(','):
			num, money = v.split(':')
			contentstr = contentstr + GetAnimalName(int(num))+money+"元  "
	OrderContent["content"] = contentstr
	try:
		rebateName, rebateMoney = Order.rebate.split(":")
		if Order.username == rebateName:
			OrderContent["rebate"] = float(rebateMoney)
		OrderContent["rebatename"] = rebateName
		OrderContent["rebateforshow"] = rebateMoney

	except:
		pass
	return OrderContent

def betorder(request, ordertype):
	ordertype = int(ordertype)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')

	if request.method == 'POST':
		ErrTips = None
		forms = GetFormByType(ordertype, request.POST)
		g_lock.acquire()
		if forms.is_valid():
			buyMoney = []
			TotalPrice = CountPrice(ordertype, forms)
			if TotalPrice > 0:
				if CanOrder():
					if TotalPrice <= GetUserCanUseMoney(username):
						try:
							Succ, err = CreateOrder(ordertype, username, forms, TotalPrice)
							if Succ:
								neworder = err
								Consume(username, TotalPrice)
								g_lock.release()
								return render(request, r'polls/ordersuc.html', {'order': GetDisplayOrderInfo(neworder), 'username':username})
							else:
								ErrTips = err
						except Exception as err:
							ErrTips = r"下单失败"+str(err)
					else:
						ErrTips = r"余额不足"
				else:
					ErrTips = r"已封盘"
			else:
				ErrTips = r"请至少购买一块钱"
		else:
			ErrTips = r"订单有非法数据"	
		g_lock.release()
		if ErrTips != None:
			return tips(request, ErrTips, reverse('polls:betorder', kwargs={'ordertype':ordertype}))
	else:
		vol, opentime = GetVolAndTime()
		if vol == -1:
			return tips(request, "尚未开盘", reverse('polls:index'))
		elif opentime < timezone.now():
			return tips(request, "已封盘", reverse('polls:index'))
		forms = GetFormByType(ordertype)
		oddstips = OrderType().oddstips(ordertype)
		return render(request, r'polls/betorder.html', {'forms': forms, 'username':username, 'ordertype':ordertype, 'vol':vol, 'closetime':opentime, "oddstips":oddstips})


def myaccount(request, page):
	if page == None:
		page = 1
	else:
		page = int(page)
	username = None
	try:
		username = request.session['username']
	except:
		return tips(request, "请先登录", reverse('polls:index'))
	if page < 1:
		return tips(request, "错误参数", reverse('polls:myaccount'))

	OrderData = BetOrder.objects.filter(username = username).order_by('-ordertime')
	numPerPage = 10
	startIndex = (page-1) * numPerPage 
	endIndex = min(len(OrderData), page*numPerPage)
	if endIndex < startIndex:
		return tips(request, "错误参数", reverse('polls:myaccount'))
	OrderList = []
	for i in range(startIndex, endIndex):
		OrderList.append(GetDisplayOrderInfo(OrderData[i]))
	money = GetUserMoney(username)
	lastPage = False
	nextPage = False
	if page > 1:
		lastPage = page - 1
	if page*numPerPage < len(OrderData):
		nextPage = page + 1
	return render(request, r'polls/myaccount.html', {'money':money, 'orderlist':OrderList, 'username':username, 'lastpage':lastPage, 'nextpage':nextPage, 'hasorder':len(OrderList)>0})

def cancelorder(request, orderid):
	Success = False
	try:
		g_lock.acquire()
		Success = BetOrder.objects.filter(id = orderid)[0].delete()
	except:
		pass
	finally:
		g_lock.release()
	if Success:
		return tips(request, "取消成功", reverse('polls:myaccount', kwargs={'page':1}))
	else:
		return tips(request, "取消失败", reverse('polls:myaccount',kwargs={'page':1}))

def history(request, page):
	page = int(page)
	username = None
	try:
		username = request.session['username']
	except:
		return tips(request, "请先登录", reverse('polls:index'))
	history = OpenNum.objects.all().exclude(result = '').order_by('-vol')
	numPerPage = 15
	startIndex = (page-1) * numPerPage 
	endIndex = min(len(history), page*numPerPage)
	Infos = []
	for i in range(startIndex, endIndex):
		info = {}
		info['vol']= history[i].vol
		index = 0
		info['normal'] = ""
		for num in history[i].result.split(","):
			index = index + 1
			if index < 7:
				if len(num) == 1:
					num = '0'+num
				info['normal'] = info['normal'] + num + ", "
			else:
				info['special'] = GetZeroNum(num)+ '  ' + GetAnimalName(int(num))	
		info['normal'] = info['normal'][:-2]
		Infos.append(info)
	lastpage = None
	nextpage = None
	if page > 1:
		lastpage = page-1
	if len(history) > endIndex:
		nextpage = page+1
	return render(request, r'polls/history.html', {'result':Infos, 'username':username, 'lastpage':lastpage, 'nextpage':nextpage})

def usermgr(request):
	username = None
	try:
		username = request.session['username']
	except:
		return tips(request, "请先登录", reverse('polls:index'))
	GroupLevel = GetUserGroup(username)
	if GroupLevel <= 0:
		return tips(request, "无权打开", reverse('polls:index'))
	if request.method == 'POST':
		ErrTips = None
		forms = UserMgrForm(request.POST)
		if forms.is_valid():
			operationusername = forms.cleaned_data['UserName']
			UserData = None
			try:
				UserData = UserInfo.objects.get(username = operationusername)
				if GroupLevel == 1:
					print("shit")
					if UserData.profitusername != username or username == operationusername:
						ErrTips = "无权操作此用户"
			except:
				ErrTips = "没有此用户"
			if ErrTips == None:
				if GroupLevel >= 1:
					rechargeMoney = forms.cleaned_data['Recharge']
					depositMoney = forms.cleaned_data['Deposit']
					if rechargeMoney == 0 and depositMoney == 0 and GroupLevel == 1:
						pass
					elif rechargeMoney > 0:
						if UserData.MoneyChange(rechargeMoney, MoneyReason.recharge):
							newBill = Bill(username = operationusername, billtype = BillType.charge, operateuser = username, money = rechargeMoney)
							newBill.save()
							return tips(request, "充值成功", reverse('polls:usermgr'))
					elif depositMoney > 0:
						if UserData.MoneyChange( -depositMoney, MoneyReason.deposit):
							newBill = Bill(username = operationusername, billtype = BillType.deposit, operateuser = username, money = -depositMoney)
							newBill.save()
							return tips(request, "提现成功", reverse('polls:usermgr'))
						else: 
							ErrTips = "提现失败"
				elif GroupLevel >= 2:
					addCredit = forms.cleaned_data['AddCredit']
					decCredit = forms.cleaned_data['DecCredit']
					if addCredit == 0 and decCredit == 0 and GroupLevel == 2:
						pass
					elif addCredit > 0:
						UserData.credit = UserData.credit + addCredit
						UserData.save()
						return tips(request, "信用增加成功", reverse('polls:usermgr'))
					elif decCredit > 0:
						UserData.credit = UserData.credit - decCredit
						UserData.save()
						return tips(request, "信用降低成功", reverse('polls:usermgr'))
				# 表单为0的情况
				return render(request, r'polls/usermanager.html', {'forms':forms, 'username':username, 'operationusername':operationusername, 'money':GetDeposit(operationusername), 'credit':GetCredit(operationusername), 'group':GroupLevel})
		else:
			ErrTips = "输入错误"
		if ErrTips:
			return tips(request, ErrTips, reverse('polls:usermgr')) 
	else:
		return render(request, r'polls/usermanager.html', {'forms':UserMgrForm(), 'username':username, 'group':GroupLevel})


def riskmgr(request):
	username = None
	try:
		username = request.session['username']
	except:
		return tips(request, "无权打开", reverse('polls:index'))
	if username != '8190':
		return False
	if request.method == 'POST':
		forms = BuyCountForm(request.POST)
		if forms.is_valid():
			bet = {}
			for i in range(1, 50):
				bet[i] = forms.cleaned_data['num'+str(i)]
			bet, risk = Risk(bet)
		else:
			return tips(request, "输入错误", reverse('polls:riskmgr')) 

	else:
		bet, risk = Risk()
	risk = round(risk * 100, 1)
	formsdata = {}
	for v in bet.items():
		formsdata['num'+str(v[0])] = v[1]
	forms = BuyCountForm(formsdata)
	return render(request, r'polls/riskmgr.html', {'username':username, 'forms':forms, 'risk':risk})

def transfer(request, page = 1):
	page = int(page)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	if request.method == 'POST':
		forms = TransferForm(request.POST)
		if forms.is_valid():
			operationusername = forms.cleaned_data['UserName']
			if operationusername == username:
				ErrTips = "不能给自己转账"
			else:
				try:
					g_lock.acquire()
					UserData = UserInfo.objects.get(username = operationusername)
					MyData = UserInfo.objects.get(username = username)
					money = forms.cleaned_data['Money']
					if money == 0:
						ErrTips = "请输入至少一元"
					elif money > GetDeposit(username):
						ErrTips = "转账失败，余额不足"
					else:
						UserData.MoneyChange(money, MoneyReason.fromtransfer)
						MyData.MoneyChange(-money, MoneyReason.transferto)
						newBill = Bill(username = operationusername, billtype = BillType.fromtransfer, operateuser = username, money = money)
						newBill.save()
						newBill = Bill(username = username, billtype = BillType.transferto, operateuser = operationusername, money = money)
						newBill.save()
						return tips(request, "转账成功", reverse('polls:transfer',kwargs={'page':1}))
				except:
					ErrTips = "无此用户"
				finally:
					g_lock.release()
		else:
			ErrTips = "参数错误"
		return tips(request, ErrTips, reverse('polls:transfer',kwargs={'page':1}))
	else:
		Bills = Bill.objects.filter(username = username).order_by('-time')
		numPerPage = 10
		startIndex = (page-1) * numPerPage 
		endIndex = min(len(Bills), page*numPerPage)
		billsInfo = []
		lastpage = None
		nextpage = None
		if page > 1:
			lastpage = page-1
		if len(Bills) > endIndex:
			nextpage = page+1
		for i in range(startIndex, endIndex):
			info = {}
			info['time']= Bills[i].time
			if Bills[i].billtype == BillType.fromtransfer:
				info['money'] = "+"+str(Bills[i].money)
			elif Bills[i].billtype == BillType.transferto:
				info['money'] = "-"+str(Bills[i].money)
			info['name'] = Bills[i].operateuser
			billsInfo.append(info)

		return render(request, r'polls/transfer.html', {'username':username, 'forms':TransferForm(), 'hasbill':len(billsInfo)>0,'bills':billsInfo, 'money':GetDeposit(username), 'nextpage':nextpage, 'lastpage':lastpage})

def deposit(request, page = 1):
	page = int(page)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')

	if request.method == 'POST':
		forms = DepositForm(request.POST)
		if forms.is_valid():
			money = forms.cleaned_data['Money']
			bankcard = forms.cleaned_data['BankCard']
			carduser = forms.cleaned_data['Name']
			if money > GetDeposit(username):
				ErrTips = "余额不足"
			else:
				try:
					g_lock.acquire()
					newDeposit = Deposit(username = username, money = money, status = 1, bankcard = bankcard+","+carduser)
					newDeposit.save()
					UserInfo.objects.get(username = username).MoneyChange(-money, MoneyReason.deposit)
					return tips(request, "提现申请成功", reverse('polls:deposit', kwargs={'page':1}))
				except:
					pass
				finally:
					g_lock.release()
		else:
			ErrTips = "输入错误"
		return tips(request, ErrTips, reverse('polls:deposit', kwargs={'page':1}))
	else:
		depositList = Deposit.objects.filter(username = username).order_by('-time')
		numPerPage = 10
		startIndex = (page-1) * numPerPage 
		endIndex = min(len(depositList), page*numPerPage)
		Infos = []
		for i in range(startIndex, endIndex):
			info = {}
			info['time']= depositList[i].time
			info['money'] = depositList[i].money
			info['bankcard'] = depositList[i].bankcard
			info['statusstr'] = DepositStatus.GetDepositStr(depositList[i].status)
			info['status'] = depositList[i].status
			info['id'] = depositList[i].id
			Infos.append(info)
		lastpage = None
		nextpage = None
		if page > 1:
			lastpage = page-1
		if len(depositList) > endIndex:
			nextpage = page+1

		return render(request, r'polls/deposit.html',{'username':username,'forms':DepositForm(),'money':GetDeposit(username), "infos":Infos, 'hashistory':len(Infos)>0})


def canceldeposit(request, depositid):
	depositid = int(depositid)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	try:
		g_lock.acquire()
		DepositData = Deposit.objects.get(id = depositid)
		if DepositData.username == username and DepositData.status == DepositStatus.applystatus:
			DepositData.delete()
			return tips(request, "取消成功，钱已经退回账户", reverse('polls:deposit', kwargs={'page':1}))
		else:
			return tips(request, "失败", reverse('polls:deposit', kwargs={'page':1}))
	except:
		return redirect('/deposit/1')
	finally:
		g_lock.release()

def invite(request, page):
	page = int(page)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	if request.method == 'POST':
		NoUseCode = InvitionCode.objects.filter(bindusername = username, used = False)
		# if len(NoUseCode) > 0:
		# 	ErrTips = "您有邀请码未使用"
		# else:
		if GetConsume(username) >= ENUM.InviteConsumeMoney:
			if GetDeposit(username) >= ENUM.InviteGiftMoney:
				try:
					g_lock.acquire()					
					UserData = UserInfo.objects.get(username = username)
					newone = InvitionCode(bindusername = username, giftmoney = ENUM.InviteGiftMoney, level = ENUM.InviteLevel)
					newone.save()
					UserData.MoneyChange(-ENUM.InviteGiftMoney, MoneyReason.newinvite)
					ErrTips = "生成邀请码成功"
				except:
					ErrTips = "失败"
				finally:
					g_lock.release()					
			else:
				ErrTips = "余额不足"+str(ENUM.InviteGiftMoney)
		else:
			ErrTips = "累计消费不足"+str(ENUM.InviteConsumeMoney)
		return tips(request, ErrTips, reverse('polls:invite', kwargs={'page':1}))
	else:
		profitArr = GetProfitByLevel(ENUM.InviteLevel).split(',')
		rebateArr = GetRebateProfitByLevel(ENUM.InviteLevel).split(',')
		profitInfos = []
		for ordertype in range(0, OrderType.count):
			info = {}
			info['name'] = GetBetNameByType(ordertype)
			info['profit'] = r'1赔'+profitArr[ordertype].split(';')[0].split(':')[1]
			info['rebateprofit'] = str(float(rebateArr[ordertype].split(';')[0].split(':')[1])*100)+r"%"
			profitInfos.append(info)

		Datas = InvitionCode.objects.filter(bindusername = username).order_by('-time')
		numPerPage = 10
		startIndex = (page-1) * numPerPage 
		endIndex = min(len(Datas), page*numPerPage)
		Infos = []
		for i in range(startIndex, endIndex):
			info = {}
			info['code']= Datas[i].code
			info['username'] = Datas[i].username
			if info['username'] == '':
				info['username'] = r"未使用"
			info['rebate'] = Datas[i].rebate
			Infos.append(info)
		lastpage = None
		nextpage = None
		if page > 1:
			lastpage = page-1
		if len(Datas) > endIndex:
			nextpage = page+1
		return render(request, r'polls/invite.html',{'username':username, 'infos':Infos, 'hasinfo':len(Infos)>0, 'profitinfos':profitInfos, 'cosume':ENUM.InviteConsumeMoney, "nextpage":nextpage, 'lastpage':lastpage})

def topup(request):
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	return render(request, r'polls/topup.html', {'username':username})

def seeorder(request, page):
	page = int(page)
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	if username == '8190':
		nowVol = GetLastOpenVol()
		if nowVol == -1:
			nowVol = GetVol()
		if nowVol != -1:
			OrderData = BetOrder.objects.filter(vol__gt = nowVol-2).order_by('-ordertime')
			numPerPage = 15
			startIndex = (page-1) * numPerPage 
			endIndex = min(len(OrderData), page*numPerPage)
			if endIndex < startIndex:
				return tips(request, "错误参数", reverse('polls:seeorder', kwargs={'page':1}))
			OrderList = []
			for i in range(startIndex, endIndex):
				OrderList.append(GetDisplayOrderInfo(OrderData[i]))
			lastPage = False
			nextPage = False
			if page > 1:
				lastPage = page - 1
			if page*numPerPage < len(OrderData):
				nextPage = page + 1
			return render(request, r'polls/seeorder.html', {'orderlist':OrderList, 'username':username, 'lastpage':lastPage, 'nextpage':nextPage, 'hasorder':len(OrderList)>0})

def winorlose(request):
	username = None
	try:
		username = request.session['username']
	except KeyError:
		return redirect('/login')
	Vol = GetLastOpenVol()
	result = []
	for i in range(Vol, max(1, Vol-30), -1):
		total = 0
		OrderData = BetOrder.objects.filter(username = username, vol = i)
		for v in OrderData:
			name, rebate = v.rebate.split(":")
			if name != None and name == username:
				rebate = float(rebate)
			else:
				rebate = 0
			total = total - v.totalmoney + v.wonmoney + rebate
		temp = { 'vol':i, 'money':round(total+0.0001, 2)}
		result.append(temp)
	totalWin = 0
	for v in BetOrder.objects.filter(username = username):
		rebate = 0
		if v.rebate != "":
			name, rebate = v.rebate.split(":")
			if name != None and name == username:
				rebate = float(rebate)
		totalWin = totalWin - v.totalmoney + v.wonmoney + rebate
	totalWin = round(totalWin+0.0001, 2)
	return render(request, r'polls/winorlose.html', {'result':result, 'username':username, 'totalWin':totalWin})
