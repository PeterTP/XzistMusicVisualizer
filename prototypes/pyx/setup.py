from setuptools import setup
from Cython.Build import cythonize
from pathlib import Path

PATH = Path(__file__).parent
FILE_PATH = str(PATH/'ExtractDict.py')

setup(ext_modules=cythonize(FILE_PATH, annotate=True))