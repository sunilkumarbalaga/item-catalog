# Item-catalog
Colleges Application App for Item catalog project. This is a python module that creates a website and JSON API for a list of colleges and the courses available in the college. Each college displays their courses and also provides user authentication using Google. Registered users will have ability to edit and delete their own college and courses. This application uses Flask,SQL Alchemy, JQuery,CSS, Javascript, and OAuth2 to create Item catalog website.

## Installation:
1.virtualBox 

2.Vagrant 

3.python 2.7


## Instructions to Run the project:

Setting up OAuth 2.0

You will need to signup for a google account and set up a client id and secret.

Visit http://console.developers.google.com for google setup.

Setting up the Environment

clone or download the repo into vagrant environment.

Type command vagrant up,vagrant ssh.

In VM, cd /vagrant/catalog

Run python database_setup.py to create the database.

Run Python lotsofcolleges.py to add the menu items.

Run python 'finalproject.py'.

open your webbrowser and visit http://localhost:5000/
