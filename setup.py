from setuptools import find_packages, setup

setup(
    name='xmltrampShow',
    version='1.0.0',
    author='Brian Zhu',
    author_email='brzx@foxmail.com',
    description='Study show the run process for xmltramp parsing xml',
    long_description=open('README.md').read(),
    url='https://github.com/brzx/xmltrampShow',
    license='GPLv2',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[],
    classifiers=(
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Topic :: Text Processing :: Markup :: XML",
    ),
)
