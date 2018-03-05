from django.conf.urls import url, include
from .views import basic

urlpatterns = [
    url(r'^login$', basic.Login.as_view()),
    url(r'^courses/', basic.Courses.as_view()),
    url(r'^coursedetail/(?P<pk>\d+)/', basic.CourseDetail.as_view()),
    url(r'^shopCart/$', basic.ShopCart.as_view()),
    url(r'^charge/$', basic.Charge.as_view()),
    url(r'^pay/$', basic.Pay.as_view()),
]