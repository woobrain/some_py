import datetime

import jwt


data = jwt.encode({'user':'woobrain',
                   'exp':datetime.datetime.utcnow()+datetime.timedelta(seconds=120)
                   },key='woobrain',algorithm='HS256')

# print(data)

data_encode = jwt.decode(data,key='woobrain')
print(data_encode)