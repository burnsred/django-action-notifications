import os
from distutils.core import setup

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


setup(
    name='django-action-notifications',
    version='0.0.18',
    packages=get_packages('action_notifications'),
    include_package_data=True,
    package_data=get_package_data('action_notifications'),
    license='MIT License',
    author='Michael Bertolacci (BurnsRED)',
    author_email='michael@burnsred.com.au',
    url='',
    long_description=open('README.md').read(),
    install_requires=[
        "Django >= 2.2",
        "django-activity-stream >= 0.8.0",
        "djangorestframework >= 3.10.2",
        "django-filter >= 2.2.0",
        "django-kronos >= 1.0",
    ],
)
