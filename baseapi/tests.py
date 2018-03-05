from django.test import TestCase

# Create your tests here.


a = {'1': {'id': 1, 'img': '111', 'title': '爬虫开发',
           'price_policy_list': {'4': {'id': 4, 'valid_period': '1个月', 'price': 99.0},
                                 '5': {'id': 5, 'valid_period': '2个月', 'price': 199.0},
                                 '6': {'id': 6, 'valid_period': '3个月', 'price': 299.0}}, 'default_policy_id': 5}}
a.pop('1')
print(a)


a = 8
b = 20
b -= a
print(b)
b *= 0.01
print(b)

aa = 2
for i in range(2):
    aa += 10
print(aa)

import datetime
import time

#转换成localtime

dt = time.strftime("%Y%m%d%H%M%S", time.localtime())
print(dt)

print(datetime.datetime.now())
with open("backend_lc/keys/app_private_2048.txt") as p:
    print(p.read())

# import os
# baseDir =
# os.path.dirname(os.path.abspath(__name__)) # 获取运行路径
# jpgdir = os.path.join(baseDir, 'media') # 加上media路径
# filename = os.path.join(jpgdir, wenjian.name) # 获取文件路径