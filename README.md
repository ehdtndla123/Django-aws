# Docker Compose로 서비스 해보기 with Aws



# 프로젝트 의의

AWS RDS 를 이용하여 데이터베이스를 구축하고 AWS 클라우드의 가상 서버에 

Django, Nginx 를 Docker 이미지로 만들어서 docker-compose로 복수 개의 컨테이너를 실행시킨다.



### AWS RDS 사용하기

![image](https://user-images.githubusercontent.com/59868624/184950089-7906c3f3-d890-412e-9e72-9b3d31e594f1.png)

```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'project1',
        'USER':'admin',
        'PASSWORD':'비밀번호',
        'HOST':'database-1.cekdulhkgjrx.ap-northeast-2.rds.amazonaws.com',
        'PORT':'3306',
        'OPTIONS':{
            'init_command':'SET sql_mode="STRICT_TRANS_TABLES"'
        }
    }
}
```



### 패키지 종속성 관리

현재 환경에서 설치한 패키지를 알려주는 txt 파일을 만들고 github에 같이 올려주자.

```
pip freeze > requirements.txt
```



## Aws 인스턴스 사용하기

![image](https://user-images.githubusercontent.com/59868624/184950259-0727d951-cdd0-46f0-b3c8-48eaa6fc4933.png)



ubuntu t2.micro 를 이용하였다.

배포가 아닌 Docker compose를 이용하기 위해 한것이므로 보안 그룹 에서 인바운드 규칙은 모두 열어주었다.

![image](https://user-images.githubusercontent.com/59868624/184950429-f20d8639-90b3-40cd-8fb5-6f5d57b96c8d.png)



인스턴스에 접속해보자.

```
ssh -i [keypair] ubuntu@[ip]
```



docker-server 폴더를 만든 후 깃허브에 올린 Django를 clone 한다.

```
mkdir docker-server
cd docker-server
git clone https://github.com/ehdtndla123/Django-aws.git
```



### 도커 다운로드

```
# 도커 다운로드
curl -fsSL https://get.docker.com/|sudo sh
# 도커 권한 설정, 컨테이너 두개 이상일경우 연결시키고 유기적으로 활용할려면 필요함 compose 사용하기때문에
sudo usermod -aG docker $USER
```

> 인스턴스에서 exit하고 다시 들어와서 권한 설정한 것을 적용하자



### Django Dockerfile 작성

```
# 도커 파일 작성
vi Dockerfile

##### vi start Dockerfile
FROM python:3.10.6

# image가 올라갔을 때 수행되는 명령어들
# -y 옵션을 넣어서 무조건 설치가 가능하도록 한다.
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update
RUN apt-get -y install vim

RUN mkdir /srv/docker-server
ADD . /srv/docker-server

WORKDIR /srv/docker-server

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

##### vi end
```



### Docker image 생성

```
# docker/django 라는 이미지 이름을 현재 디렉토리에서 실행시킨다.
docker build -t docker/django .
```



### Django 폴더에 uwsgi.ini 파일 생성

```
vi uwsgi.ini

##### vi start uwsgi.ini
[uwsgi]
socket = /srv/docker-server/apps.sock
master = true

processes = 1
threads = 2

chdir = /srv/docker-server
module = Django-aws.wsgi

logto = /var/log/uwsgi/uwsgi.log
log-reopen = true

vacuum = true
##### vi end
```



### Nginx 폴더 생성

```
mkdir nginx
cd nginx
```



### Nginx 설정 파일 생성

```
vi nginx.conf

##### vi start nginx.conf
user root;
worker_processes auto;
pid /run/nginx.pid;

events {
    worker_connections 1024;
    # multi_accept on;
}

http {

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ssl_protocols TLSv1 TLSv1.1 TLSv1.2; # Dropping SSLv3, ref: POODLE
    ssl_prefer_server_ciphers on;

    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    gzip on;
    gzip_disable "msie6";

    include /etc/nginx/sites-enabled/*;
}
##### vi end


vi nginx-app.conf

##### vi start nginx-app.conf
upstream uwsgi {
    server unix:/srv/docker-server/apps.sock;
}

server {
    listen 80;
    server_name localhost;
    charset utf-8;
    client_max_body_size 128M;

    location / {
        uwsgi_pass      uwsgi;
        include         uwsgi_params;
    }

    location /media/ {
        alias /srv/docker-server/.media/;
    }

    location /static/ {
        alias /srv/docker-server/.static/;
    }
}
##### vi end
```



### Nginx Dockerfile 작성

```
vi Dockerfile

##### vi start Dockerfile
FROM nginx:latest

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx-app.conf /etc/nginx/sites-available/

RUN mkdir -p /etc/nginx/sites-enabled/\
    && ln -s /etc/nginx/sites-available/nginx-app.conf /etc/nginx/sites-enabled/

CMD ["nginx","-g","daemon off;"]

##### vi end
```



### Nginx Image 생성

```
docker build -t docker/nginx .
```



#### **nginx가 동작하기 위해선 django가 먼저 동작하고 nginx 가 동작해야한다.**



### docker-compose 다운로드

```
sudo curl -L https://github.com/docker/compose/releases/download/1.25.0-rc2/docker-compose-
`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
# 권한 설정
sudo chmod +x /usr/local/bin/docker-compose
```



### docker-compose.yml 생성

```
vi docker-compose.yml

##### vi start docker-compose.yml
version: '3'
services:

    nginx:
        container_name: nginx
        build: ./nginx
        image: docker-server/nginx
        restart: always
        ports:
          - "80:80"
        volumes:
          - ./Django-aws:/srv/docker-server
          - ./log:/var/log/nginx
        depends_on:
          - django

    django:
        container_name: django
        build: ./Django-aws
        image: docker-server/django
        restart: always
        command: uwsgi --ini uwsgi.ini
        volumes:
          - ./Django-aws:/srv/docker-server
          - ./log:/var/log/uwsgi
##### vi end
# depends_on django 없으면 실행되지 않도록해라 라는 뜻이다.
```



### docker-compose build

```
docker-compose up -d --build
```



돌아가는지 확인해보자

```
docker-compose ps
```

