from django.conf.urls import url

from . import views

app_name = 'polls'
urlpatterns = [
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
    # url(r'^usermgr/$', views.usermgr, name='usermgr'),
    url(r'^history/(?P<page>[\d]+)/$', views.history, name='history'),
    url(r'^riskmgr/$', views.riskmgr, name='riskmgr'),
    url(r'^deposit/(?P<page>[\d]+)/$', views.deposit, name='deposit'),
    url(r'^canceldeposit/(?P<depositid>[\d]+)/$', views.canceldeposit, name='canceldeposit'),
    url(r'^betorder/(?P<ordertype>[\d]+)/$', views.betorder, name='betorder'),
    url(r'^tips/$', views.tips, name='tips'),
    url(r'^myaccount/(?P<page>[\d]+)/$', views.myaccount, name='myaccount'),
    url(r'^seeorder/(?P<page>[\d]+)/$', views.seeorder, name='seeorder'),
    url(r'^myaccount/transfer/(?P<page>[\d]+)/$', views.transfer, name='transfer'),
    url(r'^cancelorder/(?P<orderid>[\d]+)/$',views.cancelorder, name ='cancelorder'),
    url(r'^invite/(?P<page>[\d]+)/$', views.invite, name='invite'),
    url(r'^topup/$', views.topup, name='topup'),
    url(r'^winorlose/$', views.winorlose, name='winorlose'),
    url(r'^$', views.index, name='index'),
]