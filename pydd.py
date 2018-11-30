from config import *
import os, importlib,shutil

# settings = importlib.import_module(PROJECT_NAME+'.'+PROJECT_NAME+'.settings')
########################################################################
STATIC_ROOT='/static-data'
MEDIA_ROOT='/media-data'
LOGS_ROOT='/logs-data'

dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path = dir_path.replace("\\","/")
folder_to_save = 'djd_data/'

if not os.path.exists(folder_to_save):
  os.makedirs(folder_to_save)
else:
  shutil.rmtree(folder_to_save)
  os.makedirs(folder_to_save)

if DATABASE_EXTERNAL:
  WEB_ENVIROMENT['DATABASE_HOST']=DATABASE_HOST_EXTERNAL
else:
  WEB_ENVIROMENT['DATABASE_HOST']=DATABASE_IMAGE

WEB_ENVIROMENT['DEBUG']=str(DEBUG)
WEB_ENVIROMENT['STATIC_ROOT']=STATIC_ROOT
WEB_ENVIROMENT['MEDIA_ROOT']=MEDIA_ROOT
WEB_ENVIROMENT['DATABASE_PORT']=DATABASE_PORT
WEB_ENVIROMENT['DATABASE_NAME'] = DATABASE_DEFAULT_ENVIROMENTS['DATABASE_DB_VALUE']
WEB_ENVIROMENT['DATABASE_USER'] = DATABASE_DEFAULT_ENVIROMENTS['DATABASE_USER_VALUE']
WEB_ENVIROMENT['DATABASE_PASSWORD'] = DATABASE_DEFAULT_ENVIROMENTS['DATABASE_PASSWORD_VALUE']
WEB_ENVIROMENT['STATIC_URL']='/static/'
WEB_ENVIROMENT['MEDIA_URL']='/media/'

RUNSERVER_SCRIPT_NAME='runserver'

REQUIREMENTS+=[
'django',
'gunicorn',
'python-decouple',
] # adiciona django e gunicorn a requirements
#######################################################################
# Dicionario base
DOCKER={
	'REQUIREMENTS':REQUIREMENTS,
	'PROJECT_NAME':PROJECT_NAME,
	'RUNSERVER_SCRIPT_NAME':RUNSERVER_SCRIPT_NAME,
	'STATIC_ROOT':STATIC_ROOT,
  'MEDIA_ROOT':MEDIA_ROOT,
	'WEB_PORT':WEB_PORT,
	'DATABASE':DATABASE_IMAGE,
	'WEB_ENVIROMENT':WEB_ENVIROMENT,
#	'DATABASE_ROOT_SOURCE':DATABASE_ROOT['SOURCE'],
	'DATABASE_ROOT_DESTINATION':DATABASE_ROOT['DESTINATION'],
	'LOGS_ROOT':LOGS_ROOT,
  'DOCKER_COMPOSE_VERSION':DOCKER_COMPOSE_VERSION,
  'PYTHON_VERSION':PYTHON_VERSION,
  'DATABASE_HOST':WEB_ENVIROMENT['DATABASE_HOST'],
  'DATABASE_DB_NAME':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_DB_NAME'],
  'DATABASE_USER_NAME':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_USER_NAME'],
  'DATABASE_PASSWORD_NAME':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_PASSWORD_NAME'],
  'DATABASE_DB_VALUE':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_DB_VALUE'],
  'DATABASE_USER_VALUE':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_USER_VALUE'],
  'DATABASE_PASSWORD_VALUE':DATABASE_DEFAULT_ENVIROMENTS['DATABASE_PASSWORD_VALUE'],
  'DATABASE_PORT':DATABASE_PORT,
  'NETWORK_NAME':NETWORK_NAME,
  'FOLDER_NAME':folder_to_save,
  'DIR_PATH':dir_path,
  'SCSS_FOLDERS':SCSS_TO_CSS_FOLDERS[0],
  'CSS_FOLDERS':SCSS_TO_CSS_FOLDERS[1],
  'JS_FOLDERS':JS_TO_JSMIN_FOLDERS[0],
  'JSMIN_FOLDERS':JS_TO_JSMIN_FOLDERS[1],
  'IMAGE_FOLDERS':IMAGE_TO_IMAGEMIN_FOLDERS[0],
  'IMAGEMIN_FOLDERS':IMAGE_TO_IMAGEMIN_FOLDERS[1]
}
########################################################################
# DEPENDS_ON='''depends_on:
#    - {DATABASE}
#  '''.format(**DOCKER)
DEPENDS_ON='''depends_on:'''
if not DATABASE_EXTERNAL:
  DEPENDS_ON+='''
   - {DATABASE}'''.format(**DOCKER) 
if len(CONTAINERS) >= 1:
  for container in CONTAINERS:
    DEPENDS_ON+='''
   - {}'''.format(container)

DOCKER['DEPENDS_ON']=DEPENDS_ON
##########################################################################
if len(WEB_ENVIROMENT) >= 1:
  ENVIROMENT='''environment:'''
  for key in WEB_ENVIROMENT:
  	ENVIROMENT+='''
   - {}={}'''.format(key,WEB_ENVIROMENT[key])
  DOCKER['ENVIROMENT']=ENVIROMENT
else:
  DOCKER['ENVIROMENT']=''
#########################################################################
NETWORK='''
volumes:
 database:
networks:
 {NETWORK_NAME}:
'''.format(**DOCKER)
##########################################################################
#arquivo dockerfile
DOCKERFILE="""FROM python:{PYTHON_VERSION}
ENV PYTHONUNBUFFERED 1
RUN set -ex && apt-get update
COPY {FOLDER_NAME}requirements.txt ./requirements.txt
RUN set -ex && pip install -r requirements.txt
ADD ./{PROJECT_NAME} /{PROJECT_NAME}
WORKDIR /{PROJECT_NAME}
""".format(**DOCKER)
if len(WEB_COMMANDS_BUILD) >= 1:
  for command in WEB_COMMANDS_BUILD:
    DOCKERFILE+='RUN set -ex && '+command+'\n'
DOCKERFILE_FINAL_LINE='''CMD chmod +x {RUNSERVER_SCRIPT_NAME}.sh'''.format(**DOCKER)
DOCKERFILE+=DOCKERFILE_FINAL_LINE

##########################################################################
#brosersync dockerfile
BROWSERSYNC_DOCKERFILE='''
FROM node
RUN set -ex && apt-get update
RUN set -ex && npm install -g yarn
RUN set -ex && yarn global add gulp-cli
RUN set -ex && yarn global add browser-sync
ADD ./{PROJECT_NAME} /{PROJECT_NAME}
WORKDIR /{PROJECT_NAME}
USER node
'''.format(**DOCKER)
#################################################################
GULPSH = '''
#!/bin/bash
file="./package.json"
if [ ! -f "$file" ]
then
  yarn add gulp
  yarn add node-sass
  yarn add browser-sync
  yarn add gulp-sass
  yarn add gulp-rename
  yarn add gulp-autoprefixer
  yarn add gulp-uglify
  yarn add gulp-sourcemaps
  yarn add gulp-imagemin
  gulp
else
  yarn
  gulp
fi
'''
#################################################################
#browse-sync compose
BROWSER_SYNC_DOCKERCOMPOSE='''
 browsersync:
  container_name: browsersync
  build:
   context: "{DIR_PATH}"
   dockerfile: {FOLDER_NAME}browsersync.Dockerfile
  restart: always
  ports:
   - 3000:3000
   - 3001:3001
   - 3002:3002
  volumes:
   - "{DIR_PATH}/{PROJECT_NAME}:/{PROJECT_NAME}:rw"
  depends_on:
   - web
  working_dir: /{PROJECT_NAME}
  command: bash gulp.sh
  stdin_open: true
  tty: true
  networks:
   - {NETWORK_NAME}
  '''.format(**DOCKER)
############################################################################

RUNSERVER_SCRIPT='''#!/bin/bash
python manage.py makemigrations
python manage.py migrate'''

#############################################################################
# arquivo yml para docker compose
DOCKERCOMPOSE_BASE='''
version: '{DOCKER_COMPOSE_VERSION}'
services:
 web:
  container_name: web
  build:
   context: "{DIR_PATH}"
   dockerfile: {FOLDER_NAME}{PROJECT_NAME}.Dockerfile
  restart: always
  ports:
   - {WEB_PORT}:{WEB_PORT}
  expose:
   - {WEB_PORT}
  working_dir: /{PROJECT_NAME}
  command: ./wait-for-it.sh {DATABASE_HOST}:{DATABASE_PORT} --timeout=15 --strict -- /bin/bash {RUNSERVER_SCRIPT_NAME}.sh
  {DEPENDS_ON}
  {ENVIROMENT}
  stdin_open: true
  tty: true
  networks:
   - {NETWORK_NAME}'''.format(**DOCKER)
###################################################################################
VOLUMES_DEVELOPMENT='''
  volumes:
   - "{DIR_PATH}/{PROJECT_NAME}:/{PROJECT_NAME}:rw" 
   - "{DIR_PATH}/media:{MEDIA_ROOT}:rw"
'''.format(**DOCKER)

VOLUMES_PRODUCTION='''
  volumes:
   - "{DIR_PATH}/static:{STATIC_ROOT}:rw"
   - "{DIR_PATH}/media:{MEDIA_ROOT}:rw"
'''.format(**DOCKER)

DATABASE_BASE=''' 

 {DATABASE}:
  image: {DATABASE}
  container_name: {DATABASE}
  restart: always
  networks:
   - {NETWORK_NAME}
  volumes:
   - database:{DATABASE_ROOT_DESTINATION}
  environment:
   - {DATABASE_USER_NAME}={DATABASE_USER_VALUE}
   - {DATABASE_PASSWORD_NAME}={DATABASE_PASSWORD_VALUE}
   - {DATABASE_DB_NAME}={DATABASE_DB_VALUE}
   '''.format(**DOCKER)

if not DATABASE_EXTERNAL:
  DOCKERCOMPOSE_DEVELOPMENT = DOCKERCOMPOSE_BASE + VOLUMES_DEVELOPMENT + DATABASE_BASE
  DOCKERCOMPOSE_PRODUCTION = DOCKERCOMPOSE_BASE + VOLUMES_PRODUCTION + DATABASE_BASE
else:
  DOCKERCOMPOSE_DEVELOPMENT = DOCKERCOMPOSE_BASE + VOLUMES_DEVELOPMENT 
  DOCKERCOMPOSE_PRODUCTION = DOCKERCOMPOSE_BASE + VOLUMES_PRODUCTION 
##########################################################################
if not DATABASE_EXTERNAL:
  if len(DATABASE_OTHERS_ENVIROMENTS) >= 1:
    DOE=''
    for key in DATABASE_OTHERS_ENVIROMENTS:
      DOE+='''- {}={}'''.format(key,DATABASE_OTHERS_ENVIROMENTS[key])
    DOCKERCOMPOSE_DEVELOPMENT+=DOE
    DOCKERCOMPOSE_PRODUCTION+=DOE

###########################################################################
# adiciona containers
for container in CONTAINERS:
  CONTAINERS_STRUCT='''
  
 {}:
  image: {}
  container_name: {}
  restart: always
  networks:
   - {}
  '''.format(container,container,container,NETWORK_NAME)
  DOCKERCOMPOSE_DEVELOPMENT+=CONTAINERS_STRUCT
  DOCKERCOMPOSE_PRODUCTION+=CONTAINERS_STRUCT
###########################################################################
#script make ambinte
MAKE_AMBIENT='''
sed -i "s/\\r$//" {FOLDER_NAME}{RUNSERVER_SCRIPT_NAME}.sh
sed -i "s/\\r$//" ./wait-for-it.sh
sed -i "s/\\r$//" {FOLDER_NAME}gulpfile.js
sed -i "s/\\r$//" {FOLDER_NAME}gulp.sh
cp {FOLDER_NAME}{RUNSERVER_SCRIPT_NAME}.sh ./{PROJECT_NAME}
cp ./wait-for-it.sh ./{PROJECT_NAME}
cp {FOLDER_NAME}gulpfile.js ./{PROJECT_NAME}
cp {FOLDER_NAME}gulp.sh ./{PROJECT_NAME}
chmod +x ./wait-for-it.sh
mkdir {FOLDER_NAME}nginx
mkdir static/ media/ logs/
mv {FOLDER_NAME}nginx.conf {FOLDER_NAME}nginx  
'''.format(**DOCKER)
#############################################################################
NGINX='''
 nginx:
  container_name: nginx
  restart: always
  image: nginx
  networks:
   - {NETWORK_NAME} 
  volumes:
   - "{DIR_PATH}/{FOLDER_NAME}nginx/nginx.conf:/etc/nginx/nginx.conf"
   - "{DIR_PATH}/static:{STATIC_ROOT}:rw"
   - "{DIR_PATH}/media:{MEDIA_ROOT}:rw"
   - "{DIR_PATH}/logs:{LOGS_ROOT}:rw"
  depends_on:
   - web
  ports:
   - 80:{WEB_PORT}
  '''.format(**DOCKER)
#############################################################################
if BROWSERSYNC_GULP_DEV_TOOLS:
  DOCKERCOMPOSE_DEVELOPMENT +=BROWSER_SYNC_DOCKERCOMPOSE+NETWORK
else:
  DOCKERCOMPOSE_DEVELOPMENT +=NETWORK
DOCKERCOMPOSE_PRODUCTION +=NGINX+NETWORK
#############################################################################
# Verifica modo produção ou desenvolvimento
if DEBUG:
  MAKE_AMBIENT+='''docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml stop
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml stop
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml down
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml down
docker system prune --force
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml build
COMPOSE_HTTP_TIMEOUT=3600 docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml up --remove-orphans --force-recreate'''.format(**DOCKER)

  
  RUNSERVER_SCRIPT+='''
python manage.py runserver 0.0.0.0:{WEB_PORT}
  '''.format(**DOCKER)
  # DOCKERCOMPOSE+=BROWSER_SYNC_DOCKERCOMPOSE
else:
  MAKE_AMBIENT+='''docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml stop
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml stop
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml down
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_development.yml down
docker system prune --force
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml build
docker-compose -f {FOLDER_NAME}{PROJECT_NAME}_production.yml up  -d --remove-orphans --force-recreate'''.format(**DOCKER)

  RUNSERVER_SCRIPT+='''
python manage.py collectstatic --noinput
python manage.py compress --force
gunicorn --bind=0.0.0.0:{WEB_PORT} --workers=3 {PROJECT_NAME}.wsgi
	'''.format(**DOCKER)


###########################################################################
#Arquivo de configuração nginx
NGINX_CONF='''
worker_processes 1;

events {{

    worker_connections 1024;

}}

http {{

    proxy_cache_path {STATIC_ROOT} levels=1:2 keys_zone=my_cache:10m max_size=10g 
        inactive=60m use_temp_path=off;

    default_type  application/octet-stream;
    include       /etc/nginx/mime.types;

    log_format compression '$remote_addr - $remote_user [$time_local] '
                           '"$request" $status $body_bytes_sent '
                           '"$http_referer" "$http_user_agent" "$gzip_ratio"';
   




    sendfile on;

    gzip              on;
    gzip_http_version 1.0;
    gzip_proxied      any;
    gzip_min_length   500;
    gzip_disable      "MSIE [1-6]\.";
    gzip_types        text/plain text/xml text/css
                      text/comma-separated-values
                      text/javascript
                      application/x-javascript
                      application/atom+xml;

    # Configuration containing list of application servers
    upstream app_servers {{
        ip_hash;
        server web:{WEB_PORT};

    }}

    # Configuration for Nginx
    server {{

        #access_log {LOGS_ROOT}/access.log compression;
        error_log {LOGS_ROOT}/error.log warn;
        

        # Running port
        listen {WEB_PORT};

        # Max_size
        client_max_body_size 20M;

        # Settings to serve static files 
        location /static/  {{

            # Example:
            # root /full/path/to/application/static/file/dir;
            autoindex on;
            alias {STATIC_ROOT}/;

        }}

        location /media/ {{

            autoindex on;
            alias {MEDIA_ROOT}/;
        }}

       

        # Proxy connections to the application servers
        # app_servers
        location / {{


            proxy_cache my_cache;
            proxy_cache_revalidate on;
            proxy_cache_min_uses 3;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            proxy_cache_background_update on;
            proxy_cache_lock on;

            proxy_pass         http://app_servers;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;


        }}
    }}
}}

'''.format(**DOCKER)
###########################################################################
GULPFILE='''
var gulp        = require('gulp');
var browserSync = require('browser-sync').create();
var sass        = require('gulp-sass');
var rename      = require('gulp-rename');
var autoprefixer = require('gulp-autoprefixer');
var uglify = require('gulp-uglify');
var sourcemaps = require('gulp-sourcemaps');
var imagemin = require('gulp-imagemin');

// Static Server + watching scss/html files
gulp.task('serve', ['sass','js','imagemin'], function() {{

   
    browserSync.init({{
        open: false,
        proxy: {{
          target: "http://web:{WEB_PORT}",
          ws: true,
        }}
    }});

    gulp.watch("**/**/static/{SCSS_FOLDERS}/**/*.scss", ['sass']);
    gulp.watch("**/**/static/{JS_FOLDERS}/**/*.js", ['js-watch']);
    gulp.watch("**/**/static/{IMAGE_FOLDERS}/**/*", ['image-watch']);
    gulp.watch("**/*.html").on('change', browserSync.reload);
    gulp.watch("**/*.css").on('change', browserSync.reload);
    gulp.watch(["**/*.js","!**/**/static/{JS_FOLDERS}/**/*.js","!**/**/static/{JSMIN_FOLDERS}/**/*.js"]).on('change', browserSync.reload);
}});


// create a task that ensures the `js` task is complete before
// reloading browsers
gulp.task('js-watch', ['js'], function (done) {{
    browserSync.reload();
    done();
}});

gulp.task('image-watch', ['imagemin'], function (done) {{
    browserSync.reload();
    done();
}});



gulp.task('js',function(){{
    return gulp.src(["**/**/static/{JS_FOLDERS}/**/*.js","!gulpfile.js",'!node_modules/**'])
    .pipe(rename(function(file){{
            file.dirname = file.dirname.replace('{JS_FOLDERS}','{JSMIN_FOLDERS}');
            file.extname = ".min.js"
    }}))
    .pipe(sourcemaps.init())
    .pipe(uglify()).on('error',function(err){{
            console.log(err.message);
            console.log(err.cause);
            browserSync.notify(err.message, 3000); // Display error in the browser
            this.emit('end'); // Prevent gulp from catching the error and exiting the watch process
     }})
    .pipe(sourcemaps.write())
    .pipe(gulp.dest("."))
}});

gulp.task('imagemin',function(){{
  return gulp.src(["**/**/static/{IMAGE_FOLDERS}/**/*"])
  .pipe(rename(function(file){{
            file.dirname = file.dirname.replace('{IMAGE_FOLDERS}','{IMAGEMIN_FOLDERS}');
   }}))
  .pipe(imagemin({{verbose:true}}))
  .pipe(gulp.dest("."))
}});


// Compile sass into CSS & auto-inject into browsers
gulp.task('sass', function() {{
    return gulp.src(["**/**/static/{SCSS_FOLDERS}/**/*.scss",'!node_modules/**'])
        .pipe(rename(function(file){{
            file.dirname = file.dirname.replace('{SCSS_FOLDERS}','{CSS_FOLDERS}');
        }}))
        .pipe(sourcemaps.init())
        .pipe(sass({{
            errLogToConsole: true,
            indentedSyntax: false,
            outputStyle: 'compressed'
        }}).on('error',function(err){{
            console.log(err.message);
            browserSync.notify(err.message, 3000); // Display error in the browser
            this.emit('end'); // Prevent gulp from catching the error and exiting the watch process
        }}))
        .pipe(autoprefixer({{
            browsers: ['last 100 versions'],
            cascade: false
        }}))
        .pipe(sourcemaps.write())
        .pipe(gulp.dest("."))
        .pipe(browserSync.stream());
}});

gulp.task('default', ['serve']);
'''.format(**DOCKER)
###########################################################################
############################################################################
#Criando arquivos
dockerfile=open(folder_to_save+'{PROJECT_NAME}.Dockerfile'.format(**DOCKER),'w')
dockerfile.write(DOCKERFILE)
dockerfile.close()


runserver=open(folder_to_save+'{RUNSERVER_SCRIPT_NAME}.sh'.format(**DOCKER),'w')
runserver.write(RUNSERVER_SCRIPT)
runserver.close()

dockercompose = open(folder_to_save+'{PROJECT_NAME}_development.yml'.format(**DOCKER),'w')
dockercompose.write(DOCKERCOMPOSE_DEVELOPMENT)
dockercompose.close()

dockercompose = open(folder_to_save+'{PROJECT_NAME}_production.yml'.format(**DOCKER),'w')
dockercompose.write(DOCKERCOMPOSE_PRODUCTION)
dockercompose.close()

makeambient=open(folder_to_save+'make_ambient.sh','w')
makeambient.write(MAKE_AMBIENT)
makeambient.close()


nginxconf = open(folder_to_save+'nginx.conf','w')
nginxconf.write(NGINX_CONF)
nginxconf.close()

if BROWSERSYNC_GULP_DEV_TOOLS:
  brosersync = open(folder_to_save+'browsersync.Dockerfile','w')
  brosersync.write(BROWSERSYNC_DOCKERFILE)
  brosersync.close()

  gulpfile = open(folder_to_save+'gulpfile.js','w')
  gulpfile.write(GULPFILE)
  gulpfile.close()

  gulpfile = open(folder_to_save+'gulp.sh','w')
  gulpfile.write(GULPSH)
  gulpfile.close()

#########################################################################
#cria arquivos requirements
requirements=open(folder_to_save+'requirements.txt','w')
for requirement in REQUIREMENTS:
  requirements.write(requirement+'\n')
requirements.close()
