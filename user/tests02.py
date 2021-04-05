from django.test import TestCase

# Create your tests here.
# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @Time    : 2019/1/16 17:14
# @Author  : fuch
# @File    : recommend.py
from math import sqrt
users = {
    '1': {'唐伯虎点秋香': 5, '逃学威龙1': 1, '追龙': 2, '他人笑我太疯癫': 0},
    '2': {'唐伯虎点秋香': 4, '喜欢你': 2, '暗战': 3.5},
    '3': {'复仇者联盟1': 4.5, '逃学威龙1': 2, '大黄蜂': 2.5, '蜘蛛侠：平行宇宙': 2, '巴霍巴利王：开端': 4},
    '4': {'狗十三': 2, '无双': 5},
    '5': {'无双': 4, '逃学威龙1': 4, '逃学威龙2': 4.5, '他人笑我太疯癫': 3}
}
kk = [{"userid_id":1,"itemid_id":1,"score":5},{"userid_id":1,"itemid_id":2,"score":1},{"userid_id":1,"itemid_id":3,"score":2},{"userid_id":1,"itemid_id":4,"score":0},
{"userid_id":2,"itemid_id":1,"score":4},{"userid_id":2,"itemid_id":5,"score":2},{"userid_id":2,"itemid_id":6,"score":3},
{"userid_id":3,"itemid_id":7,"score":4},{"userid_id":3,"itemid_id":2,"score":2},{"userid_id":3,"itemid_id":8,"score":2},{"userid_id":3,"itemid_id":9,"score":2},{"userid_id":3,"itemid_id":10,"score":4},
{"userid_id":4,"itemid_id":11,"score":2},{"userid_id":4,"itemid_id":12,"score":5},
{"userid_id":5,"itemid_id":12,"score":4},{"userid_id":5,"itemid_id":2,"score":4},{"userid_id":5,"itemid_id":4,"score":3},
      ]


#def recommend(request):

#返回参数
data = {}
#当前登录用户id
currentUserid = 5
#    currentUserid = request.session.get(Constant.session_user_id)
currentUserid = int(currentUserid)
#获取所有用户评分数据
scorecords = kk
#scorecords = Sc.objects.all()

data_dic = {} #创建一个空字典，保存用户-项目评分矩阵
#遍历评分数据
for scorecord in scorecords:
    userid = scorecord["userid_id"]    #用户id
    itemid = scorecord["itemid_id"]    #项目id
    rating = int(scorecord["score"])   #评分
    if not userid in data_dic.keys():
        data_dic[userid] = {itemid:rating}
    else:
        data_dic[userid][itemid] = rating
if len(data_dic) == 0:
    print("没有评分数据")
    #return render(request,"index/recomen.html",context=data)

#计算用户相似度（余弦算法）
similarity_dic = {}
similarity_dic[currentUserid] = 0
for userid,items in data_dic.items():  #遍历所有用户
    if currentUserid != userid:     #非目标用户
        #余弦算法
        #计算分子
        temp = 0
        temp2 = 0
        temp3 = 0
        for itemid,rating in data_dic[currentUserid].items():   #遍历目标用户评分项目
            if itemid in items.keys():  #计算公共的项目的评分
                #注意，distance越大表示两者越相似
                temp += float(rating)*float(items[itemid])  #用户评分 * 其他用户评分
                temp2 += pow(float(rating),2)           # 用户评分平方
                temp3 += pow(float(items[itemid]),2)    #其他用户评分平方
        distance = 0
        if temp2 == 0 or temp3 == 0:    #与用户没有相同图书的，相似度为0
            distance = 0
        else:
            distance = temp / (temp2 + temp3 - temp)
            #distance = temp / (sqrt(temp2) * sqrt(temp3))
            #distance = temp / sqrt(temp2 * temp3)
        similarity_dic[userid] = distance     #保存与每个其他用户相似度
        print("userid:" + str(userid) + " : ")
        print(similarity_dic[userid])

#推荐，预测评分
#先计算目标用户的平均评分
sum_rating = 0
for itemid,rating in data_dic[currentUserid].items():
    sum_rating += float(rating)
#目标用户对项目的平均分
avg_rating = sum_rating / len(data_dic[currentUserid].items())
#推荐
item_rec_dic = {}
# 遍历用户相似度
for userid,similarity in similarity_dic.items():  #循环每个其他用户相似度：userid:用户id, similarity:相似度
    for itemid,rating in data_dic[userid].items():  #循环其他用户评分：itemid:用户id, rating:评分
        if not itemid in data_dic[currentUserid].keys(): #不是目标用户
            if not itemid in item_rec_dic.keys():
                item_rec_dic[itemid] = {userid:rating}
            else:
                item_rec_dic[itemid][userid] = rating
print("所有推荐项目:")
for i in item_rec_dic.items():
    print(i)
