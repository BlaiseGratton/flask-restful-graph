from setuptools import setup

setup(
    name='flask_restful_graph',
    packages=['flask_restful_graph'],
    include_package_data=True,
    install_requires=[
        'flask-marshmallow',
        'flask-restful',
        'py2neo'
    ]
)
