## Yagra


### 系统功能

* 用户注册、登录、登出
* 用户上传图片、管理图片设置为头像
* 用户头像访问 API


### 系统依赖

* 简单部署
    * Python v2.7
    * MySQL v5.6
    * MySQL-python v1.2.5
    * Apache 2

* Docker 部署
    * Docker version >= 1.3.1
    * Docker镜像
        * 可以具体查看对应的 mkxxxxx.sh 脚本
        * yagra-mysql: FROM mysql:5.6
        * yagra-apache: FROM debian:wheezy
            * apt-get install -y git apache2 python python-dev libmysqlclient-dev python-pip
            * pip install -r requirements.txt
            * only MySQL-python==1.2.5 in requirements.txt
        * yagra-db_scheme_loader: FROM debian:wheezy
            * apt-get install -y mysql-client netcat
        * yagra-nginx: FROM nginx:1.7


### 模块设计与实现

* CGI 请求处理
    * 利用 Apache 提供的 CGI 支持和 URL 重写功能，将用户请求统一转发到指定的处理入口（main.py）
    * 读取 CGI 请求的环境变量，根据 REQUEST_URI 的 path 部分选择对应的处理逻辑
    * 生成请求处理的结果，通过标准输出流写回

* typhoon 微框架
    * 在 typhoon 包中封装了对 CGI 请求的处理逻辑，该框架借鉴了 [Tornado](https://github.com/tornadoweb/tornado) 的处理逻辑，包括几个重要的核心模块。
        * Application: 对 handler 和完整 CGI 请求处理的封装
        * URLSpec: 基于正则，实现从 URL 到处理逻辑类（handler）的映射
        * CGIConnection: 封装了标准输出流的操作
        * CGIRequest: 封装了 CGI 请求的环境变量
        * RequestHandler: 请求处理逻辑类的基类，封装了大量的对请求处理的操作
    * 模板引擎
        * 系统基于正则表达式实现了一个简单的模板渲染器，用于 html 代码的生成
        * 模板引擎先根据指定的符号表（TOKEN）将模板符号化，渲染过程按照遇到的符号顺序，找出特定的渲染块，每个渲染区域有独立的上下文（对应不同的 python 变量），按照顺序独立渲染得到最后的结果
        * 目前支持注释、变量使用、特定表达式（包括 if, for）和 include 文件
    * 内置日志系统
        * 初始化 Application 对象时初始化内置日志，使用 python 内置的日志模块

* 代码结构
    * handler: 负责具体的逻辑处理
    * model: 封装到数据库的处理逻辑
    * form: 提供部分基础的表单验证
    * common:
        * session.py: 简单的 session 实现
        * db.py: 数据库操作抽象
    * templates: html 模板
    * static: 静态文件
    * main.py: CGI 执行入口
    * config.py.example: 配置文件模板，运行时修改为 config.py

* 系统的一些功能特性
    * 用户请求如果不需要访问数据库则不需初始化数据库连接
    * 数据库连接对象为单例模式，同一次请求多次访问数据库会共用此连接
    * 使用参数化查询避免 SQL 注入 [A guide to preventing SQL injection](http://bobby-tables.com/python.html)
    * POST 请求进行 xsrf 验证
    * POST 请求比较完整的后端验证（前后端都存在验证）
    * 根据文件头部数据简单判断图片类型，拒绝非法文件格式
    * 用户上传图片会根据内容计算 MD5，同一用户不会重复上传同一张图片

* 数据库设计
    * 表结构，包括 yagra_user, yagra_image, yagra_session 三张表，详细表结构参见 [yagra_scheme.sql](https://github.com/amyangfei/avatar-host-py/blob/master/deploy/yagra_scheme.sql)
    * 用户头像与图片的关联：图片表的每一行记录对应一张图片，每张图片只属于一个用户并且会记录该用户的 user_id；如果一张图片被选做为用户的头像，那么它的的 email_md5 字段为该用户的 email 的 MD5 值；所以属于同一个用户的所有图片记录最多有一个 email_md5 字段非空；用户表会记录它的头像对应的图片 id，这样方便查询。
    * 注意的问题：用户修改头像是会同时对 yagra_user 表和 yagra_image 表进行操作，系统将这一系列操作放在一个事务中（MySQL 使用 InnoDB 引擎支持事务）。

### 系统部署

* Docker 部署
    * 系统提供了基于 docker 的自动化部署脚本，[安装 docker](https://docs.docker.com/installation/)。（在Docker version 1.3.1, build 4e9bbfa 以及 Docker version 1.5.0, build a8a31ef 中测试过脚本，正常运行），然后执行下边的操作，你就会获得完整的 docker 镜像并启动了相应的容器。

            $ git clone https://github.com/amyangfei/avatar-host-py
            $ cd docker
            $ ./docker_build.sh clean-start

    * 脚本说明
        * docker_build.sh: 控制脚本
        * mkxxxxx.sh: 创建 docker 镜像的脚本，对应于 4 个镜像
        * load_scheme.sh: yagra-db_scheme_loader 容器启动执行的脚本，主要目的是通过 nc 检测 yagra-mysql 容器中 MySQL 服务是否启动完成
        * conf/*: 容器内运行程序使用的配置文件，可根据情况适当配置

    * 系统使用了 4 个容器
        * yagra-mysql: 独立运行 MySQL 数据库
        * yagra-apache: 运行 Apache2, 提供 CGI 服务，代码执行、文件上传都在此容器执行
        * yagra-db_scheme_loader: 用于首次运行装载数据库结构，运行后自动删除
        * yagra-nginx: 独立运行 Nginx，作为 yagra-apache 的前端

    * 安装注意
        * 启动容器的顺序一定为：yagra-mysql -> yagra-apache -> yagra-db_scheme_loader/yagra-nginx，这与容器之间的 link 有关
        * nginx 和 apache 的配置中使用了 ServerName(server_name)，实际部署需要按照情况修改 <code>docker/conf/apache_yagra.conf</code>，<code>docker/conf/nginx_yagra.conf</code> 中的 ServerName(server_name)
        * 或测试时修改 hosts <code>specific_ip_or_dnsname yagra.mxiaonao.me</code>

    * 仍存在的问题
        * 数据存放在运行的容器中，包括 Nginx/Apache/App 的日志，上传的文件和数据库数据。Docker 提供了两种方案：数据卷和数据卷容器。但实际使用存在问题，问题如下：
            * 目前容器访问共享的数据卷和数据卷容器，需要具有 root 权限，在我们的容器中运行的命令不全部是由 root 用户运行的。（当然可以选择全部通过 root 用户运行，那样问题就可以得到解决，但是就不能使用官方的 mysql 容器等）
            * Docker 社区对此也存在很多讨论：[github issue 7198](https://github.com/docker/docker/issues/7198)，[github issue 3124](https://github.com/docker/docker/issues/3124)
