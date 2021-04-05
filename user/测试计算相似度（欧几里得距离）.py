import numpy as np

users = ["小明", "小花", "小美", "小张", "小李"]
movies = ["电影1", "电影2", "电影3", "电影4", "电影5", "电影6", "电影7"]
allUserMovieStarList = [
    [1, 1, 1, 0, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 0],
    [1, 0, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 0, 0],
    [1, 1, 0, 1, 0, 1, 1]]


def converRow2Col():
    """
    行转列
    :return:
    """
    return np.array(allUserMovieStarList).transpose().tolist()


def cal_two_mv_sim(movie1Stars: list, movie2Stars: list):
    """
    欧式距离计算两个电影之间的相似度
    :param movie1Stars:
    :param movie2Stars:
    :return:
    """
    return np.sqrt(((np.array(movie1Stars) - np.array(movie2Stars)) ** 2).sum())


def cal_all_mv_sim():
    """
    计算所有电影之间的相似度
    :return:
    """
    resDic = {}
    tempList = converRow2Col()
    for i in range(0, len(tempList)):
        for j in range(i + 1, len(tempList)):
            resDic[str(i) + '-' + str(j)] = cal_two_mv_sim(tempList[i], tempList[j])
    return resDic


def calrecommendMoive(username: str) -> list:
    """
    计算待推荐的电影
    :return:list
    """
    temp = {}
    movies_sim_dic = cal_all_mv_sim()  #计算所有相似度，形成相似矩阵 [{"0-1":0,44},...]
    userindex = users.index(username)   #所有用户的索引号（0-5）
    target_user_movie_list = allUserMovieStarList[userindex] #用户对每个电影的评价，可改成用户不同特征的值
    for i in range(0, len(target_user_movie_list)):
        for j in range(i + 1, len(target_user_movie_list)):
            #判断用户出现一个评分，一个没评，并且两用户之间相似度不为空（可选出
            if target_user_movie_list[i] == 1 and target_user_movie_list[j] == 0 and \
                    (movies_sim_dic.get(str(i) + '-' + str(j)) != None or \
                                 movies_sim_dic.get(str(j) + '-' + str(i)) != None):
                #相似度（sim）= 相似矩阵中 "i-j" 和 "j-i" 的非空值
                sim = movies_sim_dic.get(str(i) + '-' + str(j)) if (
                movies_sim_dic.get(str(i) + '-' + str(j)) != None) else movies_sim_dic.get(str(j) + '-' + str(i))
                temp[j] = sim
            elif target_user_movie_list[i] == 0 and target_user_movie_list[j] == 1 and \
                    (movies_sim_dic.get(str(i) + '-' + str(j)) != None or \
                                 movies_sim_dic.get(str(j) + '-' + str(i)) != None):
                sim = movies_sim_dic.get(str(i) + '-' + str(j)) if (
                    movies_sim_dic.get(str(i) + '-' + str(j)) != None) else movies_sim_dic.get(
                    str(j) + '-' + str(i))
                temp[i] = sim
    print(temp)
    temp = sorted(temp.items(), key=lambda d: d[1])
    print("待推荐列表：", temp)
    recommendlist = [movies[i] for i, v in temp]
    print("待推荐列表：", recommendlist)
    return recommendlist


print(cal_all_mv_sim())

calrecommendMoive("小李")
calrecommendMoive("小明")


# 定义的计算相似度的公式，用的是皮尔逊相关系数计算方法
def pearson(self, rating1, rating2):
    sum_xy = 0
    sum_x = 0
    sum_y = 0
    sum_x2 = 0
    sum_y2 = 0
    n = 0
    for key in rating1:
        if key in rating2:
            n += 1
            x = rating1[key]
            y = rating2[key]
            sum_xy += x * y
            sum_x += x
            sum_y += y
            sum_x2 += pow(x, 2)
            sum_y2 += pow(y, 2)
    if n == 0:
        return 0

    # 皮尔逊相关系数计算公式
    denominator = np.sqrt(sum_x2 - pow(sum_x, 2) / n) * np.sqrt(sum_y2 - pow(sum_y, 2) / n)
    if denominator == 0:
        return 0
    else:
        return (sum_xy - (sum_x * sum_y) / n) / denominator

