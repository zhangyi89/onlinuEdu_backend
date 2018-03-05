from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import APIView
from rest_framework.response import Response
import json
import datetime
import time

from baseapi import models

from baseapi.serialize import courses
from baseapi.serialize import coupon
from dbconnect import redisPool
from baseapi.utils.exception import PricePolicyDoesNotExist

# 支付
from baseapi.views import pay


class Login(APIView):
    def get(self, request, *args, **kwargs):
        return Response('login')

    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        if username == '123' and password == '123':
            return Response('登录成功')
        return Response('用户名或密码错误')


class Courses(APIView):
    def get(self, request, *args, **kwargs):
        course_list = models.Course.objects.all()
        ret = courses.CourseSerializer(instance=course_list, many=True)
        return Response(ret.data)


class CourseDetail(APIView):
    def get(self, request, *args, **kwargs):
        # 根据请求课程id判断返回数据
        pk = kwargs.get('pk')
        if pk:
            # courseItem = models.Course.objects.get(id=pk)
            course_item = models.Course.objects.filter(id=pk).first()
            # 根据课程详细的obj找到该课程的价格
            # print(courseItem.coursedetail.hours)

            ret = courses.CourseSerializer(instance=course_item)
            return Response(ret.data)


class ShopCart(APIView):
    """保存到购物车"""

    # def __init__(self):
    #     self.conn = redisPool.conn

    def get(self, request, *args, **kwargs):
        # 从redis中获取数据
        # 取出这个用户的所有key(课程id）
        user_id = 1
        shop_cart_list = redisPool.conn.hget("shoppingcart", user_id)
        data_dict = json.loads(shop_cart_list.decode("utf-8"))
        return Response(data_dict)

    def post(self, request, *args, **kwargs):
        # 1. 验证用户是否登录
        # 2. 获取获取用户提交的数据，并判断数据的正确性（课程和价格策略）
        # 3. 根据前端需求保存相应的数据到redis中
        # 4. 返回请求结果
        """
        保存到redis的数据结构：
        {"shoppingcart":
            {"用户ID":
                {"课程id":
                    {
                       "课程名称": "name",
                       "课程图像": "img",
                       "价格策略": {"策略1": {"序号": "id", "有效期": "valid_period", "价格": "price"}},
                       "选中策略": "price_policy_id"
                   }
                }
          }
        }
        请求结果数据结构：
        ret_data = {"代号": "code","信息":"message", "数据":"data"}
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        ret_data = {"code": 1000, "message": None, "data": []}
        price_policy = {}
        data = {}
        # user_id = request.user.id
        user_id = 1
        course_id = request.data.get('course_id')
        price_policy_id = request.data.get('policy_id')
        try:
            # 1. 获取课程对象 exlcude用来判断课程是否是非学位课程,以及是否是上线课程，如果不是则抛出自定义异常
            course_obj = models.Course.objects.exclude(course_type=2, status=0).filter(id=course_id).first()

            # 2. 获取课程的价格策略
            price_policys = course_obj.price_policy.all()
            flag = False
            for item in price_policys:
                # 判断策略id是否合法
                if price_policy_id == item.id:
                    flag = True
                price_policy[item.id] = {"id": item.id, "valid_period": item.get_valid_period_display(),
                                         "price": item.price}
            if not flag:
                # 策略不合法则抛出异常
                raise PricePolicyDoesNotExist()

            # 3. 保存数据到redis中
            #    课程id,课程图片地址,课程标题，所有价格策略，默认价格策略
            # 1) 获取用户购物车信息
            user_cart = redisPool.conn.hget('shoppingcart', user_id)
            course_dict = {
                "id": course_obj.id,
                "img": course_obj.course_img,
                "title": course_obj.name,
                "price_policy_list": price_policy,
                "default_policy_id": price_policy_id
            }
            # if not user_cart:
            #         data = {course_obj.id: course_dict}
            # else:
            #     data = json.loads(user_cart.decode('utf-8'))
            #     data[course_obj.id] = course_dict
            data[course_obj.id] = course_dict
            # data必须json.dumps保存，否则的话无法json.loads
            redisPool.conn.hset('shoppingcart', user_id, json.dumps(data))
        except ObjectDoesNotExist as e:
            ret_data['code'] = 1001
            ret_data['message'] = "对象不存在"
        except PricePolicyDoesNotExist as e:
            ret_data['code'] = 1002
            ret_data['message'] = "价格策略不存在"
        except Exception as e:
            ret_data['code'] = 1003
            ret_data['message'] = "加入购物车失败"
            print(e)
        return JsonResponse(ret_data)

    def delete(self, request, *args, **kwargs):
        ret_data = {"code": 1000, "message": None, "data": []}
        user_id = 1
        cid = request.data.get('cid')

        try:
            # 1. 判断删除的cid是否存在购物中
            course_cart = json.loads(redisPool.conn.hget('shoppingcart', user_id).decode("utf8"))
            a = course_cart[str(cid)]
            # 删除对应的课程
            b = course_cart.pop(str(cid))
            # 重新保存到redis
            redisPool.conn.hset('shoppingcart', user_id, json.dumps(course_cart))
        except ObjectDoesNotExist as e:
            ret_data['code'] = 1001
            ret_data['message'] = "对象不存在"
        except Exception as e:
            print(e)
            ret_data['code'] = 1003
            ret_data['message'] = "删除失败"
        return Response(json.dumps(ret_data))


class Charge(APIView):
    """结算（当用户点击去结算时）
    1.发送请求数据，即购物车里的当前课程id
    2.根据课程ID，查找可以使用的课程优惠卷和通用优惠券,以及根据用户登录信息，找到用户的贝里
    3.返回去结算json数据
    去结算json数据格式：

    """
    a = {"课程":
             {"课程id":
                  {"课程名称": "name",
                   "课程图像": "img",
                   "价格策略": {"策略1": {"序号": "id", "有效期": "valid_period", "价格": "price"}},
                   "选中策略": "price_policy_id",
                   "课程优惠卷": "coupon"
                   },
              },
         "用户贝里": "贝里数量",
         "通用优惠卷": {"优惠卷1": "数量", "优惠卷2": "数量"}
         }

    def post(self, request, *args, **kwargs):
        # 获取用户提交的支付课程id 和用户id
        chargeId = request.data.get('chargeId')
        user_id = 1
        # 根据课程id找到购物车里的信息
        course_info = json.loads(redisPool.conn.hget("shoppingcart", user_id).decode('utf8'))
        data = {}
        data["courses"] = course_info

        # 获取用户的贝里
        # balance = request.user.balance
        balance = models.Account.objects.filter(id=user_id).first().balance
        data['balance'] = balance

        # 查找这个用户的课程优惠券
        coupons = models.CouponRecord.objects.filter(account__id=user_id)

        # 序列化优惠券信息
        couponSerializer = coupon.CouponRecordSerializers(instance=coupons, many=True)
        data['coupons'] = couponSerializer.data
        print(data)
        return Response(data)


class Pay(APIView):
    def post(self, request, *args, **kaargs):
        """
        获取用户提交的数据
        1. 支付订单中的每个课程以及课程的优惠卷，计算出折后价
        2. 在1计算出的折后价基础上加上通用优惠券，计算出课程总价格
        3. 在课程总价格的基础上减去用户使用的贝里，计算出应付款
        4. 判断用户选择的支付方式，返回支付页面
        :param request:
        :param args:
        :param kaargs:
        :return:
        """
        # 判断用户合法性
        # user_id = request.user.id
        user_id = 1

        # 获取每个课程信息
        courses = request.data.get('courses')

        total_course_price = 0

        for item in courses:
            # 判断课程的合法性
            # 判断课程价格的合法性
            # 判断优惠券的合法性

            course_price = item.get('coursePrice')
            # 每个课程的优惠券
            coupon = item.get('coupon')

            # 判断优惠券的类型，用来判断如何使用优惠券
            coupon_obj = models.Coupon.objects.filter(name=coupon).first()
            course_price = checkCoupon(coupon_obj, course_price)
            total_course_price += course_price

        # 共同券
        comm_coupon = request.data.get('commCoupon')
        coupon_obj = models.Coupon.objects.filter(name=comm_coupon).first()
        total_course_price = checkCoupon(coupon_obj, total_course_price)

        # 贝里
        # balance = request.user.balance
        bei_li = request.data.get('beili')
        # 判断贝里的合法性

        # 应付款
        pay_price = total_course_price - bei_li

        # 判断支付类型
        pay_way = request.data.get('payWay')
        # 判断支付类型的合法性

        # 生成支付订单
        payment_type = pay_way
        payment_number = ""
        # 转换时间格式(20160505202854)
        order_number = time.strftime("%Y%m%d%H%M%S", time.localtime())

        account = user_id
        actual_amount = pay_price
        status = 0
        order_obj = models.Order.objects.create(
            payment_type=pay_way, order_number=order_number, account_id=user_id, actual_amount=pay_price, status=1
        )



        # 生成订单详情(一个订单可能关联多个订单详情）
        # order = order_number
        # object_id = "课程id"
        # original_price = "课程原价"
        # price = "折后价格"
        # valid_period_display = "有效期显示"
        # valid_period = "课程有效期"

        order_detail = []
        for item in courses:
            object_id = item.get('courseID')
            original_price = item.get('coursePrice')
            # 每个课程的优惠券
            coupon = item.get('coupon')
            # 判断优惠券的类型，用来判断如何使用优惠券
            coupon_obj = models.Coupon.objects.filter(name=coupon).first()
            price = checkCoupon(coupon_obj, original_price)
            valid_period = item.get('valid_period')
            valid_period_display = valid_period
            order_detail_obj = models.OrderDetail(content_type_id=8,
                                                  order=order_obj,
                                                  object_id=object_id,
                                                  original_price=original_price,
                                                  price=price,
                                                  valid_period=valid_period)
            order_detail.append(order_detail_obj)
        models.OrderDetail.objects.bulk_create(order_detail)

        # 判断支付类型（可以通过反射获取），获取支付对象
        alipay = pay.ali()
        # 生成支付的url
        query_params = alipay.direct_pay(
            subject="mmp",  # 商品简单描述
            out_trade_no="x2" + order_number,  # 商户订单号
            total_amount=pay_price,  # 交易金额(单位: 元 保留俩位小数)
        )
        pay_url = "https://openapi.alipaydev.com/gateway.do?{}".format(query_params)
        print(pay_url)

        return Response("123")


def checkCoupon(obj, price):
    money_equivalent_value = obj.money_equivalent_value
    if obj.coupon_type == 0:
        # 通用券，相当于等值货币
        price -= money_equivalent_value
        # 数据库中减去用户的这张优惠券
    elif obj.coupon_type == 1:
        # 满减券, 判断课程价格是否满足最低消费，如果满足则减少此券的面值minimum_consume
        minimum_consume = obj.minimum_consume
        if price >= minimum_consume:
            price -= money_equivalent_value
    elif obj.coupon_type == 2:
        # 折扣券，课程价格打折，off_percent
        off_percent = obj.off_percent * 0.01
        price *= off_percent
    return price
