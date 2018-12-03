# -*- coding: utf-8 -*-
"""
Created on Thu Nov 29 17:09:36 2018

@author: prodipta
"""
import os
from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext as _build_ext
    
# lazy loading of cython, see below:
# https://stackoverflow.com/questions/37471313/setup-requires-with-cython 
try:
    from Cython.Build import cythonize
except ImportError:
     def cythonize(*args, **kwargs):
         from Cython.Build import cythonize
         return cythonize(*args, **kwargs)
     
# read README for long description
with open("README.md", "r") as fh:
    long_description = fh.read()
    
# read requirements.txt for dependencies
def parse_requirements(requirements_txt):
    with open(requirements_txt) as f:
        for line in f.read().splitlines():
            if not line or line.startswith("#"):
                continue
            yield line
            
def install_requires():
    return list(set([r for r in parse_requirements('requirements.txt')]))

# custom build extension for numpy
class BlueshiftBuildExt(_build_ext):
    '''
        build_ext command for use when numpy headers are needed.
        see https://stackoverflow.com/questions/2379898/make\
        -distutils-look-for-numpy-header-files-in-the-correct-place
    '''
    def run(self):
        import numpy
        self.include_dirs.append(numpy.get_include())
        _build_ext.run(self)

print(f"working dir is {os.getcwd()}")
ext_modules = [
        Extension('blueshift.assets._assets', ['blueshift/assets/_assets.pyx']),
        Extension('blueshift.blotter._accounts', ['blueshift/blotter/_accounts.pyx']),
        Extension('blueshift.blotter._perf', ['blueshift/blotter/_perf.pyx']),
        Extension('blueshift.execution._clock', ['blueshift/execution/_clock.c']),
        Extension('blueshift.trades._order_types', ['blueshift/trades/_order_types.pyx']),
        Extension('blueshift.trades._order', ['blueshift/trades/_order.pyx']),
        Extension('blueshift.trades._trade', ['blueshift/trades/_trade.pyx']),
        Extension('blueshift.trades._position', ['blueshift/trades/_position.pyx']),
        Extension('blueshift.utils.cutils', ['blueshift/utils/cutils.pyx']),
        ]

setup(
    name='blueshift',
    cmdclass = {'build_ext': BlueshiftBuildExt},
    url="https://github.com/QuantInsti/blueshift",
    version="0.0.1",
    description='A complete algorithmic trading system.',
    long_description=long_description,
    entry_points={'console_scripts': ['blueshift = blueshift.__main__:main']},
    author='QuantInsti Quantitative Learnings',
    author_email='blueshift-support@quantinsti.com',
    packages=find_packages(include=['blueshift', 'blueshift.*']),
    ext_modules=cythonize(ext_modules),
    include_package_data=True,
    package_data={root.replace(os.sep, '.'):
                  ['*.pyi', '*.pyx', '*.pxi', '*.pxd']
                  for root, dirnames, filenames in os.walk('blueshift')
                  if '__pycache__' not in root},
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console'
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'Intended Audience :: Science/Research',
        'Topic :: Office/Business :: Financial',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Intended Audience :: Financial and Insurance Industry'
    ],
    setup_requires=['cython','numpy'],
    install_requires=install_requires()
)