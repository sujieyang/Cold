import os
from werkzeug.wrappers import Request, Response   #Request 和Response 反应
from werkzeug.exceptions import HTTPException, MethodNotAllowed, \
     NotImplemented, NotFound
from werkzeug.routing import Map, Rule    #Map  存储保存路由，Rule设置规则
from werkzeug.serving import run_simple
from werkzeug.local import LocalStack,LocalProxy
from jinja2 import Environment,FileSystemLoader  #增加templates模板
from werkzeug.contrib.securecookie import SecureCookie    #cookie模板

url_map=Map()    # 全局的url映射
views = {}              # 存储endpoint到处理函数的映射


class Request(Request):
    """Encapsulates a request."""


class Response(Response):
    """Encapsulates a response."""

class _RequestContext(object):
    """请求上下文（request context）包含所有请求相关的信息。它会在请求进入时被创建，
    然后被推送到_request_ctx_stack，在请求结束时会被相应的移除。它会为提供的
    WSGI环境创建URL适配器（adapter）和请求对象。
    """
    def __init__(self, app, environ):
        self.app = app
        self.url_adapter = app.url_map.bind_to_environ(environ) # url适配器，绑定
        self.request = Request(environ)
        self.session = app.open_session(self.request)

    def __enter__(self):
        # print(self.test)
        _request_stk.push(self)

    def __exit__(self, exc_type, exc_value, tb):
        # 在调试模式（debug mode）而且有异常发生时，不要移除（pop）请求堆栈。
        if tb is None or not self.app.debug:
            _request_stk.pop()

#模板
def render_template(template_name,**context):
    '''
    :param template_name:模板名字
    :param context: 传递给模板的字典参数
    :return: template
    '''
    template_path = os.path.join(os.getcwd(), 'templates')
    jinja_env = Environment(loader=FileSystemLoader(template_path), autoescape=True)
    return jinja_env.get_template(template_name).render(context)



def url_for(endpoint, filename=None,force_extenal=False):
    if filename is not None:
        file_path = os.path.join(filename, '\%s' % endpoint)
        return file_path
    urls = url_map.bind("127.0.0.1")
    relative_url = urls.build(endpoint,force_external=force_extenal)
    print(relative_url)
    return relative_url


class View(object):
    """Baseclass for our views."""
    def __init__(self):
        self.methods_meta = {
            'GET': self.GET,
            'POST': self.POST,
            'PUT': self.PUT,
            'DELETE': self.DELETE,
        }
    def GET(self):
        raise MethodNotAllowed()  #405
    POST = DELETE = PUT = GET

    def HEAD(self):
        return self.GET()

    def dispatch_request(self, request, *args, **options):  #request
        if request.method in self.methods_meta:
            return self.methods_meta[request.method](request, *args, **options)
        else:
            return '<h1>Unsupported require method</h1>'

    @classmethod
    def get_func(cls):
        def func(*args, **kwargs):
            obj = func.view_class()
            return obj.dispatch_request(*args, **kwargs)
        func.view_class = cls
        return func

class Cold(object):
    secret_key = None
    # 加密组件可以使用它来作为cookies或其他东西的签名。
    debug = True
    def __init__(self):
        self.url_map = url_map
        self.view = views

    def request_context(self,environ):  #上下文
        return _RequestContext(self,environ)

    def process_response(self,response):
        session = _request_stk.top.session
        if session is not None:
            self.save_session(session,response)
        return response

    def make_response(self, Re):    #处理对象类型
        # 判断Re的类型
        if isinstance(Re, Response):
            return Re
        if isinstance(Re, str):
            return Response(Re)
        if isinstance(Re, tuple):
            return Response(*Re)
        return Response.force_type(Re, request.environ)

    def wsgi_app(self,environ,start_response):
        with self.request_context(environ):  #上下文
            req = Request(environ)
            response = self.dispatch_request(req)  #响应
            if response:#如果可以找到正确的匹配项
                # response = Response(response, content_type='text/html; charset=UTF-8')
                response = self.make_response(response)
                response = self.process_response(response)
            else:#找不到，返回404NotFound
                response = Response('<h1>404 Not Found<h1>', content_type='text/html; charset=UTF-8', status=404)

            return response(environ, start_response)


    def open_session(self, request):#
        """
        :param request: Request实例
        """
        #创建或打开一个新的session，默认的实现是存储所有的session数据到一个签名的cookie中，
        # 前提是secret_key属性被设置
        key = self.secret_key
        if key is not None:
            return SecureCookie.load_cookie(request, 'session', secret_key=key)

    def save_session(self, session, response):
        #print(response)
        if session is not None:
             session.save_cookie(response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def dispatch_request(self, req):
        urls = self.url_map.bind_to_environ(req.environ)
        self.url_map.bind_to_environ(req.environ)
        try:
            endpoint, value = urls.match()
            print(self.view[endpoint](req, **value))
            return self.view[endpoint](req, **value)
        except HTTPException as e:
            response = e
        return response

    def add_url_rule(self,urls):  #添加路由
        #for url in urls:
            #self.url_map[url] = urls[url].get_func()
        for url in urls:
            self.url_map.add(Rule(url,endpoint=str(urls[url])))
            self.view[str(urls[url])] = urls[url].get_func()

    def run(self, port=5000, ip='127.0.0.1', debug=True):
        run_simple(ip, port, self, use_debugger=debug, use_reloader=True)


_request_stk = LocalStack()  #栈
current_app = LocalProxy(lambda: _request_stk.top.app)
#对LocalStack 进行封装，current_app是一个上下文代理
request = LocalProxy(lambda: _request_stk.top.request)
session = LocalProxy(lambda: _request_stk.top.session)
#request封装了客户端的请求信息和session代表了用户会话信息