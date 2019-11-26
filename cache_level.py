import json

from flask import Flask, request
# import redis
from rediscluster import RedisCluster
from flask_restful import Resource,Api,fields,marshal_with
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
class Config(object):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1:3306/toutiao'
    # RESOURCE_FIELDS = {
    #     'msg':'ok',
    #     'data':{
    #         'id':fields.Integer,
    #         'name':fields.String,
    #
    #     }
    # }

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app=app)
api = Api(app)

class User(db.Model):
    """
    用户基本信息
    """
    __tablename__ = 'user_basic'

    class STATUS:
        ENABLE = 1
        DISABLE = 0

    id = db.Column('user_id', db.Integer, primary_key=True, doc='用户ID')
    mobile = db.Column(db.String, doc='手机号')
    password = db.Column(db.String, doc='密码')
    name = db.Column('user_name', db.String, doc='昵称')
    profile_photo = db.Column(db.String, doc='头像')
    last_login = db.Column(db.DateTime, doc='最后登录时间')
    is_media = db.Column(db.Boolean, default=False, doc='是否是自媒体')
    is_verified = db.Column(db.Boolean, default=False, doc='是否实名认证')
    introduction = db.Column(db.String, doc='简介')
    certificate = db.Column(db.String, doc='认证')
    article_count = db.Column(db.Integer, default=0, doc='发帖数')
    following_count = db.Column(db.Integer, default=0, doc='关注的人数')
    fans_count = db.Column(db.Integer, default=0, doc='被关注的人数（粉丝数）')
    like_count = db.Column(db.Integer, default=0, doc='累计点赞人数')
    read_count = db.Column(db.Integer, default=0, doc='累计阅读人数')

    account = db.Column(db.String, doc='账号')
    email = db.Column(db.String, doc='邮箱')
    status = db.Column(db.Integer, default=1, doc='状态，是否可用')

    # 两种方法都可以
    # followings = db.relationship('Relation', primaryjoin='User.id==Relation.user_id')
    followings = db.relationship('Relation', foreign_keys='Relation.user_id')


class UserProfile(db.Model):
    """
    用户资料表
    """
    __tablename__ = 'user_profile'

    class GENDER:
        MALE = 0
        FEMALE = 1

    id = db.Column('user_id', db.Integer, primary_key=True, doc='用户ID')
    gender = db.Column(db.Integer, default=0, doc='性别')
    birthday = db.Column(db.Date, doc='生日')
    real_name = db.Column(db.String, doc='真实姓名')
    id_number = db.Column(db.String, doc='身份证号')
    id_card_front = db.Column(db.String, doc='身份证正面')
    id_card_back = db.Column(db.String, doc='身份证背面')
    id_card_handheld = db.Column(db.String, doc='手持身份证')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    utime = db.Column('update_time', db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')
    register_media_time = db.Column(db.DateTime, doc='注册自媒体时间')

    area = db.Column(db.String, doc='地区')
    company = db.Column(db.String, doc='公司')
    career = db.Column(db.String, doc='职业')

    followings = db.relationship('Relation', foreign_keys='Relation.user_id')


class Relation(db.Model):
    """
    用户关系表
    """
    __tablename__ = 'user_relation'

    class RELATION:
        DELETE = 0
        FOLLOW = 1
        BLACKLIST = 2

    id = db.Column('relation_id', db.Integer, primary_key=True, doc='主键ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user_basic.user_id'), db.ForeignKey('user_profile.user_id'), doc='用户ID')
    target_user_id = db.Column(db.Integer, db.ForeignKey('user_basic.user_id'), doc='目标用户ID')
    relation = db.Column(db.Integer, doc='关系')
    ctime = db.Column('create_time', db.DateTime, default=datetime.now, doc='创建时间')
    utime = db.Column('update_time', db.DateTime, default=datetime.now, onupdate=datetime.now, doc='更新时间')


REDIS_CLUSTER = [
    {'host': '127.0.0.1', 'port': '7000'},
    {'host': '127.0.0.1', 'port': '7001'},
    {'host': '127.0.0.1', 'port': '7002'},
]
cache_list = {}

class IndexView(Resource):
    # @marshal_with(Config.RESOURCE_FIELDS)
    def get(self):
        user_id = request.args.get('userid')

        key = 'user:{}:profile'.format(user_id)
        # Redis缓存
        redis_cluster = RedisCluster(startup_nodes=REDIS_CLUSTER)
        # 如果redis中有数据，直接取出
        first_cache = cache_list.get(key)
        if first_cache:
            return first_cache
        else:
            value_enc = redis_cluster.get(key)
            if value_enc:
                cache_list[key] = json.loads(value_enc)
                return json.loads(value_enc)
            # 如果redis中无数据，去数据库查询并存入redis
            else:
                id = User.query.get(user_id)

                data = {
                    'id':id.id,
                    'name':id.name
                }
                data_enc = json.dumps(data)
                cache_list[key] = data
                redis_cluster.setex(key, data_enc, 6000)
                return data
api.add_resource(IndexView,'/')

if __name__ == '__main__':
    app.run(host='192.168.179.131')