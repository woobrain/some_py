import datetime
import json
from time import mktime

import jwt
from flask import Flask, request, g, jsonify, redirect, url_for
from flask_restful import Api, Resource

"""
1.一般来说，会首先判断地址是否需要认证
2.不需要认证，则不进行token检验，如;首页
3.需要认证，进行token判断，如果没有token字段，则返回登陆
4.如果有字段token，为空，错，过期，那么需要进行获取refresh_token
5.如果refresh_token 不存在，返回登陆
6.存在，获取过期时间，过期。返回登陆
7.没有过期，则根据refresh_token获取新的token和新的refresh_token，返回给前端

"""


class Config(object):

    key = 'woobrain'
    algorithm = 'HS256'
    exp_time = {
        'days': 12,
        'hours': 2,
        'minutes': 3,
        'seconds': 4
    }
    DATE_HOURS = datetime.datetime.now() + datetime.timedelta(hours=2)
    DATE_DAYS = datetime.datetime.now() + datetime.timedelta(days=14)
    TIME_CHUO = mktime(datetime.datetime.now().timetuple())


app = Flask(__name__)
app.config.from_object(Config)
api = Api(app)


def login_token(username):
    token = jwt.encode({'username': username,
                        'exp': Config.DATE_HOURS},
                       key=Config.key, algorithm=Config.algorithm)
    refrash_token = jwt.encode({'username': username,
                                'exp': Config.DATE_DAYS,
                                'token': True},
                               key=Config.key, algorithm=Config.algorithm)
    return token.decode(), refrash_token.decode()


def check_login(token):
    try:
        user_info = jwt.decode(token, key=Config.key)
    except Exception:
        return None
    else:
        return user_info


# 抽取
def check_token():
    breare_token = request.headers.get('Authorization')
    if breare_token:
        token_list = breare_token.split(' ')
        if len(token_list) == 2:
            token = token_list[1]
            if token:
                user_info = check_login(token)
                return user_info
    return None

# 获取用户信息以及token
@app.before_request
def UserInfoToken():
    # 前端给后端传入token时,形式是
    # Authorization:Bearer token
    user_info = check_token()
    # 万能的try
    # try:
    #     res = user_info.get('token')
    #     print(res)
    # except Exception:
    #     if user_info:
    #         g.username = user_info['username']
    #     else:
    #         g.username = None
    # else:
    #     return redirect('/login')


    if user_info:
        # 不会抛出错误的get
        if user_info.get('token') is None:
            g.username = user_info['username']
        else:
            return redirect('/login')
    else:
        g.username = None


def loginverify(func):
    def wrapper(*args, **kwargs):
        if g.username:
            return func(*args, **kwargs)
        else:
            print(g.username)
            return {'msg': 'token error'}, 401

    return wrapper


class IndexView(Resource):
    def get(self):
        return {'msg': 'ok', 'index': 'index ....'}


class LoginView(Resource):
    def get(self):
        return {'msg': 'ok', 'data': '这是登录'}

    def post(self):
        data = json.loads(request.data.decode())
        username = data.get('username')
        password = data.get('password')

        if username == 'laowang' and password == '123456':
            token, refrash_token = login_token(username)

            return {'msg': 'ok', 'data': {'token': token, 'refrash_token': refrash_token,'exp':Config.TIME_CHUO}}


class CenterVerView(Resource):
    method_decorators = [
        loginverify
    ]

    def get(self):
        return {'msg': 'ok', 'username': g.username}


class RefreshTokenView(Resource):
    def get(self):
        user_info = check_token()
        if user_info:
            if user_info.get('token') is not None:
                print(user_info.get('token'))
                new_token, new_refresh_token = login_token(g.username)
                return {'msg': 'ok', 'data': {'token': new_token, 'refresh_token': new_refresh_token,'exp':Config.TIME_CHUO}}

        return redirect('/login')


api.add_resource(IndexView, '/')
api.add_resource(LoginView, '/login')
api.add_resource(CenterVerView, '/token')
api.add_resource(RefreshTokenView, '/refresh_token')
print(app.url_map)

if __name__ == '__main__':
    app.run(debug=True,host='192.168.179.131')