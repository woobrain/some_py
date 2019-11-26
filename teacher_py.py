"""
1.如果客户端请求的页面，不需要认证，直接返回响应
2.如果客户端请求需要认证的页面。它需要获取本地保存的token
    如果没有获取到，则直接跳转到登录页面

3.如果获取到了本地的token，之后，客户端先判断token是否过期

4. 如果普通的token没有过期，则可以访问页面

5. 如果普通的token过期了，则使用refresh_token

6.如果refresh_token存在，则让refresh_token 去请求一个接口
    这个接口会验证我们的refresh_token,
    如果refresh_token过期，则必须让用户登录
    如果refresh_token没有过期，则返回一个新的 普通token。还会返回最新的refresh_token


根据流程我们需要定义4个接口
1.不需要认证的视图
2.登录视图
3.需要认证的视图
4.需要根据refresh来换取token的视图
"""
import json

from flask import Flask, request, redirect
from flask_restful import Api,Resource
import jwt
from datetime import datetime,timedelta
from flask import g
from time import mktime
app = Flask(__name__)
api=Api(app)

SECRET_KEY='itcast'

#########################################################
# 功能代码
#生成token
def login_token(username):

    # ① 普通token         2小时
    token=jwt.encode(payload={
        'username':username,
        'fresh':False,
        'exp':datetime.utcnow() + timedelta(hours=2)
    },key=SECRET_KEY)
    # ② fresh_token       14天
    fresh_token = jwt.encode(payload={
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=14),
        'fresh':True        # 有这个标记的才是 fresh_token
    }, key=SECRET_KEY)

    # 生成的数据是bytes类型
    return token.decode(),fresh_token.decode()

# 验证token
def check_token(token):

    try:
        data=jwt.decode(token,key=SECRET_KEY)
    except Exception:
        return None
    else:
        return data
########################获取请求token的方法##############################################
def get_request_token():
    bearer_token = request.headers.get('Authorization')
    if bearer_token:
        # Bearer eyJ0eXAiOiJKV1QiLC.JhbGciOiJIUzI1NiJ9.eyJ1c2Vybm
        # 以空格进行 分割，分割为三部分
        data = bearer_token.partition(' ')
        if len(data) == 3:  # 最好判断一下数量
            return data[2]

    return None
################################时间戳################################################
# 让前端记录token获取的时间
# 日期    2019-11-26 09:38:00
# 时间戳   从1970年1月1日 到现在的一个秒数
def get_timestamp():
    date = datetime.utcnow() + timedelta(hours=2)
    return mktime(date.timetuple())
##############请求钩子  获取用户信息 吧用户信息放到g变量中#####################################
@app.before_request
def get_user_info():
    g.username=None
    g.token = None
    # 获取请求头中的 bearer_token,只有携带的时候才有
    bearer_token=request.headers.get('Authorization')
    if bearer_token:
        #Bearer eyJ0eXAiOiJKV1QiLC.JhbGciOiJIUzI1NiJ9.eyJ1c2Vybm
        #以空格进行 分割，分割为三部分
        data=bearer_token.partition(' ')
        if len(data)==3:  #最好判断一下数量
            token=data[2]
            #验证token
            payload=check_token(token)
            if payload: #说明token没有问题
                g.username=payload.get('username')
                g.token = payload.get('fresh')
                # 把用户信息，放到g变量中，以便下边使用




###################装饰器，判断用户是否登录#################################
def loginrequired(func):
    def wrapper(*args,**kwargs):
        # 根据用户信息来判断
        if g.username:
            return func(*args,**kwargs)
        # else:
        #     return {'msg':'token error'},401

    return wrapper
#########################################################
# 视图


#1.不需要认证的视图
class IndexView(Resource):
    def get(self):
        return {'data':'index'}

#2.登录视图
class LoginView(Resource):

    def get(self):
        return {'msg':'login。。。。'}

    def post(self):
        """
        # 1.获取请求参数
        # 2.验证参数
        # 3.判断用户名和密码是否正确
        # 4.如果用户名和密码正确，返回token，refresh_token
        """
        # 1.获取请求参数
        data=json.loads(request.data.decode())
        username=data.get('username')
        password=data.get('password')
        # 2.验证参数(省略)
        # 3.判断用户名和密码是否正确
        if username == 'laowang' and password == 'gebi':
            # user_id,username,photo 等信息
            token,fresh_token=login_token(username)
            # 4.如果用户名和密码正确，返回token，refresh_token
            return {'msg':'ok','data':{'token':token,
                                       'fresh_token':fresh_token,
                                       'expire':get_timestamp()}}
#3.需要认证的视图
"""
每次请求前，我们获取用户的信息
如果用户登录了，则可以访问
如果用户没有登录，则不可以访问

① 我们先定义一个请求钩子，来获取用户信息
② 我们定义一个 装饰器来让 视图装饰

"""
class CenterView(Resource):

    method_decorators = [
        loginrequired
    ]

    def get(self):

        return {'msg':'ok','data':{'username':'laowang'}}

#4.需要根据refresh来换取token的视图
class RefreshView(Resource):

    def put(self):
        """
        1.获取refresh_token
        2.如果refresh_token有效，则返回新的token和新的refresh_token
        3.如果refresh_token无效，则返回 403，前端收到403请求，前端会跳转
        :return:
        """
        # 1.获取refresh_token,验证refresh_token
        refresh_token=get_request_token()
        if refresh_token:
            # 验证token
            payload= check_token(refresh_token)

            if payload:
                if payload.get('fresh') is None:
                    return {'msg':'请登录'},403
                # 2.如果refresh_token有效，则返回新的token和新的refresh_token
                username=payload.get('username')
                new_token,new_fresh_token=login_token(username)
                return {'msg':'ok','data':{'token':new_token,
                                           'fresh_token':new_fresh_token,
                                           'expire': get_timestamp()}}
            else:
                # 3.如果refresh_token无效，则返回 403，前端收到403请求，前端会跳转
                return {'msg': '请登录'}, 403
        else:
            return {'msg':'请登录'},403



# url
api.add_resource(IndexView,'/')
api.add_resource(LoginView,'/login')
api.add_resource(CenterView,'/center')
api.add_resource(RefreshView,'/refresh')

if __name__ == '__main__':
    app.run(host='192.168.179.131',debug=True)