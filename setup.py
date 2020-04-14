import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='xintesis',
    version='0.1',
    scripts=[],
    author="Jairo Lefebre",
    author_email="jairo.lefebre@gmail.com",
    description="Simple Python Flask based REST API builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/J41R0/Xintesis",
    packages=setuptools.find_packages(),
    install_requires=[
        'werkzeug >= 0.15.4',
        'flask_restplus >= 0.11.0',
        'flask_cors >= 3.0.7',
        'flask_jwt_extended >= 3.10.0',
        'jinja2 >= 2.10.1',
        'click >= 7.0'
    ],
    python_requires='>=3.6',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
