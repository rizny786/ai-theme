from setuptools import setup, find_packages
setup(
    name='ai_theme_api',
    version='1.0',
    description='A small package for AI theme',
    author='IP1SMS',
    author_email='rizny.mubarak@ip1.se',
    packages=find_packages(),
    install_requires=[
        'requests',
        'pipwin',
        'cairocffi',
        'Pillow',
        'cairosvg',
        'selenium',
    ],
)