from setuptools import setup

setup(
    name='flask-restful-graph',
    packages=['flask-restful-graph'],
    include_package_data=True,
    install_requires=[
        'flask-marshmallow',
        'flask-restful',
        'neomodel'
    ]
)
