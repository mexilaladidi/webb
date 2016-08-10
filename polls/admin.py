from django.contrib import admin

from .models import UserInfo, OpenNum, BetOrder, InvitionCode, Bill, Deposit

class OrderAdmin(admin.ModelAdmin):
	list_display = ('vol', 'username', 'ordertype', 'totalmoney', 'wonmoney')
	list_filter = ['username', 'vol']
	search_fields = ['username','vol']

class InvitionCodeAdmin(admin.ModelAdmin):
	list_display = ('code', 'bindusername')
	list_filter = ['bindusername']
	search_fields = ['bindusername']

class BillAdmin(admin.ModelAdmin):
	list_display = ('username', 'money', 'billtype', 'operateuser')
	list_filter = ['username']
	search_fields = ['username']

class DepositAdmin(admin.ModelAdmin):
	list_display = ('username', 'money', 'status', 'bankcard')
	list_filter = ['username']
	search_fields = ['username']


admin.site.register(UserInfo)
admin.site.register(OpenNum)
admin.site.register(BetOrder, OrderAdmin)
admin.site.register(InvitionCode, InvitionCodeAdmin)
admin.site.register(Bill, BillAdmin)
admin.site.register(Deposit, DepositAdmin)

# Register your models here.
