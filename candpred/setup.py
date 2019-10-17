from setuptools import setup

setup(
   name='candpred',
   version='0.1.0',
   author='Nicholas Broad',
   author_email='nbroad94@gmail.com',
   packages=['candpred', 'candpred.test'],
   scripts=['bin/candpred_script.py'],
   license='LICENSE.txt',
   description='Takes news articles and predicts the popularity of democratic presidential candidates',
   long_description=open('README.txt').read(),
   package_data={'candpred': ['data/candpred_data.txt']}
)