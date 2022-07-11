from setuptools import setup, find_packages

setup(
    name='chesspecker',
    version='0.3',
    packages=find_packages(exclude=('test', )),
    install_requires=[
        'chess',
        ],
    entry_points={
        'console_scripts': [
            'peckerchess=chesspecker.bin:main',
        ],
    },
)
