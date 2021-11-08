import os, sys

if getattr(sys, 'frozen', False):
    mainfolder = sys._MEIPASS
else:
    mainfolder = os.path.dirname(os.path.abspath(__file__))