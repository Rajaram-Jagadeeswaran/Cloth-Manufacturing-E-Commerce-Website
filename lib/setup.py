from setuptools import setup, find_packages

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Education',
    'Operating System :: Microsoft :: Windows :: Windows 11',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.11'
]

setup(
    name='order-processing-library',
    version='0.0.1',
    description='My package is used to handle the basic discount, tax & shipping calculation',
    long_description=open('README.md').read() + '\n\n' + open('CHANGELOG.txt').read(),
    url='',
    author='Rajaram Jagadeeswaran',
    author_email='x22239243@student.ncirl.ie',
    license='MIT',
    classifiers= classifiers,
    keywords='discount',
    packages=find_packages(),
    install_requires=['']
)