import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='xintesis',
    version='1.0',
    scripts=[],
    author="Jairo Lefebre",
    author_email="jairo.lefebre@gmail.com",
    description="A Docker and AWS utility package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/J41R0/Xintesis",
    packages=setuptools.find_packages(),
    install_requires=[
        'setuptools',
        'werkzeug >= 0.15.4',
        'flask_restplus >= 0.11.0',
        'flask_cors >= 3.0.7',
        'flask_jwt_extended >= 3.10.0',
        'jinja2 >= 2.10.1',
        'click >= 7.0',
        'selenium-requests >= 1.3'
    ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Debian compatible",
    ],
)
