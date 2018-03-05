import redis

# pool = redis.ConnectionPool(host='172.16.240.132', port=6379)
conn = redis.Redis(host='172.16.240.132', port=6379)

# 字典，散列表，哈希
# conn.hset('k4','n1','xxx')
# data = conn.hget('k4','n1')
# print(data)
# conn.hset('oldboyedu', 'alex',16)
# conn.hincrby('oldboyedu', 'alex', amount=-1)
# data = conn.hget('oldboyedu', 'alex')
# print(data)
# conn.hset('oldboyedu', 'oldboy',56)

# for k, v in conn.hscan_iter('oldboyedu', match="*lx"):
#     print(k, v)


