# edu

Management website for educational centers with DJANGO

#for linux users

1. Install virualenv (pip3 install virtualenv)
2. Install and activate environment (virtualenv env) (source env/bin/activate)
3. Create .env file in main directory

.env file
SECRET_KEY=
DEBUG=True

<!-- No need to fill when debug is true -->

DOMAIN=
PROJECTDIR=
USERNAME=

<!--  -->

3. Install requirements (pip3 install -r reqiurements.txt)
4. Apply migrations (python3 manage.py migrate)
5. Create Super User (python3 manage.py createsuperuser)
6. Run app (python3 manage.py runserver)
