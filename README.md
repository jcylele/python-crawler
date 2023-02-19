# python-crawler
traverse a website, download resources and manage them with a database, the corresponding frontend project can be found [here](https://github.com/jcylele/python-crawler)

## main features

1. SQLAlchemy

   [SQLAlchemy](https://www.sqlalchemy.org/)

   A SQL toolkit and Object Relational Mapper for Python.
   It's used to operate databases(MySQL is used in this project). 
   ORM is quite easy to use, but watch out for sessions. 
   Keep their lives short and avoid doing time-consuming jobs inside.

2. Beautiful Soup

   [Beautiful Soup Documentation](https://beautiful-soup-4.readthedocs.io/en/latest/)

   A Python library for pulling data out of HTML and XML files.
   It works fine with static html pages and incredibly easy to use.
   For dynamic pages(e.g, scroll to refresh), maybe you should use [Selenium](https://selenium-python.readthedocs.io/) instead.

3. Requests

    [Requests Documentation](https://requests.readthedocs.io/en/latest/)
    
    An elegant and simple HTTP library for Python.
    Use sessions with headers and cookies for better adaptability.
    Head function sometimes is better than the get function, such as getting size of an image before downloading and validating the size after that.


4. A Simple Work Queue System

   Each worker fetches work from corresponding queue and processes it repeatedly.
   Different queues containing different types of tasks.
   A guarder monitors and reports the running status of workers and queues

## TODO
A local website built in [FastAPI](https://fastapi.tiangolo.com/) and [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/)

