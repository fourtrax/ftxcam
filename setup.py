# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("processFile", ["processFile.pyx"]),Extension("path", ["libs/path.pyx"]),Extension("parser", ["libs/parser.pyx"]),
    			Extension("geometry", ["geometry.pyx"])]
)
