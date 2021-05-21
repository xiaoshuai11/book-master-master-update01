from functools import wraps

from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from math import sqrt
import numpy as np
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from rest_framework.renderers import JSONRenderer
from django.views.decorators.cache import cache_page

from recommend_books import recommend_by_user_id
from .forms import *


def login_in(func):  # 验证用户是否登录
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = args[0]
        is_login = request.session.get("login_in")
        if is_login:
            return func(*args, **kwargs)
        else:
            return redirect(reverse("login"))
    return wrapper


def books_paginator(books, page):
    paginator = Paginator(books, 6)
    if page is None:
        page = 1
    books = paginator.page(page)
    return books


class JSONResponse(HttpResponse):
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs["content_type"] = "application/json"
        super(JSONResponse, self).__init__(content, **kwargs)

#登录
def login(request):
    if request.method == "POST":
        form = Login(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            result = User.objects.filter(username=username)
            if result:
                user = User.objects.get(username=username)
                if user.password == password:
                    request.session["login_in"] = True
                    request.session["user_id"] = user.id
                    request.session["name"] = user.name
                    return redirect(reverse("all_book"))
                else:
                    return render(
                        request, "user/login.html", {"form": form, "error": "账号或密码错误"}
                    )
            else:
                return render(
                    request, "user/login.html", {"form": form, "error": "账号不存在"}
                )
    else:
        form = Login()
        return render(request, "user/login.html", {"form": form})

#注册
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        error = None
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password2"]
            email = form.cleaned_data["email"]
            name = form.cleaned_data["name"]
            phone = form.cleaned_data["phone"]
            address = form.cleaned_data["address"]
            age = form.cleaned_data["age"]
            sex = form.cleaned_data["sex"]
            work = form.cleaned_data["work"]
            User.objects.create(
                username=username,
                password=password,
                email=email,
                name=name,
                phone=phone,
                address=address,
                age=age,
                sex=sex,
                work=work,
            )
            # 根据表单数据创建一个新的用户
            return redirect(reverse("login"))  # 跳转到登录界面
        else:
            # print(form, 'lllllllllllllllll')
            return render(
                request, "user/register.html", {"form": form, "error": error}
            )  # 表单验证失败返回一个空表单到注册页面
    form = RegisterForm()
    return render(request, "user/register.html", {"form": form})

#登录页面
def logout(request):
    if not request.session.get("login_in", None):  # 不在登录状态跳转回首页
        return redirect(reverse("index"))
    request.session.flush()  # 清除session信息
    return redirect(reverse("index"))

#所有书籍
def all_book(request):
    books = Book.objects.annotate(user_collector=Count('collect')).order_by('-user_collector')
    paginator = Paginator(books, 9)
    current_page = request.GET.get("page", 1)
    books = paginator.page(current_page)
    return render(request, "user/item.html", {"books": books, "title": "所有书籍"})

# 搜索
def search(request):
    if request.method == "POST":  # 如果搜索界面
        key = request.POST["search"]
        request.session["search"] = key  # 记录搜索关键词解决跳页问题
    else:
        key = request.session.get("search")  # 得到关键词
    books = Book.objects.filter(
        Q(title__icontains=key) | Q(intro__icontains=key) | Q(author__icontains=key)
    )  # 进行内容的模糊搜索
    page_num = request.GET.get("page", 1)
    books = books_paginator(books, page_num)
    return render(request, "user/item.html", {"books": books})


# 获取具体的书籍
def book(request, book_id):
    book = Book.objects.get(pk=book_id)
    book.num += 1
    book.save()
    #取出图书评论先关信息
    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)

    if user_id:
        user = User.objects.get(pk=user_id)
        is_collect = book.collect.filter(id=user_id).first()
        is_rate = Rate.objects.filter(book=book, user=user).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


@login_in
# 图书评分
def score(request, book_id):
    user = User.objects.get(id=request.session.get("user_id"))
    book = Book.objects.get(id=book_id)
    score = float(request.POST.get("score", 0))
    is_rate = Rate.objects.filter(book=book, user=user).first()
    if not is_rate:
        book.rate_num += 1
        book.save()
        Rate.objects.get_or_create(user=user, book=book, defaults={"mark": score},age=user.age,sex=user.sex,work=user.work,address=user.address)
        is_rate = {'mark': score}
    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    #计算书籍总平均得分
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)
    user = User.objects.get(pk=user_id)
    is_collect = book.collect.filter(id=user_id).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


@login_in
# 评论
def commen(request, book_id):
    user = User.objects.get(id=request.session.get("user_id"))
    book = Book.objects.get(id=book_id)
    comment = request.POST.get("comment", "")
    Comment.objects.create(user=user, book=book, content=comment)
    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)
    user = User.objects.get(pk=user_id)
    is_collect = book.collect.filter(id=user_id).first()
    is_rate = Rate.objects.filter(book=book, user=user).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


@login_in
#点赞
def good(request, commen_id, book_id):
    # 点赞
    commen = Comment.objects.get(id=commen_id)
    commen.good += 1
    commen.save()
    book = Book.objects.get(id=book_id)
    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)
    if user_id is not None:
        user = User.objects.get(pk=user_id)
        is_collect = book.collect.filter(id=user_id).first()
        is_rate = Rate.objects.filter(book=book, user=user).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


@login_in
#点击收藏
def collect(request, book_id):
    user = User.objects.get(id=request.session.get("user_id"))
    book = Book.objects.get(id=book_id)
    book.collect.add(user)
    book.sump += 1  # 收藏人数加1
    book.save()

    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)

    user = User.objects.get(pk=user_id)
    is_collect = book.collect.filter(id=user_id).first()
    is_rate = Rate.objects.filter(book=book, user=user).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


@login_in
#取消收藏
def decollect(request, book_id):
    user = User.objects.get(id=request.session.get("user_id"))
    book = Book.objects.get(id=book_id)
    book.collect.remove(user)
    book.sump -= 1
    book.save()
    comments = book.comment_set.order_by("-create_time")
    user_id = request.session.get("user_id")
    rate = Rate.objects.filter(book=book).aggregate(Avg("mark")).get("mark__avg", 0)
    rate = rate if rate else 0
    book_rate = round(rate, 2)

    user = User.objects.get(pk=user_id)
    is_collect = book.collect.filter(id=user_id).first()
    is_rate = Rate.objects.filter(book=book, user=user).first()
    rate_num = book.rate_num
    sump = book.sump
    return render(request, "user/book.html", locals())


# 方法I
# @cache_page(60 * 1)
def message_boards(request, fap_id=1, pagenum=1, **kwargs):
    # 获取论坛内容
    msg = request.GET.get('msg', '')
    # print('做了缓存')
    have_board = True
    if fap_id == 1:
        # 热门
        msg_board = MessageBoard.objects.all().order_by('-like_num')
    elif fap_id == 2:
        # 最新
        msg_board = MessageBoard.objects.all().order_by('-create_time')
    elif fap_id == 3:
        # 点赞
        is_login = request.session.get("login_in")
        if not is_login:
            return redirect(reverse("login"))
        user = User.objects.get(id=request.session.get("user_id"))
        collectboards = CollectBoard.objects.filter(user=user, is_like=True).order_by(
            'create_time')
        msg_board = []
        for mb in collectboards:
            msg_board.append(mb.message_board)

    elif fap_id == 4:
        # 收藏
        is_login = request.session.get("login_in")
        if not is_login:
            return redirect(reverse("login"))
        user = User.objects.get(id=request.session.get("user_id"))
        collectboards = CollectBoard.objects.filter(user=user, is_collect=True).order_by(
            'create_time')
        msg_board = []
        for mb in collectboards:
            msg_board.append(mb.message_board)
    elif fap_id == 5:
        # 我的
        is_login = request.session.get("login_in")
        if not is_login:
            return redirect(reverse("login"))
        user = User.objects.get(id=request.session.get("user_id"))
        msg_board = MessageBoard.objects.filter(user=user).order_by('-create_time')
    else:
        msg_board = MessageBoard.objects.all().order_by('create_time')
    if not msg_board:
        have_board = False

    # 构建分页器对象,blogs=所有博文,2=每页显示的个数
    paginator = Paginator(msg_board, 10)

    # 获取第n页的页面对象
    page = paginator.page(pagenum)

    # Paginator和Page的常用API
    # page.previous_page_number()
    # page.next_page_number()
    # page.has_previous()
    # page.has_next()

    # 构造页面渲染的数据
    '''
    渲染需要的数据:
    - 当前页的博文对象列表
    - 分页页码范围
    - 当前页的页码
    '''
    data = {
        # 当前页的博文对象列表
        "page": page,
        # 分页页码范围
        "pagerange": paginator.page_range,
        # 当前页的页码
        "currentpage": page.number,
        "message_boards": msg_board,
        "have_board": have_board,
        "fap_id": fap_id,
    }

    return render(request, "user/message_boards.html", context=data)


@login_in
def new_message_board(request):
    # 写新论坛
    user = User.objects.get(id=request.session.get("user_id"))
    title = request.POST.get("title")
    content = request.POST.get("content")
    # print('ddddddddddddddddd', title, content)
    if not title or not content:
        return redirect(reverse("message_boards", kwargs={'fap_id': 2, 'pagenum': 1}))
    MessageBoard.objects.create(user=user, content=content, title=title)
    return redirect(reverse("message_boards", args=(2, 1)))


def get_message_board(request, message_board_id, fap_id=1, currentpage=1):
    # 用户每浏览一次，就增加一次浏览量
    try:
        user = User.objects.get(id=request.session.get("user_id"))
        collectboard = CollectBoard.objects.filter(user=user, message_board_id=message_board_id)
        is_like = collectboard.first().is_like
        is_collect = collectboard.first().is_collect
    except:
        is_like = 0
        is_collect = 0

    MessageBoard.objects.filter(id=message_board_id).update(look_num=F('look_num') + 1)
    msg_board = MessageBoard.objects.get(id=message_board_id)

    board_comments = msg_board.boardcomment_set.all()
    have_comment = True
    if not board_comments:
        have_comment = False

    context = {"msg_board": msg_board,
               "board_comments": board_comments,
               "have_comment": have_comment,
               "fap_id": fap_id,
               "currentpage": currentpage,
               'is_like': is_like,
               'is_collect': is_collect,
               'message_board_id': message_board_id
               }
    return render(request, "user/message_board.html", context=context)


@login_in
def new_board_comment(request, message_board_id, fap_id=1, currentpage=1):
    # 写评论
    content = request.POST.get("content")
    if not content:
        return redirect(reverse("get_message_board", args=(message_board_id, fap_id, currentpage)))

    MessageBoard.objects.get(id=message_board_id)
    user = User.objects.get(id=request.session.get("user_id"))

    BoardComment.objects.create(
        user=user, content=content, message_board_id=message_board_id
    )
    MessageBoard.objects.filter(id=message_board_id).update(feebback_num=F('feebback_num') + 1)
    return redirect(reverse("get_message_board", args=(message_board_id, fap_id, currentpage)))


# @login_in
# 点赞或收藏
def like_collect(request):
    # 点赞或收藏

    try:
        user = User.objects.get(id=request.session.get("user_id"))
    except:
        return JsonResponse(data={'code': 2, 'msg': '没有登录'})
    message_board_id = request.POST.get("message_board_id")
    like_or_collect = request.POST.get("like_or_collect", None)  # 点赞还是收藏
    is_like = request.POST.get("is_like", None)  # 是否点赞
    is_collect = request.POST.get("is_collect", None)  # 是否收藏
    # print('lllll', like_or_collect, is_like, is_collect)
    if like_or_collect not in ['like', 'collect'] or None in [is_like, is_collect]:
        return JsonResponse(data={'code': 0, 'msg': '参数有误1'})
    try:
        collectboard = CollectBoard.objects.filter(user=user, message_board_id=message_board_id)
        if not collectboard:
            CollectBoard.objects.create(user=user, message_board_id=message_board_id,
                                        is_collect=is_collect if like_or_collect == 'collect' else 0,
                                        is_like=is_like if like_or_collect == 'like' else 0)
            if like_or_collect == 'like':
                if is_like == 0:
                    MessageBoard.objects.filter(id=message_board_id).update(like_num=F('like_num') - 1)
                else:
                    MessageBoard.objects.filter(id=message_board_id).update(like_num=F('like_num') + 1)
            else:
                if is_like == 0:
                    MessageBoard.objects.filter(id=message_board_id).update(collect_num=F('collect_num') - 1)
                else:
                    MessageBoard.objects.filter(id=message_board_id).update(collect_num=F('collect_num') + 1)
            return JsonResponse(data={'code': 1, 'msg': '操作成功'})
        collectboard = collectboard.first()
        if like_or_collect == 'like':
            is_collect = collectboard.is_collect
        else:
            is_like = collectboard.is_like
        CollectBoard.objects.filter(user=user, message_board_id=message_board_id).update(is_collect=is_collect,
                                                                                         is_like=is_like)
        if like_or_collect == 'like':
            if is_like == 0:
                MessageBoard.objects.filter(id=message_board_id).update(like_num=F('like_num') - 1)
            else:
                MessageBoard.objects.filter(id=message_board_id).update(like_num=F('like_num') + 1)
        else:
            if is_like == 0:
                MessageBoard.objects.filter(id=message_board_id).update(collect_num=F('collect_num') - 1)
            else:
                MessageBoard.objects.filter(id=message_board_id).update(collect_num=F('collect_num') + 1)
        return JsonResponse(data={'code': 1, 'msg': '操作成功', 'is_like': is_like, 'is_collect': is_collect})
    except Exception as e:
        print(e)
        return JsonResponse(data={'code': 0, 'msg': '参数有误2'})


@login_in
def personal(request):
    # 获取我的信息
    user = User.objects.get(id=request.session.get("user_id"))
    if request.method == "POST":
        form = Edit(instance=user, data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse("personal"))
        else:
            return render(
                request, "user/personal.html", {"message": "修改失败", "form": form}
            )
    form = Edit(instance=user)
    return render(request, "user/personal.html", {"form": form})


@login_in
# 我的收藏
def mycollect(request):
    user = User.objects.get(id=request.session.get("user_id"))
    book = user.book_set.all()
    return render(request, "user/mycollect.html", {"book": book})


@login_in
#我的活动
def myjoin(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    user_actions = user.action_set.all()
    return render(request, "user/myaction.html", {"action": user_actions})


@login_in
#我的评论
def my_comments(request):
    user = User.objects.get(id=request.session.get("user_id"))
    comments = user.comment_set.all()
    # print('comment:', comments)
    return render(request, "user/my_comment.html", {"comments": comments})

# 删除评论
@login_in
def delete_comment(request, comment_id):
    # 删除评论
    Comment.objects.get(pk=comment_id).delete()
    user = User.objects.get(id=request.session.get("user_id"))
    comments = user.comment_set.all()
    # print('comment:', comments)
    return render(request, "user/my_comment.html", {"comments": comments})


@login_in
def my_rate(request):
    user = User.objects.get(id=request.session.get("user_id"))
    rate = user.rate_set.all()
    return render(request, "user/my_rate.html", {"rate": rate})


@login_in
#删除评分
def delete_rate(request, rate_id):
    #pk为primary key（主键）
    rate = Rate.objects.filter(pk=rate_id)
    if not rate:
        return render(request, "user/my_rate.html", {"rate": rate})
    rate = rate.first()
    rate.book.rate_num -= 1
    rate.book.save()
    rate.save()
    rate.delete()
    user = User.objects.get(id=request.session.get("user_id"))
    rate = user.rate_set.all()
    return render(request, "user/my_rate.html", {"rate": rate})

#最热书籍
def hot_book(request):
    page_number = request.GET.get("page", 1)
    #根据收藏量排序
    books = Book.objects.annotate(user_collector=Count('collect')).order_by('-user_collector')[:10]
    books = books_paginator(books[:10], page_number)
    return render(request, "user/item.html", {"books": books, "title": "最热书籍"})

#最新书籍
def latest_book(request):
    page_number = request.GET.get("page", 1)
    books = books_paginator(Book.objects.order_by("-id")[:10], page_number)
    return render(request, "user/item.html", {"books": books, "title": "最新书籍"})

#诺贝尔文学奖
def nobel_book(request):
    page_number = request.GET.get("page", 1)
    book_cate = "诺贝尔文学奖"
    books = books_paginator(Book.objects.filter(good=book_cate), page_number)
    return render(request, "user/item.html", {"books": books, "title": book_cate})

#茅盾文学奖
def md_book(request):
    page_number = request.GET.get("page", 1)
    book_cate = "茅盾文学奖"
    books = books_paginator(Book.objects.filter(good=book_cate), page_number)
    return render(request, "user/item.html", {"books": books, "title": book_cate})


def begin(request):
    if request.method == "POST":
        email = request.POST["email"]
        username = request.POST["username"]
        result = User.objects.filter(username=username)
        if result:
            if result[0].email == email:
                result[0].password = request.POST["password"]
                return HttpResponse("修改密码成功")
            else:
                return render(request, "user/begin.html", {"message": "注册时的邮箱不对"})
        else:
            return render(request, "user/begin.html", {"message": "账号不存在"})
    return render(request, "user/begin.html")


def kindof(request):
    tags = Tags.objects.all()
    return render(request, "user/kindof.html", {"tags": tags})


def kind(request, kind_id):
    tags = Tags.objects.get(id=kind_id)
    books = tags.tags.all()
    return render(request, "user/kind.html", {"books": books})


#周推荐图书（初始版，未使用）
@login_in
def reco_by_week(request):
    page = request.GET.get("page", 1)
    books = books_paginator(recommend_by_user_id(request.session.get("user_id")), page)
    path = request.path
    title = "周推荐图书"
    return render(
        request, "user/item.html", {"books": books, "path": path, "title": title}
    )

#混合协同过滤推荐书籍（月热度）
@login_in
def reco_by_month(request):
    currentUserid = request.session.get("user_id")

    #协同过滤计算评分用户相似度，和与其其他用户的平衡系数W
    similarity_dic, mark_book_number = cosine(currentUserid)
    print("余弦相似度：")
    print(similarity_dic)
    print("平衡系数：")
    print(mark_book_number)
    #欧几里得计算用户特征距离
    euclid_dict = Euclid_Distance(currentUserid)

    #保存各用户最终相似性
    ultimately_list = {}

    # 如果登录用户没有进行评分
    if similarity_dic == 0:
        for key in euclid_dict.keys():
            ultimately_list[key] = (1 / (1 + euclid_dict[key]))
    else:
        for key in similarity_dic.keys():
            sum01= mark_book_number[key] * similarity_dic[key]
            sum02 = (1-mark_book_number[key]) * (1/(1+euclid_dict[key]))
            grade = sum01 + sum02
            ultimately_list[key] = grade
            print("用户ID：",key)
            print("协同过滤：",similarity_dic[key])
            print("平衡系数W：",mark_book_number[key])
            print("欧几里得：",euclid_dict[key])
            print("//////////////////////")
    print("最终相似度列表：")
    print(ultimately_list)

    # 将相似度从大到小进行排序，方便后期推荐书籍
    b = zip(ultimately_list.values(), ultimately_list.keys())  # 转换成（值，键）的元祖类型
    b = list(sorted(b, reverse=True))  # 按照相似度从大到小排序，并转换为列表
    print("排序后的相似度列表：")
    print(b)

    #定义一个空QuerySet存放推荐书籍
    bookid_list = Rate.objects.filter().none()

    kid = 0
    # 用户已经评论过的书籍（不推荐）: user_book_list
    user_book_list = Rate.objects.filter(user_id=currentUserid).values_list("book_id")
    print("用户已评价图书：")
    print(user_book_list)

    # 默认推荐10本书籍,并且用户相似度要大于0.2（考虑到用户没评分时，只能计算欧氏距离，相似度极小，取消0.2限制
    while len(bookid_list) < 10 and kid < len(b)-1:
        # 找出替他用户中评分高（>=3 ）的，并且目标用户没有评论的图书
        # 条件：相似度从大到小的用户；不包含已选择过的图书； 不包含目标用户所评价过的图书；图书的评价必须大于等于3
        bookid_list |= Rate.objects.filter(
            Q(user_id=b[kid][1]) & ~Q(book_id__in=list(bookid_list)) & ~Q(book_id__in=user_book_list) & Q(
                mark__gte=3)).values_list("book_id")
        print("增加其他用户评论后的推荐书单：")
        print(bookid_list)
        kid += 1

    print("最终根据相似度推荐图书：")
    print(bookid_list)

    # 当推荐不够10本时，找阅读量最大的补够10本
    if len(bookid_list) < 10:
        # 过滤条件：没有在协同过滤推荐中的书；没有在已评论过的书；按照阅读量从大到小 ； 补齐10本书
        k = Book.objects.filter(~Q(id__in=bookid_list) & ~Q(id__in=user_book_list)).order_by("-num").all()[
            :10 - len(bookid_list)].values_list("id")

        # QuerySet 合并 必须类型相同，所有去Book中查找一遍
        bookid_list = Book.objects.filter(id__in=bookid_list).values_list("id")
        print("不够10本时：补充书单")
        print(k)
        bookid_list = bookid_list.union(k)  # 将两个书单（QuerySet)合并
        bookid_list = set(i[0] for i in bookid_list)
    print("最终确定推荐书单：")
    print(bookid_list)

    books = Book.objects.filter(id__in=bookid_list).all()
    return render(request, "user/item.html", {"books": books, "title": "混合协同过滤推荐"})


     ## 月推荐图书
    # page = request.GET.get("page", 1)
    # books = books_paginator(recommend_by_user_id(request.session.get("user_id")), page)
    # path = request.path
    # title = "月推荐图书"
    # return render(
    #     request, "user/item.html", {"books": books, "path": path, "title": title}
    # )



def create_book(request, ):
    # 创建书籍
    from django.db import connection, connections

    with open('book.sql', 'r', encoding='utf-8') as f:
        cursor = connection.cursor()  # cursor = connections['default'].cursor()
        for sql in f.readlines():
            # print(sql)
            try:
                cursor.execute(sql)
            except:
                pass

    return redirect(reverse("login", ))


# celery测试
from user.task import start_running
from itertools import chain

from django.db.models import Q
def celery_test(request):
    print('>=====开始发送请求=====<')
    start_running.delay('发送短信')
    # start_running.apply_async(('发送短信',), countdown=10)  # 10秒后再执行异步任务
    return HttpResponse('<h2> 请求已发送 </h2>')

#（未使用）协同过滤（余弦算法）（只基于余弦算法推荐）
@login_in
def recommend(request):
    #返回参数
    data = {}
    #当前登录用户id
    currentUserid = request.session.get("user_id")
    currentUserid = int(currentUserid)
    #获取所有用户评分数据
    scorecords = Rate.objects.all()

    data_dic = {} #创建一个空字典，保存用户-项目评分矩阵
    #遍历评分数据
    for scorecord in scorecords:
        userid = scorecord.user_id    #用户id
        itemid = scorecord.book_id    #书籍id
        rating = int(scorecord.mark)   #评分
        if not userid in data_dic.keys():
            data_dic[userid] = {itemid:rating}
        else:
            data_dic[userid][itemid] = rating

    #没有评分数据或该用户没有评分
    print("当前用户id:")
    print(currentUserid)
    if len(data_dic) == 0 or currentUserid not in data_dic.keys():
        books = Book.objects.order_by("-num","-rate_num").all()[:10]
        return render(request, "user/item.html", {"books": books, "title": "协同过滤推荐"})

    print(data_dic)

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
    print(similarity_dic)
    #将相似度从大到小进行排序，方便后期推荐书籍
    b = zip(similarity_dic.values(),similarity_dic.keys())  #转换成（值，键）的元祖类型
    b = list(sorted(b,reverse = True))  # 按照相似度从大到小排序，并转换为列表
    print(b)
    bookid_list = Rate.objects.filter().none()
    #t_uid = max(similarity_dic,key=similarity_dic.get)  #找出相似度最高的用户id号，再去找他的评价图书
    #bookid_list = Rate.objects.filter(user_id=t_uid).values_list("book_id")
    kid = 0
    # 用户已经评论过的书籍（不推荐）: user_book_list
    user_book_list = Rate.objects.filter(user_id=currentUserid).values_list("book_id")
    print("用户已评价图书：")
    print(user_book_list)

    # 默认推荐10本书籍,并且用户相似度要大于0.7
    while len(bookid_list) <10 and b[kid][0] > 0.7 and kid < len(b):
        # 找出替他用户中评分高（>=3 ）的，并且目标用户没有评论的图书
        #条件：相似度从大到小的用户；不包含已选择过的图书； 不包含目标用户所评价过的图书；图书的评价必须大于等于3
        bookid_list |= Rate.objects.filter(Q(user_id=b[kid][1]) & ~Q(book_id__in=list(bookid_list)) & ~Q(book_id__in=user_book_list) & Q(mark__gte=3)).values_list("book_id")
        print(bookid_list)
        kid += 1

    print("真实推荐图书（相似度推荐）")
    print(bookid_list)
    # 推荐不够10本时，找阅读量最大的补够10本
    if len(bookid_list) < 10:
        #过滤条件：没有在协同过滤推荐中的书；没有在已评论过的书；按照阅读量从大到小 ； 补齐10本书
        k = Book.objects.filter(~Q(id__in=bookid_list) & ~Q(id__in=user_book_list)).order_by("-num").all()[:10-len(bookid_list)].values_list("id")
        print("推荐图书id")

        #QuerySet 合并 必须类型相同，所有去Book中查找一遍
        bookid_list = Book.objects.filter(id__in=bookid_list).values_list("id")
        print(bookid_list)
        print(k)
        bookid_list = bookid_list.union(k) #将两个书单（QuerySet)合并
        bookid_list = set(i[0] for i in bookid_list)
    print(bookid_list)
    #bookid_list = list(chain(bookid_list, k))
    books = Book.objects.filter(id__in=bookid_list).all()

    #books = Book.objects.filter(Q(id__in=bookid_list) | Q(id__in=k))
    #max(similarity_dic[userid])
    return render(request, "user/item.html", {"books": books, "title": "协同过滤推荐"})


#协同过滤（皮尔逊相关系数）未使用
@login_in
def pierxun(request):
    # book = Rate.objects.values("user_id","mark","book_id")
    ss = Rate.objects.values("user_id", "mark", "book_id")
    users = {}
    for i in ss:
        # print(i["user_id"],i["mark"],i["book_id"])
        if i["user_id"] not in users:
            users[i["user_id"]] = {}
        users[i["user_id"]][i["book_id"]] = float(i["mark"])

    class recommender:
        # data：数据集，这里指users
        # k：表示得出最相近的k的近邻
        # metric：表示使用计算相似度的方法
        # n：表示推荐book的个数
        def __init__(self, data, k=5, metric='pearson', n=10):

            self.k = k
            self.n = n
            self.username2id = {}
            self.userid2name = {}
            self.productid2name = {}

            self.metric = metric
            if self.metric == 'pearson':
                self.fn = self.pearson
            if type(data).__name__ == 'dict':
                self.data = data

        def convertProductID2name(self, id):
            if id in self.productid2name:
                return self.productid2name[id]
            else:
                return id

        # 定义的计算相似度的公式，用的是皮尔逊相关系数计算方法
        def pearson(self, rating1, rating2):
            sum_xy = 0
            sum_x = 0
            sum_y = 0
            sum_x2 = 0
            sum_y2 = 0
            n = 0
            print("非目标用户id:")
            print(rating1)
            print(rating2)
            for k_id in rating1:
                print(k_id)
                if k_id in rating2:
                    n += 1
                    x = rating1[k_id]
                    y = rating2[k_id]
                    print("x ,y ", x, y)
                    sum_xy += x * y
                    sum_x += x
                    sum_y += y
                    sum_x2 += pow(x, 2)
                    sum_y2 += pow(y, 2)
                    print("sun_xy,sum_x,sum_y,sum_x2,sum_y2::", sum_xy, sum_x, sum_y, sum_x2, sum_y2)
            if n == 0:
                return 0
            print("n=", n)
            # 皮尔逊相关系数计算公式
            denominator = sqrt(sum_x2 - pow(sum_x, 2) / n) * sqrt(sum_y2 - pow(sum_y, 2) / n)
            print("皮尔逊：", denominator)
            if denominator == 0:
                return 0
            else:
                return (sum_xy - (sum_x * sum_y) / n) / denominator

        def computeNearestNeighbor(self, username):
            distances = []
            for instance in self.data:
                print("目标用户id:")
                print(instance)
                if instance != username:
                    distance = self.fn(self.data[username], self.data[instance])
                    distances.append((instance, distance))

            distances.sort(key=lambda artistTuple: artistTuple[1], reverse=True)
            return distances

        # 推荐算法的主体函数
        def recommend(self, user):
            # 定义一个字典，用来存储推荐的书单和分数
            recommendations = {}
            # 计算出user与所有其他用户的相似度，返回一个list
            nearest = self.computeNearestNeighbor(user)

            userRatings = self.data[user]
            #         print userRatings
            totalDistance = 0.0
            # 得住最近的k个近邻的总距离
            for i in range(self.k):
                totalDistance += nearest[i][1]
            if totalDistance == 0.0:
                totalDistance = 1.0

            # 将与user最相近的k个人中user没有看过的书推荐给user，并且这里又做了一个分数的计算排名
            for i in range(self.k):

                # 第i个人的与user的相似度，转换到[0,1]之间
                weight = nearest[i][1] / totalDistance

                # 第i个人的name
                name = nearest[i][0]

                # 第i个用户看过的书和相应的打分
                neighborRatings = self.data[name]

                for artist in neighborRatings:
                    if not artist in userRatings:
                        if artist not in recommendations:
                            recommendations[artist] = (neighborRatings[artist] * weight)
                        else:
                            recommendations[artist] = (recommendations[artist] + neighborRatings[artist] * weight)

            recommendations = list(recommendations.items())
            recommendations = [(self.convertProductID2name(k), v) for (k, v) in recommendations]

            # 做了一个排序
            recommendations.sort(key=lambda artistTuple: artistTuple[1], reverse=True)

            return recommendations[:self.n], nearest

    def adjustrecommend(id):
        bookid_list = []
        r = recommender(users)
        k, nearuser = r.recommend(id)
        for i in range(len(k)):
            bookid_list.append(k[i][0])
        # bookid_list推荐书籍的id，nearuser[:3]最近邻的3个用户
        return bookid_list, nearuser[:5]

    # user_id：需要查询的用户id
    user_id = request.session.get("user_id")
    bookid_list, near_list = adjustrecommend(user_id)
    print("bookid_list:", bookid_list)
    print("near_list:", near_list)
    books = Book.objects.filter(id__in=bookid_list)
    return render(request, "user/item.html", {"books": books, "title": "协同过滤推荐（皮尔逊系数）"})


#余弦相似度、平衡系数:W
def cosine(currentUserid):
    # 返回参数
    data = {}
    # 当用户没有评分书籍时
    if Rate.objects.filter(user_id=currentUserid).count() == 0:
        print("此用户没有评分，余弦相似度为：0，平衡系数为：0")
        return 0,0

    # 获取所有用户评分数据
    scorecords = Rate.objects.all()
    data_dic = {}  # 创建一个空字典，保存用户-项目评分矩阵
    # 遍历评分数据
    for scorecord in scorecords:
        userid = scorecord.user_id  # 用户id
        itemid = scorecord.book_id  # 书籍id
        rating = int(scorecord.mark)  # 评分
        if not userid in data_dic.keys():
            data_dic[userid] = {itemid: rating}
        else:
            data_dic[userid][itemid] = rating
    print("所有用户评分，格式：{用户id:{书id:评分。。。}。。。}  ")
    print(data_dic)

    # 保存每名用户评分的图书数量
    user_book_list = list(data_dic[currentUserid].keys())
    print("当前用户评分书籍id：")
    print(user_book_list)
    print("书籍个数：")
    print(len(user_book_list))
    mark_book_number = {}
    #计算平衡系数:W （共同评分数占双方总评分数）
    for key in data_dic.keys():
        if key != currentUserid:
            other_list = list(data_dic[key].keys())
            inter = len(list(set(user_book_list).intersection(set(other_list))))
            un = len(list(set(user_book_list).union(set(other_list))))
            mark_book_number[key] = inter / un
    print("平衡系数W:")
    print(mark_book_number)

    # 计算用户相似度（余弦算法）
    similarity_dic = {}
    for userid, items in data_dic.items():  # 遍历所有用户
        if currentUserid != userid:  # 非目标用户
            # 余弦算法
            # 计算分子
            temp = 0
            temp2 = 0
            temp3 = 0
            for itemid, rating in data_dic[currentUserid].items():  # 遍历目标用户评分项目
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
            print("用户:" + str(userid) + " ，余弦相似度： ")
            print(similarity_dic[userid])
    print(similarity_dic)
    return similarity_dic,mark_book_number

#欧几里得距离
def Euclid_Distance(currentUserid):
    ss = User.objects.values("id", "sex", "age", "address", "work")
    print("所有用户特征信息：")
    print(ss)
    k = []
    current_list = []
    user_list = []
    print("各用户特征信息值：id、性别、年龄、国家、工作")
    for i in ss:
        print(i)
        if i["id"] == currentUserid:
            current_list = [i["sex"], i["age"], i["address"], i["work"]]
        else:
            user_list.append(i["id"])
            k.append([i["sex"], i["age"], i["address"], i["work"]])
    print("非登录用户特征提取为矩阵：")
    print(k)
    print("非登录用户id：")
    print(user_list)
    print("非登录用户个数：")
    print(len(user_list))

    #保存各非登录用户与登录用户的欧几里得距离
    euclid_dict = {}
    # 欧几里得距离：计算目标用户与其他用户
    for i in range(0, len(user_list)):
        kk = np.sqrt(((np.array(current_list) - np.array(k[i])) ** 2).sum())
        euclid_dict[user_list[i]] = kk
    print("登录与非登录用户的欧几里得距离：id : 距离")
    print(euclid_dict)
    return euclid_dict

