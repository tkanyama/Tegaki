# -*- coding: utf-8 -*-
'''

プログラム名：jFont.py

日本語フォントの設定

バージョン：1.0

python 3.7.1

作成：2019/9 完山

'''
import os
from os.path import expanduser
# import matplotlib
# matplotlib.interactive(True)
# matplotlib.use('WXAgg')
from matplotlib.font_manager import FontProperties
import platform

def font_set(fontsize=8, c=1.0):
    osname = platform.system()
    home = expanduser('~')
    root = os.path.dirname(__file__)
    # 日本語フォントの設定
    if os.path.exists(root + '/Fonts/ipaexg.ttf'):
        # プログラムと同じフォルダーに日本語フォントがある場合はそれを使用する。
        gothicname = root + '/Fonts/ipaexg.ttf'  # ゴシック
        minchoname = root + '/Fonts/ipaexm.ttf'  # 明朝
    else:
        if osname == 'Windows':
            if os.path.exists(r'C:\WINDOWS\Fonts\ipaexg.ttf'):
                gothicname = r'C:\WINDOWS\Fonts\ipaexg.ttf'  # ゴシック
                minchoname = r'C:\WINDOWS\Fonts\ipaexm.ttf'  # 明朝
            elif os.path.exists(home + r'\AppData\Local\Microsoft\Windows\Fonts\ipaexg.ttf'):
                gothicname = home + r'\AppData\Local\Microsoft\Windows\Fonts\ipaexg.ttf'  # ゴシック
                minchoname = home + r'\AppData\Local\Microsoft\Windows\Fonts\ipaexm.ttf'  # 明朝
            else:
                gothicname ='sans-serif' # ゴシック
                minchoname ='serif'        # 明朝

        elif osname == 'Darwin':  # Mac OS
            if os.path.exists(r'/Library/Fonts/ipaexg.ttf'):
                gothicname = r'/Library/Fonts/ipaexg.ttf'  # ゴシック
                minchoname = r'/Library/Fonts/ipaexm.ttf'  # 明朝
            else:
                gothicname ='sans-serif' # ゴシック
                minchoname ='serif'        # 明朝
        elif osname == 'Linux':
            if os.path.exists(home + r'/.fonts/IPAexfont00301/ipaexg.ttf'):
                gothicname = home + r'/.fonts/IPAexfont00301/ipaexg.ttf'  # ゴシック
                minchoname = home + r'/.fonts/IPAexfont00301/ipaexm.ttf'  # 明朝
            else:
                gothicname ='sans-serif' # ゴシック
                minchoname ='serif'        # 明朝

    fp1 = FontProperties(fname=minchoname, size=fontsize * c)
    fp2 = FontProperties(fname=gothicname, size=fontsize * c)
    return fp1, fp2

def mincho_font_set(fsize=8, c1=1.0):
    fp1, fp2 = font_set(fontsize=fsize, c=c1)
    return fp1

def gothic_font_set(fsize=8, c1=1.0):
    fp1, fp2 = font_set(fontsize=fsize, c=c1)
    return fp2