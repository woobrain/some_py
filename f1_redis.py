import redis


redis_conn = redis.StrictRedis(host='127.0.0.1',port=6379)

pipe = redis_conn.pipeline()
pipe.get('name')
pipe.get('age')
pipe.set('like','py')
res = pipe.execute()
print(res)