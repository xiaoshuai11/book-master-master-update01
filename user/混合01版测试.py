import numpy as np

k = [{"a":1,"b":2,"c":3,"d":4},{"a":2,"b":2,"c":2,"d":2},
     {"a": 1, "b": 3, "c": 3, "d": 3}]

s = []
for i in k:
    s.append([i["a"],i["b"],i["c"],i["d"]])

print(s)
print(s[0])
print(s[0][0])
#余弦夹角距离
def cos_angle(user,other):
    # 返回参数
    data = {}
    # 当前登录用户id
    currentUserid = request.session.get("user_id")
    currentUserid = int(currentUserid)
    data_dic = {}  # 创建一个空字典，保存用户-项目评分矩阵
    # 获取所有用户评分数据
    scorecords = Rate.objects.all()

    data_dic = {}  # 创建一个空字典，保存用户-项目评分矩阵
    # 遍历评分数据
    for scorecord in scorecords:
        userid = scorecord.user_id  # 用户id
        itemid = scorecord.book_id  # 书籍id
        rating = int(scorecord.mark)  # 评分
        sex = int(scorecord.sex)    #性别
        age = int(scorecord.age)    #年龄
        work = int(scorecord.work)  #工作
        address = int(scorecord.address)    #国家

        if not userid in data_dic.keys():
            data_dic[userid] = {itemid: [rating, sex, age, work, address]}
        else:
            data_dic[userid][itemid] = [rating, sex, age, work, address]


    # 遍历评分数据
    for scorecord in rate_list:
        userid = scorecord.user_id  # 用户id
        itemid = scorecord.book_id  # 书籍id
        rating = int(scorecord.mark)  # 评分
        if not userid in data_dic.keys():
            data_dic[userid] = {itemid: rating}
        else:
            data_dic[userid][itemid] = rating

    # 计算用户相似度（余弦算法）
    similarity_dic = {}
    similarity_dic[currentUserid] = 0
    for userid, items in data_dic.items():  # 遍历所有用户
        if currentUserid != items[0]:  # 非目标用户
            # 余弦算法
            # 计算分子
            temp = 0
            temp2 = 0
            temp3 = 0
            for itemid, TT in data_dic[currentUserid].items():  # 遍历目标用户评分项目
                if itemid in items.keys():  # 计算公共的项目的评分
                    # 注意，distance越大表示两者越相似
                    temp += float(rating) * float(items[itemid])  # 用户评分 * 其他用户评分
                    temp2 += pow(float(rating), 2)  # 用户评分平方
                    temp3 += pow(float(items[itemid]), 2)  # 其他用户评分平方
            distance = 0
            if temp2 == 0 or temp3 == 0:  # 与用户没有相同图书的，相似度为0
                distance = 0
            else:
                distance = temp / (temp2 + temp3 - temp)
                # distance = temp / (sqrt(temp2) * sqrt(temp3))
            similarity_dic[userid] = distance  # 保存与每个其他用户相似度
            print("userid:" + str(userid) + " : ")
            print(similarity_dic[userid])
    print(similarity_dic)
    # 将相似度从大到小进行排序，方便后期推荐书籍
    b = zip(similarity_dic.values(), similarity_dic.keys())  # 转换成（值，键）的元祖类型
    b = list(sorted(b, reverse=True))  # 按照相似度从大到小排序，并转换为列表
    print(b)
    bookid_list = Rate.objects.filter().none()
    # t_uid = max(similarity_dic,key=similarity_dic.get)  #找出相似度最高的用户id号，再去找他的评价图书
    # bookid_list = Rate.objects.filter(user_id=t_uid).values_list("book_id")
    kid = 0
    # 用户已经评论过的书籍（不推荐）: user_book_list
    user_book_list = Rate.objects.filter(user_id=currentUserid).values_list("book_id")
    print("用户已评价图书：")
    print(user_book_list)

    # 默认推荐10本书籍,并且用户相似度要大于0.7
    while len(bookid_list) < 10 and b[kid][0] > 0.7 and kid < len(b):
        # 找出替他用户中评分高（>=3 ）的，并且目标用户没有评论的图书
        # 条件：相似度从大到小的用户；不包含已选择过的图书； 不包含目标用户所评价过的图书；图书的评价必须大于等于3
        bookid_list |= Rate.objects.filter(
            Q(user_id=b[kid][1]) & ~Q(book_id__in=list(bookid_list)) & ~Q(book_id__in=user_book_list) & Q(
                mark__gte=3)).values_list("book_id")
        print(bookid_list)
        kid += 1

    print("真实推荐图书（相似度推荐）")
    print(bookid_list)
    # 推荐不够10本时，找阅读量最大的补够10本
    if len(bookid_list) < 10:
        # 过滤条件：没有在协同过滤推荐中的书；没有在已评论过的书；按照阅读量从大到小 ； 补齐10本书
        k = Book.objects.filter(~Q(id__in=bookid_list) & ~Q(id__in=user_book_list)).order_by("-num").all()[
            :10 - len(bookid_list)].values_list("id")
        print("推荐图书id")

        # QuerySet 合并 必须类型相同，所有去Book中查找一遍
        bookid_list = Book.objects.filter(id__in=bookid_list).values_list("id")
        print(bookid_list)
        print(k)
        bookid_list = bookid_list.union(k)  # 将两个书单（QuerySet)合并
        bookid_list = set(i[0] for i in bookid_list)
    print(bookid_list)
    # bookid_list = list(chain(bookid_list, k))
    books = Book.objects.filter(id__in=bookid_list).all()

    # books = Book.objects.filter(Q(id__in=bookid_list) | Q(id__in=k))
    # max(similarity_dic[userid])
    return render(request, "user/item.html", {"books": books, "title": "协同过滤推荐"})