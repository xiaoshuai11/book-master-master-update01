from django import forms
from .models import *


class Login(forms.Form):
    username = forms.CharField(
        label="用户名",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control required"}),
    )
    password = forms.CharField(
        label="密码",
        widget=forms.PasswordInput(attrs={"class": "form-control required"}),
    )


class Edit(forms.ModelForm):
    class Meta:
        model = User
        fields = ["password", "name", "email", "address", "phone"]
        laebls = {
            "password": "密码",
            "name": "昵称",
            "email": "邮箱",
            "address": "国家",
            "phone": "手机号码",
        }
        widgets = {
            "password": forms.PasswordInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.NumberInput(attrs={"class": "form-control"}),
            "phone": forms.NumberInput(attrs={"class": "form-control"}),
        }

        # def clean_name(self):
        #     name = self.cleaned_data.get("name")
        #     result = User.objects.filter(name=name)
        #     if result:
        #         raise form.ValidationError("Name already exists")
        #     return name


class RegisterForm(forms.ModelForm):
    """
    username = forms.CharField(
        label="用户名",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    age = forms.IntegerField(
        label="年龄",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    work = forms.IntegerField(
        label="工作",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="邮箱", widget=forms.EmailInput(attrs={"class": "form-control"})
    )
    name = forms.CharField(
        label="姓名",
        max_length=128,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    phone = forms.CharField(
        label="手机",
        max_length=128,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    address = forms.CharField(
        label="地址",
        max_length=128,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    """
    password1 = forms.CharField(label='密码', widget=forms.PasswordInput(),
                                error_messages={'required': '密码不能为空'})

    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput(),
                                       error_messages={'required': '重复密码不能为空'})
    age = forms.IntegerField(
        min_value=1,
        max_value=140,
        label="年龄",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    class Meta:
        model = User
        # fields = "__all__"    #使用默认顺序展示
        # 自定义展示顺序
        fields = ['username','password1','password2','sex','age','name', 'work','phone','email','address']

        # 重新ModelForm  __init__ 改变页面格式
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 将每一个格式添加 class = 'form-control' ，和 'placeholder' 属性
        for name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = '请输入%s' % (field.label,)

    def clean_username(self):
        username = self.cleaned_data.get("username")

        if len(username) < 1:
            raise forms.ValidationError(
                "Your username must be at least 6 characters long."
            )
        elif len(username) > 50:
            raise forms.ValidationError("用户名太长啦")
        else:
            filter_result = User.objects.filter(username=username)
            if len(filter_result) > 0:
                raise forms.ValidationError("用户名已存在")
        return username

    def clean_name(self):
        name = self.cleaned_data.get("name")
        filter_result = User.objects.filter(name=name)
        if len(filter_result) > 0:
            raise forms.ValidationError("名字已存在")
        return name

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 6:
            raise forms.ValidationError("密码太短啦")
        elif len(password1) > 20:
            raise forms.ValidationError("密码太长啦.")
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("密码输入不匹配，请再输入一次")
        return password2
