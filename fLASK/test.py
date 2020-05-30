from fLASK.app import Cold,View,session,url_for
import json
from app import *   #init
from werkzeug.utils import redirect   #重定向
from fLASK.orm import Model,StringField  #数据库简单操作

class User(Model):
    __table__ = 'users'
    __database__='my_user'
    id = StringField(primary_key=True, ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    name = StringField(ddl='varchar(50)')

class mysql(View):
    def GET(self,request):
        user1 = User.filter(where="name='cold2'")[0]
        print(user1)
        name = user1.get('name')
        passwd=user1.get('passwd')
        return render_template("index.html", name=name,passwd=passwd)


class Index(View):
    def GET(self,request,x):
        # session['hello'] = 2
        # return redirect(url_for())
        return 'helloer'
    def POST(self,request):
        print(json.dumps(request.form['color']))
        return json.dumps({'1':'hello'})

class Test(View):
    def GET(self,request):
        # print(session['hello1'])
        print(redirect('/red'))
        return redirect('/red')
    def POST(self,request):
        return json.dumps({'2':'hello'})

class red(View):
    def GET(self,request):
        session['name']='cold'
        return '<h1> 302 success </h1>'

class URL(View):
    def GET(self,request):
        session['name']='URL'
        return redirect(url_for('11'))

urls = {'/<x>':Index,
        '/test':Test,
        '/red':red,
        '/mysql':mysql,
        '/URL':URL}

app = Cold()
app.secret_key = 'password'

app.add_url_rule(urls)
app.run()
