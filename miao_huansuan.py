import datetime,time

date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(1574685945.0))

b = True
user = None
def a():
    if b and not user:
        return 'aa'
ab = a()
print(ab)
print(datetime.datetime.now())
print(datetime.datetime.utcnow())
print(date)