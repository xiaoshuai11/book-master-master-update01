import pymysql
import pandas as pd
#用面向对象的方式编写，更加熟悉面向对象代码风格
class Mysql_csv(object):
    #定义一个init方法，用于读取数据库
    def __init__(self):
        #读取数据库和建立游标对象
        self.connect = pymysql.connect(host="127.0.0.1",port=3306,user="root",password="331155",database="book_test_csv",charset="utf8")
        self.cursor = self.connect.cursor()
    #定义一个del类，用于运行完所有程序的时候关闭数据库和游标对象
    def __del__(self):
        self.connect.close()
        self.cursor.close()
    def read_csv_colnmus(self):
        #读取csv文件的列索引，用于建立数据表时的字段
        data = pd.read_csv("I:/crack/DATA/myfir.csv",encoding="utf-8")
        #因为读取的数据类型是array一维数组，所以把他转化成列表更方便操作
        data_1 = list(data.columns)
        return data_1
    def read_csv_values(self):
        #读取csv文件数据
        data = pd.read_csv("C:/Users/Administrator/Desktop/毕业设计/图书数据/BX-CSV-Dump/BX-Books.csv", encoding="utf-8")
        data_3 = list(data.values)
        return data_3
    def write_mysql(self):
        #在数据表中写入数据，因为数据是列表类型，把他转化为元组更符合sql语句
        for i in self.read_csv_values(): #因为数据是迭代列表，所以用循环把数据提取出来
            data_6 = tuple(i)
            sql = """insert into movie values{}""".format(data_6)
            self.cursor.execute(sql)
            self.commit()
        print("植入完成")
    def commit(self):
        #定义一个确认事务运行
        self.connect.commit()
    def create(self):
        #创建数据表，用刚才提取的列索引作为字段
        data_2 = self.read_csv_colnmus()
        sql = """create table movie({0} int unsigned primary key not null auto_increment,{1} varchar(200),{2} varchar(100),{3} varchar(100),{4} varchar(100),{5} int)""".format(data_2[0],data_2[1],data_2[2],data_2[3],data_2[4],data_2[5])
        self.cursor.execute(sql)
        self.commit()
    #运行程序，记得要先调用创建数据的类，在创建写入数据的类
    def run(self):
        self.create()
        self.write_mysql()
#最后用一个main()函数来封装
def main():
    sql = Mysql_csv()
    sql.run()
if __name__ == '__main__':
    main()


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
