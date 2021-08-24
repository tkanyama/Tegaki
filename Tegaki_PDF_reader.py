# -*- coding: utf-8 -*-
'''

プログラム名：MainFrame.py

風洞実験結果から応答解析を行い、報告書用の図表を作成するプログラム

バージョン：1.0

python 3.7.1

作成：2020/4 完山

'''

# ライブラリーの読み込み
import os

import matplotlib

matplotlib.interactive(True)
matplotlib.use('WXAgg')
import matplotlib.pyplot as plt

import wx
import wx.lib.scrolledpanel as scrolled
import platform
import time
from PyPDF2 import PdfFileWriter, PdfFileReader
import shutil
from pdf2image import convert_from_path, convert_from_bytes
import numpy as np
import pyocr
import pyocr.builders
from PIL import Image
import openpyxl

import re
from janome.tokenizer import Tokenizer
from janome.analyzer import Analyzer
from janome import tokenfilter, charfilter

# 自作モジュールのimport
from ReadAreaBox import ReadAreaBox, MiniBox
from Errata import Errata
from UserDic import UserDic
from KanjiFind import *

# メニューIDの設定
ID_READ_PARA = 101  # 層風力計算
ID_SAVE = 102  # 解析結果保存
# ID_CALC_RESPONSE =102                     # 応答解析
ID_EXIT = 105  # 終了
ID_UNDO = 200  # UNDO
ID_ROTATE_MINUS = 201  # 時計回りに回転
ID_ROTATE_PLUS = 202  # 反時計回りに回転
ID_PAGE_DELETE = 203  # 反時計回りに回転
ID_PAGE_BREAK = 204  # ページの区切りを操作
ID_ERRATA = 205  # ページの区切りを操作
ID_DIC = 206  # ページの区切りを操作

ID_VEIW_RATIO = 300  # 表示倍率

ID_OCR = 501  # OCR (テキスト認識）
ID_ANALYSIS = 502  # 形態解析

ID_BOX_ADD1 = 401  # AREA BOX titleの追加
ID_BOX_ADD2 = 402  # AREA BOX dateの追加
ID_BOX_ADD3 = 403  # AREA BOX nameの追加
ID_BOX_ADD4 = 404  # AREA BOX docの追加
ID_BOX_SAVE = 411  # AREA BOX の保存
ID_BOX_LOAD = 412  # AREA BOX の読込
ID_BOX_DELL_LAST = 413  # AREA BOX のLAST削除
ID_BOX_DELL_ALL = 414  # AREA BOX の全削除

FRAME_WIDTH = 1350  # メインパネルの幅
FRAME_HEIGHT = 753  # メインパネルの高さ
CONTROL_PANEL_HEIGHT = 60  # 上側のコントロールパネルの高さ
CONTROL_PANEL_WIDTH = FRAME_WIDTH  # 上側のコントロールパネルの幅

THUMBNAIL_PANEL_WIDTH = 250  # サムネイルパネルの幅
THUMBNAIL_PANEL_HEIGHT = FRAME_HEIGHT - CONTROL_PANEL_HEIGHT-40 # サムネイルパネルの幅

PDF_PANEL_WIDTH = 700
PDF_PANEL_HEIGHT = FRAME_HEIGHT - CONTROL_PANEL_HEIGHT
PDF_DPI = 300

TEXT_PANEL_WIDTH1 = FRAME_WIDTH - THUMBNAIL_PANEL_WIDTH - PDF_PANEL_WIDTH
TEXT_PANEL_HEIGHT1 = (FRAME_HEIGHT - CONTROL_PANEL_HEIGHT) * 0.49

TEXT_PANEL_WIDTH2 = TEXT_PANEL_WIDTH1
TEXT_PANEL_HEIGHT2 = FRAME_HEIGHT - TEXT_PANEL_HEIGHT1

BUTTON_WIDTH = 80
BUTTON_HEIGHT = CONTROL_PANEL_HEIGHT / 2

TIMER_INTERVAL1 = 1000

AREA_BOX_LINE_WIDTH = 3
MINI_BOX_LINE_WIDTH = 1

resizeFlag = False

SMALL_BOX_P1 = (5, 15)
SMALL_BOX_P2 = (95, 25)
LARGE_BOX_P1 = (2, 2)
LARGE_BOX_P2 = (98, 98)

CATEGORY = ['役員会議事録', '理事会議事録', '理事会議事次第', '評議員会議事録', '評議員会議事次第']
CATEGORY2 = ['役員会', '理事会', '評議員会']


# =======================================================================
#       正誤表　訂正　モジュール
# =======================================================================
class errata:
    def __init__(self):
        self.user_dic = "dic/正誤表.xlsx"
        book = openpyxl.load_workbook(self.user_dic)

        active_sheet = book.active
        self.dic = []
        for row in active_sheet.rows:
            col = []
            for cell in row:
                col.append(cell.value)
            self.dic.append(col)

    def exec_errata(self, text=''):
        result = ''
        lines = text.splitlines()
        for line_text in lines:
            t1 = line_text.replace(' ', '', 500)
            if t1 != '':
                line_text = line_text.replace(' ', '', 500)

                for row in self.dic:
                    if row[0] != None:
                        line_text = line_text.replace(row[0], row[1], 500)

                result += line_text + '\n'

        return result


def year_convart(date='昭和34年1月22日'):
    date2 = '1900/1/1'
    if date != '':
        if date.count('年') > 0:
            y1 = date[0:date.find('年') + 1]
            y2 = ''
            md = date[date.find('年') + 1:]
            if re.match('昭和元年', y1):
                y2 = str(1926) + '年'
            elif re.match('昭和', y1):
                y2 = str(1925 + int(re.sub(r'\D', '', y1))) + '年'
            elif re.match('平成元年', y1):
                y2 = str(1989) + '年'
            elif re.match('平成', y1):
                y2 = str(1988 + int(re.sub(r'\D', '', y1))) + '年'
            elif re.match('令和元年', y1):
                y2 = str(2019) + '年'
            elif re.match('令和', y1):
                y2 = str(2018 + int(re.sub(r'\D', '', y1))) + '年'

            date2 = y2 + md
            date2 = date2.replace('年', '/').replace('月', '/').replace('日', '')
        elif date.count('H.') > 0:
            y = int(date[2:4]) + 1988
            date2 = date
            date2 = date2.replace(date2[0:4], str(y))
            date2 = date2.replace('.', '/')

    return date2


class MainFrame(wx.Frame):

    def __init__(self, *args, **kwargs):

        year_convart('令和2年1月22日')
        # OSの種類の読み込み（'Windows' or 'Darwin' or 'Linux'）
        self.osname = platform.system()
        self.home = os.path.expanduser('~')
        # self.data_dir = self.home + "/PDF_DATA"
        self.save_dir = self.home + "/DATABASE_DATA"
        self.box_data_dir = self.home + "/BOX_DATA"
        # self.user_dic = self.home + "/dic/gbrc_dic.csv"
        self.user_dic = "dic/gbrc_dic.csv"
        self.para_data = self.home + "/PDF_DATA/para.ini"
        self.data_dir = self.load_data()

        # ウインドウのバーの高さの設定（osによって異なるため）
        if self.osname == 'Windows':
            bar_h = 60
            self.bar_w = 18
            self.scw = 20.0
            # 1.インストール済みのTesseractのパスを通す
            path_tesseract = "C:\\Program Files\\Tesseract-OCR"
            if path_tesseract not in os.environ["PATH"].split(os.pathsep):
                os.environ["PATH"] += os.pathsep + path_tesseract
            self.SCROLL_PAGE_HEIGHT = 68

        elif self.osname == 'Darwin':  # Mac OS
            bar_h = 22
            self.bar_w = 15
            self.scw = 10.0
            self.SCROLL_PAGE_HEIGHT = 70
            from os.path import expanduser
        elif self.osname == 'Linux':
            bar_h = 22
            self.bar_w = 15
            self.scw = 20.0
            self.SCROLL_PAGE_HEIGHT = 70
            from os.path import expanduser

        wx.Frame.__init__(self, *args, **kwargs)  # メインパネルの作成wx.BORDER_STATIC
        self.Center()  # ウィンドウをモニターのセンターに表示
        (self.frame_w, self.frame_h) = self.GetSize()  # ウィンドウのサイズの読み込み

        # =======================[ メイン　パネル ]=========================================
        self.mainPanel = wx.Panel(self, wx.ID_ANY, pos=(0, 0), size=(self.frame_w, self.frame_h - self.bar_w))

        # =======================[ コントロール　パネル ]=========================================
        self.v_layout1 = wx.BoxSizer(wx.HORIZONTAL)
        self.ctrl_panel = wx.Panel(self.mainPanel, wx.ID_ANY, pos=(0, 0),
                                   size=(CONTROL_PANEL_WIDTH, CONTROL_PANEL_HEIGHT), style=wx.DOUBLE_BORDER)
        self.ctrl_panel.SetBackgroundColour('white')
        # self.v_layout1.Add(self.ctrl_panel)

        # =======================[ ボタンの設定 ]=========================================
        # PDFファイル読み込みボタン
        self.pdf_read_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'pdf読込',
                                         size=(BUTTON_WIDTH, BUTTON_HEIGHT), pos=(BUTTON_WIDTH * 0.5, 0))
        self.Bind(wx.EVT_BUTTON, self.pdf_read_button_handler, self.pdf_read_button)  # イベントを設定
        self.v_layout1.Add(self.pdf_read_button)

        # 読み込みページ数設定用COMBO BOX
        font1 = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.page_items = ['all', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        self.page_item = '3'
        self.comboPage = wx.ComboBox(self.ctrl_panel, choices=self.page_items,
                                     size=(BUTTON_WIDTH, BUTTON_HEIGHT),
                                     pos=(BUTTON_WIDTH * 0.5, CONTROL_PANEL_HEIGHT / 2))
        self.comboPage.SetValue(self.page_item)
        self.comboPage.Font = font1
        self.v_layout1.Add(self.comboPage, 1, wx.EXPAND | wx.ALL, 10)

        # 前のページを表示するボタン
        self.page_minus_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '↑',
                                           size=(BUTTON_WIDTH / 2, BUTTON_HEIGHT),
                                           pos=(BUTTON_WIDTH * 1.7, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.page_minus_button_handler, self.page_minus_button)  # イベントを設定
        self.v_layout1.Add(self.page_minus_button)

        # 次のページを表示するボタン
        self.page_plus_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '↓',
                                          size=(BUTTON_WIDTH / 2, BUTTON_HEIGHT),
                                          pos=(BUTTON_WIDTH * 2.2, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.page_plus_button_handler, self.page_plus_button)  # イベントを設定
        self.v_layout1.Add(self.page_plus_button)

        # 現在のページ　／　最終ページの表示
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.pageText = wx.StaticText(self.ctrl_panel, wx.ID_ANY,
                                      '[ page {}/{} ]'.format(0, 0), pos=(BUTTON_WIDTH * 1.7, 10))
        self.pageText.SetFont(font)
        self.v_layout1.Add(self.pageText)

        # 現在のページ　／　最終ページの表示
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.boxText = wx.StaticText(self.ctrl_panel, wx.ID_ANY,
                                     '[ ボックス ]', pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 1.0, 5))
        self.boxText.SetFont(font)
        self.v_layout1.Add(self.boxText)

        # ReadAreaBoxを表示するボタン
        self.box_ADD_title_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'タイトル',
                                              size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                              pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 2.2, 0))
        self.Bind(wx.EVT_BUTTON, self.box_ADD_title_button_handler, self.box_ADD_title_button)  # イベントを設定
        self.v_layout1.Add(self.box_ADD_title_button)

        self.box_ADD_date_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '日付',
                                             size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                             pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 2.2, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.box_ADD_date_button_handler, self.box_ADD_date_button)  # イベントを設定
        self.v_layout1.Add(self.box_ADD_date_button)

        self.box_ADD_name_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '氏名',
                                             size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                             pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 3.2, 0))
        self.Bind(wx.EVT_BUTTON, self.box_ADD_name_button_handler, self.box_ADD_name_button)  # イベントを設定
        self.v_layout1.Add(self.box_ADD_name_button)

        # ReadAreaBoxを表示するボタン
        self.box_ADD_doc_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '資料',
                                            size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                            pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 3.2, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.box_ADD_doc_button_handler, self.box_ADD_doc_button)  # イベントを設定
        self.v_layout1.Add(self.box_ADD_doc_button)

        # ReadAreaBoxを保存するボタン
        self.box_save_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'Box保存',
                                         size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                         pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 5.2, 0))
        self.Bind(wx.EVT_BUTTON, self.box_save_button_handler, self.box_save_button)  # イベントを設定
        self.v_layout1.Add(self.box_save_button)

        self.box_load_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'Box読込',
                                         size=(BUTTON_WIDTH * 1.0, BUTTON_HEIGHT),
                                         pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 5.2, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.box_load_button_handler, self.box_load_button)  # イベントを設定
        self.v_layout1.Add(self.box_load_button)

        # 最後のReadAreaBoxを消去するボタン
        self.box_DEL_last_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'Last Box消去',
                                             size=(BUTTON_WIDTH * 1.2, BUTTON_HEIGHT),
                                             pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 6.3, 0))
        self.Bind(wx.EVT_BUTTON, self.box_DEL_last_buttonn_handler, self.box_DEL_last_button)  # イベントを設定
        self.v_layout1.Add(self.box_DEL_last_button)

        # すべてのReadAreaBoxを消去するボタン
        self.box_DEL_all_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'Box全消去',
                                            size=(BUTTON_WIDTH * 1.2, BUTTON_HEIGHT),
                                            pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 6.3, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.box_DEL_all_buttonn_handler, self.box_DEL_all_button)  # イベントを設定
        self.v_layout1.Add(self.box_DEL_all_button)

        # 正誤表を編集するボタン
        self.Errata_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '正誤表の編集',
                                       size=(BUTTON_WIDTH * 1.4, BUTTON_HEIGHT),
                                       pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 8.0, 0))
        self.Bind(wx.EVT_BUTTON, self.Errata_button_handler, self.Errata_button)  # イベントを設定
        self.v_layout1.Add(self.Errata_button)

        # ユーザー辞書を編集するボタン
        self.Dic_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'ユーザ辞書の編集',
                                    size=(BUTTON_WIDTH * 1.4, BUTTON_HEIGHT),
                                    pos=(THUMBNAIL_PANEL_WIDTH + BUTTON_WIDTH * 8.0, CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.Dic_buttonn_handler, self.Dic_button)  # イベントを設定
        self.v_layout1.Add(self.Dic_button)

        # OCR（光学的文字認識）を開始するボタン
        self.ocr_button1 = wx.Button(self.ctrl_panel, wx.ID_ANY, 'テキスト認識',
                                     size=(BUTTON_WIDTH * 1.25, BUTTON_HEIGHT),
                                     pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH + BUTTON_WIDTH * 1.0, 0))
        self.Bind(wx.EVT_BUTTON, self.ocr_button_handler1, self.ocr_button1)  # イベントを設定
        # self.Bind(wx.EVT_BUTTON, self.box_DEL_buttonn_handler, self.ocr_button1)  # イベントを設定
        self.v_layout1.Add(self.ocr_button1)

        # 手書き文字認識を開始するボタン
        self.cnn_button = wx.Button(self.ctrl_panel, wx.ID_ANY, '手書文字認識',
                                     size=(BUTTON_WIDTH * 1.25, BUTTON_HEIGHT),
                                     pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH + BUTTON_WIDTH * 1.0,
                                          CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.cnn_button_handler, self.cnn_button)  # イベントを設定
        # self.Bind(wx.EVT_BUTTON, self.box_DEL_buttonn_handler, self.ocr_button1)  # イベントを設定
        self.v_layout1.Add(self.cnn_button)

        # 形態解析を開始するボタン
        self.analysis_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'データ作成',
                                         size=(BUTTON_WIDTH, BUTTON_HEIGHT),
                                         pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH + BUTTON_WIDTH * 2.4, 0))
        self.Bind(wx.EVT_BUTTON, self.analysis_button_handler, self.analysis_button)  # イベントを設定
        self.v_layout1.Add(self.analysis_button)

        # 形態解析結果を保存するボタン
        self.result_save_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'データ保存',
                                            size=(BUTTON_WIDTH, BUTTON_HEIGHT),
                                            pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH + BUTTON_WIDTH * 3.5, 0))
        self.Bind(wx.EVT_BUTTON, self.result_save_button_handler, self.result_save_button)  # イベントを設定
        self.v_layout1.Add(self.result_save_button)

        # 形態解析結果を読み出すボタン
        self.result_load_button = wx.Button(self.ctrl_panel, wx.ID_ANY, 'データ読込',
                                            size=(BUTTON_WIDTH, BUTTON_HEIGHT),
                                            pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH + BUTTON_WIDTH * 3.5,
                                                 CONTROL_PANEL_HEIGHT / 2))
        self.Bind(wx.EVT_BUTTON, self.result_load_button_handler, self.result_load_button)  # イベントを設定
        self.v_layout1.Add(self.result_load_button)

        # =======================[ comboboxの設定 ]=========================================
        # 表示倍率
        self.dataExist1 = False
        font1 = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.comboText = wx.StaticText(self.ctrl_panel, wx.ID_ANY,
                                       '表示倍率'.format(0, 0), pos=(THUMBNAIL_PANEL_WIDTH, 10))
        self.comboText.SetFont(font1)
        self.v_layout1.Add(self.comboText)

        self.raito_items = ['50', '75', '100', '125', '150']
        self.ratio = '100'

        self.combo1 = wx.ComboBox(self.ctrl_panel, choices=self.raito_items,
                                  pos=(THUMBNAIL_PANEL_WIDTH, CONTROL_PANEL_HEIGHT / 2))
        self.combo1.Bind(wx.EVT_COMBOBOX, self.OnCombo)
        self.combo1.Bind(wx.EVT_TEXT, self.OnCombo)

        self.combo1.SetValue(self.ratio)
        self.combo1.Font = font1
        self.v_layout1.Add(self.combo1, 1, wx.EXPAND | wx.ALL, 10)

        # =======================[ Sizerの設定 ]=========================================
        self.ctrl_panel.SetSizer(self.v_layout1)

        # =======================[ ボタン使用不能に設定する ]=========================================
        self.page_minus_button.Enabled = False
        self.page_plus_button.Enabled = False
        self.analysis_button.Enabled = False
        self.ocr_button1.Enabled = False
        self.cnn_button.Enabled = False

        self.box_ADD_title_button.Enabled = False
        self.box_ADD_name_button.Enabled = False
        self.box_ADD_date_button.Enabled = False
        self.box_ADD_doc_button.Enabled = False

        self.box_DEL_all_button.Enabled = False
        self.box_DEL_last_button.Enabled = False
        self.box_save_button.Enabled = False
        self.box_load_button.Enabled = False
        self.result_save_button.Enabled = False

        # =======================[ サブ　パネル ]=========================================
        self.panel_height1 = self.frame_h - self.bar_w - CONTROL_PANEL_HEIGHT-50
        self.subPanel1 = wx.Panel(self.mainPanel, wx.ID_ANY, pos=(0, CONTROL_PANEL_HEIGHT),
                                  size=(self.frame_w, self.panel_height1))
        # self.subPanel1.SetBackgroundColour('green')

        # =======================[ サムネイル表示スクロールパネル ]=========================================
        self.thumbnail_scroll_panel = scrolled.ScrolledPanel(self.subPanel1, wx.ID_ANY, pos=(0, 0),
                                                             size=(THUMBNAIL_PANEL_WIDTH, THUMBNAIL_PANEL_HEIGHT),
                                                             style=wx.DOUBLE_BORDER)
        self.thumbnail_scroll_panel.SetupScrolling()
        self.thumbnail_scroll_panel.SetBackgroundColour(wx.Colour(red=220, green=220, blue=220))
        self.thumbnail_scroll_panel.Bind(wx.EVT_CHILD_FOCUS, self.OnThumbnailChildFocus)
        # self.thumbnail_scroll_panel.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)

        # =======================[ PDF表示スクロールパネル ]=========================================
        self.pdf_scroll_panel = scrolled.ScrolledPanel(self.subPanel1, wx.ID_ANY, pos=(THUMBNAIL_PANEL_WIDTH, 0),
                                                       size=(PDF_PANEL_WIDTH, PDF_PANEL_HEIGHT*0.91), style=wx.DOUBLE_BORDER)
        self.pdf_scroll_panel.SetupScrolling()
        self.pdf_scroll_panel.SetBackgroundColour(wx.Colour(red=200, green=200, blue=200))
        self.pdf_scroll_panel.Bind(wx.EVT_CHILD_FOCUS, self.OnPdfPanelChildFocus)

        # =======================[ ノートブック ]=========================================
        self.notebook1 = wx.Notebook(self.subPanel1, id=wx.ID_ANY,
                                     pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH, 0),
                                     size=(TEXT_PANEL_WIDTH1, TEXT_PANEL_HEIGHT1*0.95))

        self.notebook2 = wx.Notebook(self.subPanel1, id=wx.ID_ANY,
                                     pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH, TEXT_PANEL_HEIGHT1*0.95),
                                     size=(TEXT_PANEL_WIDTH1, TEXT_PANEL_HEIGHT1))

        self.Text_panel_1 = wx.Panel(self.notebook1, wx.ID_ANY)
        self.Text_panel_2 = wx.Panel(self.notebook2, wx.ID_ANY)

        self.notebook1.AddPage(self.Text_panel_1, u"テキスト認識")
        self.notebook2.AddPage(self.Text_panel_2, u"データ")

        # =======================[ 認識テキスト表示パネル ]=========================================
        self.result_text1 = wx.TextCtrl(self.Text_panel_1, wx.ID_ANY, pos=(0, 0),
                                        size=(TEXT_PANEL_WIDTH1*0.95, TEXT_PANEL_HEIGHT1 * 0.85),
                                        style=wx.TE_LEFT | wx.TE_MULTILINE)
        self.result_text1.SetValue("")
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.result_text1.SetFont(font)

        # =======================[ 形態解析結果表示パネル ]=========================================
        self.result_text2 = wx.TextCtrl(self.Text_panel_2, wx.ID_ANY, pos=(0, 0),
                                        size=(TEXT_PANEL_WIDTH1*0.95, TEXT_PANEL_HEIGHT1 * 0.84),
                                        style=wx.TE_LEFT | wx.TE_MULTILINE)
        self.result_text2.SetValue("")
        font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.result_text2.SetFont(font)

        # # =======================[ 結果リスト表示パネル ]=========================================
        # self.listctrl = wx.ListCtrl(self.subPanel1, wx.ID_ANY,
        #                             pos=(THUMBNAIL_PANEL_WIDTH + PDF_PANEL_WIDTH, TEXT_PANEL_HEIGHT1),
        #                             size=(TEXT_PANEL_WIDTH1, FRAME_HEIGHT - TEXT_PANEL_HEIGHT1), style=wx.LC_REPORT)
        #
        # self.listctrl.InsertColumn(0, "番号", wx.LIST_FORMAT_LEFT, 40)
        # self.listctrl.InsertColumn(1, "項目", wx.LIST_FORMAT_LEFT, 120)
        # self.listctrl.InsertColumn(2, "データ", wx.LIST_FORMAT_LEFT, TEXT_PANEL_WIDTH1-160)

        self.pageMax = 0
        self.dpi = PDF_DPI
        self.caregory = CATEGORY
        self.caregory2 = CATEGORY2

        # =======================[ インターバル・タイマーの設定 ]=========================================
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)

        # =======================[ クローズボタン処理の設定 ]=========================================
        # クローズボタンが押された場合の処理を設定(self.ExitHandlerの実行）
        self.Bind(wx.EVT_CLOSE, self.ExitHandler)

        # =======================[ メニューの設定 ]=========================================
        # メニューの設定
        # 「ファイル」バーのメニューの作成
        self.menu_file = wx.Menu()
        self.menu_file.Append(ID_READ_PARA, 'PDFファイル読込' + '\t' + 'Ctrl+O')
        self.menu_file.Append(ID_SAVE, 'データ保存' + '\t' + 'Ctrl+S')

        # menu_file.Append(ID_CALC_RESPONSE, '応答解析' + '\t' + 'Ctrl+R')
        # menu_file.AppendSeparator()
        self.menu_file.Append(ID_EXIT, '終了' + '\t' + 'Ctrl+Q')
        # 「編集」バーのメニューの作成
        self.menu_edit = wx.Menu()
        self.menu_edit.Append(ID_UNDO, '元へ戻す' + '\t' + 'Ctrl+Z')
        self.menu_edit.Append(ID_ROTATE_MINUS, '時計回りに90°回転' + '\t' + 'Ctrl+R')
        self.menu_edit.Append(ID_ROTATE_PLUS, '反時計回りに90°回転' + '\t' + 'Ctrl+L')
        self.menu_edit.Append(ID_PAGE_DELETE, 'ページ削除' + '\t' + 'Ctrl+D')
        self.menu_edit.Append(ID_PAGE_BREAK, '文書の区切りを挿入' + '\t' + 'Ctrl+I')
        self.menu_edit.Append(ID_ERRATA, '正誤表の編集' + '\t' + 'Ctrl+M')
        self.menu_edit.Append(ID_DIC, 'ユーザ辞書の編集' + '\t' + 'Ctrl+N')

        self.menu_view = wx.Menu()
        self.menu_view_ratio = wx.Menu()
        num = 0
        for item in self.raito_items:
            self.menu_view_ratio.Append(ID_VEIW_RATIO + num, item)
            num += 1
        self.menu_view.AppendSubMenu(self.menu_view_ratio, '表示倍率')

        self.menu_box = wx.Menu()
        self.menu_box.Append(ID_BOX_ADD1, 'タイトルボックス追加' + '\t' + 'Ctrl+1')
        self.menu_box.Append(ID_BOX_ADD2, '日付ボックス追加' + '\t' + 'Ctrl+2')
        self.menu_box.Append(ID_BOX_ADD3, '氏名ボックス追加' + '\t' + 'Ctrl+3')
        self.menu_box.Append(ID_BOX_ADD4, '資料ボックス追加' + '\t' + 'Ctrl+4')
        self.menu_box.Append(ID_BOX_SAVE, 'ボックスの保存' + '\t' + 'Ctrl+5')
        self.menu_box.Append(ID_BOX_LOAD, 'ボックスの読込' + '\t' + 'Ctrl+6')
        self.menu_box.Append(ID_BOX_DELL_LAST, '最後のボックス削除' + '\t' + 'Ctrl+7')
        self.menu_box.Append(ID_BOX_DELL_ALL, 'ボックスの全削除' + '\t' + 'Ctrl+8')

        self.menu_tool = wx.Menu()
        self.menu_tool.Append(ID_OCR, 'OCR（テキスト認識）' + '\t' + 'Ctrl+T')
        self.menu_tool.Append(ID_ANALYSIS, 'データ作成' + '\t' + 'Ctrl+A')

        # メニューの作成
        self.menu_bar = wx.MenuBar()
        self.menu_bar.Append(self.menu_file, 'ファイル')
        self.menu_bar.Append(self.menu_edit, '編集')
        self.menu_bar.Append(self.menu_view, '表示')
        self.menu_bar.Append(self.menu_box, 'ボックス')
        self.menu_bar.Append(self.menu_tool, 'ツール')
        # menu_bar.Append(menu_graph, '画面表示')
        # menu_bar.Append(menu_pdf, 'PDF作図')
        # メニューの貼り付け
        self.SetMenuBar(self.menu_bar)
        # メニューの選択が行われた場合の処理(self.selectMenuの実行）
        self.Bind(wx.EVT_MENU, self.selectMenu)

        # データが読み込まれる前はメニュー項目を無効にする。
        self.menu_bar.Enable(ID_UNDO, False)
        self.menu_bar.Enable(ID_SAVE, False)
        self.menu_bar.Enable(ID_ROTATE_MINUS, False)
        self.menu_bar.Enable(ID_ROTATE_PLUS, False)
        self.menu_bar.Enable(ID_PAGE_DELETE, False)
        self.menu_bar.Enable(ID_PAGE_BREAK, False)
        self.menu_bar.Enable(ID_BOX_ADD1, False)
        self.menu_bar.Enable(ID_BOX_ADD2, False)
        self.menu_bar.Enable(ID_BOX_ADD3, False)
        self.menu_bar.Enable(ID_BOX_ADD4, False)
        self.menu_bar.Enable(ID_BOX_SAVE, False)
        self.menu_bar.Enable(ID_BOX_LOAD, False)
        self.menu_bar.Enable(ID_BOX_DELL_LAST, False)
        self.menu_bar.Enable(ID_BOX_DELL_ALL, False)
        self.menu_bar.Enable(ID_OCR, False)
        self.menu_bar.Enable(ID_ANALYSIS, False)

    # =======================[ 終了処理の設定 ]=========================================
    # クローズボタンの処理
    def ExitHandler(self, event):
        '''
        クロースボタンが押された場合のイベント処理
        :param event:
        :return: なし
        '''
        self.mainExit()

    # プログラムの終了処理
    def mainExit(self):
        '''
        プログラムの終了処理
        :return:
        '''
        dlg = wx.MessageDialog(self, message=u"終了します。よろしいですか？", caption=u"終了確認", style=wx.YES_NO)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            wx.Exit()

    # =======================[ メニュー処理の設定 ]=========================================
    # メニューが選択されたときの処理
    def selectMenu(self, event):
        '''
        メニューが選択された場合の処理
        :param event:
        :return: なし
        '''
        id1 = event.GetId()
        if id1 == ID_EXIT or id1 == wx.ID_EXIT:  # 終了処理
            self.mainExit()
        elif id1 == ID_READ_PARA:  # PDFファイルの読み込み
            self.pdf_read()
        elif id1 == ID_ROTATE_MINUS:  # ページの時計方向への回転
            self.RotateImage(-90)
        elif id1 == ID_ROTATE_PLUS:  # ページの反時計方向への回転
            self.RotateImage(90)
        elif id1 == ID_PAGE_DELETE:  # ページの削除
            self.PageDelete()
        elif id1 == ID_UNDO:  # 処理の取り消し
            self.undo_exec()
        elif id1 == ID_PAGE_BREAK:  # 文書の区切りの挿入・削除
            self.pageBreak_Change()
        elif id1 == ID_ERRATA:  # 正誤表の編集
            self.Errata_Edit()
        elif id1 == ID_DIC:  # ユーザー辞書の編集
            self.Dic_Edit()

        elif id1 >= ID_VEIW_RATIO and id1 <= ID_VEIW_RATIO + len(self.raito_items) - 1:
            self.ratio_change(id1 - ID_VEIW_RATIO)

        elif id1 == ID_BOX_ADD1:
            self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=0)
        elif id1 == ID_BOX_ADD2:
            self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=1)
        elif id1 == ID_BOX_ADD3:
            self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=2)
        elif id1 == ID_BOX_ADD4:
            self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=3)
        elif id1 == ID_BOX_SAVE:
            self.box_save()
        elif id1 == ID_BOX_LOAD:
            self.box_load()
        elif id1 == ID_BOX_DELL_LAST:
            self.box_DEL_last()
        elif id1 == ID_BOX_DELL_ALL:
            self.box_DEL()
        elif id1 == ID_OCR:
            self.execOCR()
        elif id1 == ID_ANALYSIS:
            self.text_analysis()

    def Errata_button_handler(self, event):
        self.Errata_Edit()

    def Errata_Edit(self):
        E1 = Errata(None, -1)
        E1.Show()

    def Dic_buttonn_handler(self, event):
        self.Dic_Edit()

    def Dic_Edit(self):
        D1 = UserDic(None, -1)
        D1.Show()

    # =======================[ インターバルタイマー処理の設定 ]=========================================
    # インターバル処理
    def OnTimer(self, event):
        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        flag1 = False  # ページの回転処理があったかどうかチェックする処理
        for t in self.thumbnail_panel:
            p1 = 0
            if t.flag == 90:
                self.undo_copy()
                flag1 = True  # ページの回転があったのでTrue
                t.flag = 0
                p1 = t.page  # 回転したページ番号の取得
                self.pdf_images[p1] = self.pdf_images[p1].rotate(90, expand=True)  # ページの回転
            elif t.flag == -90:
                self.undo_copy()
                flag1 = True  # ページの回転があったのでTrue
                t.flag = 0
                p1 = t.page  # 回転したページ番号の取得
                self.pdf_images[p1] = self.pdf_images[p1].rotate(-90, expand=True)  # ページの回転

            if self.pageOrientarion[p1] == '縦書き':
                self.pageOrientarion[p1] = '横書き'
            else:
                self.pageOrientarion[p1] = '縦書き'

        if flag1:  # ページの回転処理があった場合は画面を書き直す
            self.thumbnail_scroll_panel.DestroyChildren()  # サムネイル表示の削除
            self.pdf_scroll_panel.DestroyChildren()  # PDF表示の削除
            self.image_setting()  # 再描画
            time.sleep(0.5)  # 時間調整

        # 文書の区切り位置に変更が無かったかどうかチェック
        num = 0
        for t in self.thumbnail_text:
            if t.BreakChange:  # サムネイルの区切りの変更の有無（Trueの場合は変更あり）
                t.BreakChange = False  # 変更があったことは読み取ったので２度読みしないようFalseに書き換える。
                self.pageBreak[num] = t.pageBreak  # 文書区切り配列に記録しておく
            num += 1
        num = 0

        # 現在のフォーカスページ（self.page）が文書の区切りかどうかを判別してメニュー表示を切り替える。
        for t in self.thumbnail_text:
            if self.page == t.page + 1:
                if t.pageBreak:
                    self.menu_edit.MenuItems[4].SetItemLabel('文書の区切りを削除：' + '\t' + 'Ctrl+I')
                else:
                    self.menu_edit.MenuItems[4].SetItemLabel('文書の区切りを挿入：' + '\t' + 'Ctrl+I')
                break
            num += 1

        if self.AreaBox_total_n > 0:
            change_page = []
            for i in range(self.pageMax):
                change_page.append(False)

            flag2 = False
            for box in self.AreaBox:
                [a, p] = box
                if a.flag:
                    flag2 = True
                    change_page[p - 1] = True
                    a.flag = False
            if flag2:
                # print('change')
                for i in range(self.pageMax):
                    if change_page[i]:
                        self.thumbnail_panel[i].DestroyChildren()
                n = 0
                for box in self.AreaBox:
                    [a, p] = box
                    n += 1
                    if change_page[p - 1]:
                        pos1 = a.possion1
                        pos2 = a.possion2
                        kind = a.kind
                        self.miniBox[p - 1] = [MiniBox(self.thumbnail_panel[p - 1], pos1=pos1,
                                                       pos2=pos2,
                                                       width=MINI_BOX_LINE_WIDTH, kind=kind, num=n), p]
                    if p == self.page:
                        self.thumbnail_panel[p - 1].OnFocus()

        self.timer.Start(TIMER_INTERVAL1)  # 処理が終わったのでタイマーを再開する。

    # =======================[ 文書の区切りの変更処理 ]=========================================
    def pageBreak_Change(self):
        if self.thumbnail_text[self.page - 1].pageBreak:
            self.thumbnail_text[self.page - 1].pageBreak = False
            self.pageBreak[self.page - 1] = False
        else:
            self.thumbnail_text[self.page - 1].pageBreak = True
            self.pageBreak[self.page - 1] = True
        self.thumbnail_text[self.page - 1].FileBreak()

    # =======================[ 元へ戻すために変数のコピーを作成 ]=========================================
    def undo_copy(self, kind=''):
        # PDFイメージデータのコピー
        self.pdf_images_copy = []
        for image in self.pdf_images:
            self.pdf_images_copy.append(image)
        self.page_copy = self.page  # 現在のページ
        self.pageMax_copy = self.pageMax  # 最大ページ

        # 文書の区切り配列のコピー
        self.pageBreak_copy = []
        for t in self.pageBreak:
            self.pageBreak_copy.append(t)
        # 元へ戻すメニューの書き換え
        self.menu_edit.MenuItems[0].SetItemLabel('元へ戻す：' + kind + '\t' + 'Ctrl+Z')
        self.menu_bar.Enable(ID_UNDO, True)  # 元へ戻すメニューを有効にする。
        self.can_undo_flag = True  # 元へ戻す可能フラグをTrueにする。

    # =======================[ 元へ戻すを実行する処理 ]=========================================
    def undo_exec(self):
        if self.can_undo_flag:  # 元へ戻す可能フラグがTrueの場合。
            self.timer.Stop()  # 処理が終わるまでタイマーを止める。
            self.pdf_images = []  # PDFイメージデータのコピー
            for image in self.pdf_images_copy:
                self.pdf_images.append(image)
            self.pageBreak = []  # 文書の区切り配列のコピー
            for t in self.pageBreak_copy:
                self.pageBreak.append(t)
            self.page = self.page_copy
            self.pageMax = self.pageMax_copy

            # 画面を書き直す
            self.thumbnail_scroll_panel.DestroyChildren()
            self.pdf_scroll_panel.DestroyChildren()
            self.image_setting()
            self.page_set(self.page)
            # 元へ戻すメニューの書き換え
            self.menu_edit.MenuItems[0].SetItemLabel('元へ戻す：' + '\t' + 'Ctrl+Z')
            self.menu_bar.Enable(ID_UNDO, False)  # 元へ戻すメニューを無効にする。
            self.can_undo_flag = False  # 元へ戻す可能フラグをFalseにする。
            self.timer.Start(TIMER_INTERVAL1)  # 処理が終わったのでタイマーを再開する。

    # =======================[ ページの回転処理 ]=========================================
    def RotateImage(self, angle):
        if angle == 90 or angle == -90:
            self.timer.Stop()

            self.undo_copy(kind='回転')

            p1 = self.page - 1
            self.pdf_images[p1] = self.pdf_images[p1].rotate(angle, expand=True)
            self.thumbnail_scroll_panel.DestroyChildren()
            self.pdf_scroll_panel.DestroyChildren()
            if self.pageOrientarion[p1] == '縦書き':
                self.pageOrientarion[p1] = '横書き'
            else:
                self.pageOrientarion[p1] = '縦書き'

            self.image_setting()

            time.sleep(1.0)
            self.pdf_main_panel[self.page - 1].SetFocus()
            self.thumbnail_panel[self.page - 1].SetFocus()
            self.timer.Start(TIMER_INTERVAL1)

    # =======================[ ページ削除処理 ]=========================================
    def PageDelete(self, page=0):
        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        dlg = wx.MessageDialog(self, message=u"このページを削除します。よろしいですか？",
                               caption=u"確認", style=wx.YES_NO | wx.NO_DEFAULT)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.undo_copy(kind='削除')

            if page > 0:
                p1 = page
            else:
                p1 = self.page

            self.thumbnail_panel[p1 - 1].OffFocus()
            self.pdf_main_panel[p1 - 1].OffFocus()
            del self.pdf_images[p1 - 1]
            del self.pageBreak[p1 - 1]
            del self.pageOrientarion[p1 - 1]
            del self.pageSize[p1 - 1]
            if p1 == self.pageMax:
                self.page -= 1
            self.pageMax -= 1
            self.thumbnail_scroll_panel.DestroyChildren()
            self.pdf_scroll_panel.DestroyChildren()
            self.image_setting()
            self.page_set(self.page)

        self.timer.Start(TIMER_INTERVAL1)

    # =======================[ サムネール表示ページのフォーカス処理 ]=========================================
    def OnThumbnailChildFocus(self, event):
        if event.Window.Label.isdigit():
            p1 = int(event.Window.Label)
        else:
            p1 = int(event.Window.Parent.Label)

        if p1 >= 0:
            self.thumbnail_panel[self.page - 1].OffFocus()
            self.pdf_main_panel[self.page - 1].OffFocus()
            self.page = p1 + 1
            self.thumbnail_panel[self.page - 1].OnFocus()
            self.pdf_scroll_panel.ScrollChildIntoView(self.pdf_main_panel[self.page - 1])
            self.pdf_main_panel[self.page - 1].OnFocus()
            self.pdf_scroll_panel.Refresh()
            self.pageText.SetLabel('[ page {}/{} ]'.format(self.page, self.pageMax))

            if self.AreaBox_n[self.page - 1] > 0:
                self.box_DEL_all_button.Enabled = True
            else:
                self.box_DEL_all_button.Enabled = False

    # =======================[ PDF表示ページのフォーカス処理 ]=========================================
    def OnPdfPanelChildFocus(self, event):
        if event.Window.Label.isdigit():
            p1 = int(event.Window.Label)
        else:
            p1 = int(event.Window.Parent.Label)

        if p1 >= 0:
            self.thumbnail_panel[self.page - 1].OffFocus()
            self.pdf_main_panel[self.page - 1].OffFocus()
            self.page = p1 + 1
            self.thumbnail_panel[self.page - 1].OnFocus()
            self.thumbnail_scroll_panel.ScrollChildIntoView(self.thumbnail_panel[self.page - 1])
            self.pdf_main_panel[self.page - 1].OnFocus()
            self.pdf_scroll_panel.Refresh()
            # self.pageText.SetLabel(title = '[ page {}/{}]'.format(self.page, self.pageMax))

            if self.AreaBox_n[self.page - 1] > 0:
                self.box_DEL_all_button.Enabled = True
            else:
                self.box_DEL_all_button.Enabled = False

    # =======================[ PDFファイル読み込みボタンのイベント処理 ]=========================================
    def pdf_read_button_handler(self, evt):
        self.pdf_read()

    # =======================[ PDFファイル読み込み処理 ]=========================================
    def pdf_read(self):

        # ファイルダイアログの表示
        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        iDir = self.data_dir
        filter = "Pdf files (*.pdf)|*.pdf"
        dlg = wx.FileDialog(None, 'select files', iDir, filter, style=wx.FD_OPEN | wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPaths()
        else:
            file = []
        self.pdf_list = list(file)  # 複数のファイル名を取得
        self.pdf_read2()
        self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    def pdf_read2(self):
        fn = len(self.pdf_list)
        if fn > 0:
            aa = ' ファイル ページ {}/{}'.format(1, fn)
            dialog = wx.ProgressDialog(u'PDFデータの読み込み中 ', aa, fn,
                                       parent=None,
                                       style=wx.PD_APP_MODAL | wx.PD_SMOOTH | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT)
            dialog.Show()

            self.pageMax = 0  # ページ数
            self.page = 1  # 最初に表示するページ
            self.pdf_images = []  # PDFのイメージのlist
            self.pageBreak = []  # ページの区切り
            self.pageSize = []  # 各ペー人の用紙サイズ
            self.pageOrientarion = []  # 各ページの向き
            self.AreaBox = []  # 読み取りボックスオブジェクトのlist
            self.AreaBox_kind = []  # 読み取りボックスオブジェクトの種類
            self.AreaBox_page = []  # 読み取りボックスの描画ページlist
            self.AreaBox_total_n = 0  # 読み取りボックスオブジェクトのページ
            self.AreaBox_n = []  # 読み取りボックスの各ページの個数
            self.miniBox = []  # 読み取りボックスオブジェクトのlist
            self.miniBox_kind = []  # 読み取りボックスオブジェクトの種類
            self.miniBox_page = []  # 読み取りボックスの描画ページlist
            self.miniBox_total_n = 0  # 読み取りボックスオブジェクトのページ
            self.miniBox_n = []  # 読み取りボックスの各ページの個数
            self.fname = []  # 読み込みファイル名（複数）
            self.dirName = []  # 読み込みファイルのディレクトリー名（複数）

            p = self.comboPage.GetValue()
            if p == 'all':
                lastpage = None
            else:
                lastpage = int(p)

            # 合計ページ数の算定
            num = 0
            for file_name in self.pdf_list:
                self.dirName.append(os.path.dirname(file_name))
                self.fname.append(os.path.basename(file_name))
                aa = ' ファイル ページ {}/{}'.format(num + 1, fn)
                alive, skip = dialog.Update(num, aa)
                time1 = time.time()
                pdf_file_reader = PdfFileReader(file_name)  # (5)
                page_nums = pdf_file_reader.getNumPages()
                if lastpage != None:
                    if page_nums < lastpage:
                        lastpage = page_nums
                    page_nums = lastpage

                # p1 = pdf_file_reader.getPage(0)

                a = pdf_file_reader.getPageLayout
                self.pageMax += page_nums
                images = convert_from_path(str(file_name), self.dpi, last_page=lastpage)  # pdfの全ページを300dpiでイメージに変換
                for image in images:
                    self.pdf_images.append(image)  # pdfの全ページを300dpiでイメージに変換
                    (x, y) = image.size
                    ps1, po1 = self.paperSize(x, y, self.dpi)
                    self.pageSize.append(ps1)
                    self.pageOrientarion.append(po1)

                    self.pageBreak.append(False)
                    self.AreaBox_n.append(0)
                    self.miniBox_n.append(0)

                    # self.AreaBox.append([])

                num += 1

            self.dataExist1 = True
            self.image_setting()
            self.save_data(dir=self.dirName[0])

            # データが読み込まれれたのでメニュー項目を有効にする。
            self.menu_bar.Enable(ID_ROTATE_MINUS, True)
            self.menu_bar.Enable(ID_ROTATE_PLUS, True)
            self.menu_bar.Enable(ID_PAGE_DELETE, True)
            self.menu_bar.Enable(ID_PAGE_BREAK, True)
            self.menu_bar.Enable(ID_OCR, True)

            self.menu_bar.Enable(ID_BOX_ADD1, True)
            self.menu_bar.Enable(ID_BOX_ADD2, True)
            self.menu_bar.Enable(ID_BOX_ADD3, True)
            self.menu_bar.Enable(ID_BOX_ADD4, True)
            self.menu_bar.Enable(ID_BOX_SAVE, True)
            self.menu_bar.Enable(ID_BOX_LOAD, True)
            self.menu_bar.Enable(ID_BOX_DELL_LAST, True)
            self.menu_bar.Enable(ID_BOX_DELL_ALL, True)

            self.page_minus_button.Enabled = True
            self.page_plus_button.Enabled = True
            # self.ocr_button1.Enabled = True
            self.box_ADD_title_button.Enabled = True
            self.box_ADD_name_button.Enabled = True
            self.box_ADD_date_button.Enabled = True
            self.box_ADD_doc_button.Enabled = True
            self.box_save_button.Enabled = True
            self.box_load_button.Enabled = True

            self.result_text1.Value = ''
            self.result_text2.Value = ''
            self.pageText.SetLabel('[ page {}/{} ]'.format(self.page, self.pageMax))


    def save_data(self, dir=''):
        if dir != '':
            with open(self.para_data, mode='w', encoding='utf-8') as f:
                f.write(dir)

    def load_data(self):
        if os.path.exists(self.para_data):
            with open(self.para_data, mode='r', encoding='utf-8') as f:
                data = f.read()
            # data = open(self.para_data, mode='r', encoding='utf-8')
        else:
            data = self.home + "/PDF_DATA"
        return data

    # =======================[ ページプラスボタンのイベント処理 ]=========================================
    def page_plus_button_handler(self, evt):
        self.page_plus()

    def page_plus(self):
        self.page_set(self.page + 1)

    def page_minus_button_handler(self, evt):
        self.page_minus()

    def page_minus(self):
        self.page_set(self.page - 1)

    def page_set(self, page=1):
        if page >= 1 and page <= self.pageMax:
            self.thumbnail_panel[self.page - 1].OffFocus()
            self.pdf_main_panel[self.page - 1].OffFocus()
            self.page = page
            self.thumbnail_panel[self.page - 1].OnFocus()
            self.pdf_main_panel[self.page - 1].OnFocus()

            self.thumbnail_scroll_panel.ScrollChildIntoView(self.thumbnail_panel[self.page - 1])
            self.pdf_scroll_panel.ScrollChildIntoView(self.pdf_main_panel[self.page - 1])
            self.pageText.SetLabel('[ page {}/{} ]'.format(self.page, self.pageMax))

            if len(self.AreaBox[self.page - 1]) > 0:
                self.box_DEL_all_button.Enabled = True
            else:
                self.box_DEL_all_button.Enabled = False

    def paperSize(self, width=595.68, height=842.4, dpi=300):
        w1 = int(float(width) / dpi * 25.4)
        h1 = int(float(height) / dpi * 25.4)
        x = min(w1, h1)

        if x >= 181 and x <= 183:
            psize = 'B5'
        elif x >= 209 and x <= 211:
            psize = 'A4'
        elif x >= 256 and x <= 258:
            psize = 'B4'
        elif x >= 296 and x <= 298:
            psize = 'A3'
        else:
            psize = 'OTHER'

        if h1 > w1:
            pori = '縦書き'
        else:
            pori = '横書き'

        return psize, pori

    def OnCombo(self, event):
        ratio_copy = self.ratio
        combo = event.GetEventObject()
        ratio1 = combo.GetValue()
        if ratio1.isdigit() and ratio_copy != ratio1:
            self.ratio = ratio1
            self.combo1.SetValue(self.ratio)
            if self.dataExist1:
                self.image_setting()
        # print(combo.GetValue())

    def ratio_change(self, ratio_number):
        ratio_copy = self.ratio
        ratio1 = self.raito_items[ratio_number]
        if ratio1.isdigit() and ratio_copy != ratio1:
            self.ratio = ratio1
            self.combo1.SetValue(self.ratio)
            if self.dataExist1:
                self.image_setting()

    # =======================[ 画面に画像を表示する処理 ]=========================================
    def image_setting(self):
        # if self.pageMax > 0:
        try:
            self.thumbnail_scroll_panel.DestroyChildren()
            self.pdf_scroll_panel.DestroyChildren()
        except:
            pass
        # self.page = 1
        num = 0
        # self.pagepanel = []
        self.thumbnail_panel = []  # サムネイル表示のパネルデータ
        self.thumbnail_text = []
        self.pdf_main_panel = []
        self.pdf_main_text = []
        self.v_layout = wx.BoxSizer(wx.VERTICAL)
        self.v_layout_main = wx.BoxSizer(wx.VERTICAL)
        self.gx = float(THUMBNAIL_PANEL_WIDTH / np.sqrt(2.0)) - self.scw
        self.gx2 = self.panel_height1 - self.scw

        self.ratio = self.combo1.GetValue()
        if self.ratio.isdigit():
            ratio1 = float(self.ratio) / 100.0
        else:
            ratio1 = 1.0

        for pdf_image in self.pdf_images:  # (7)
            s = pdf_image.size
            if s[1] > s[0]:
                small_image = pdf_image.resize((int(self.gx), int(self.gx * np.sqrt(2.0))), Image.BICUBIC)
                wximage = wx.Image(small_image.size[0], small_image.size[1])
                wximage.SetData(small_image.convert('RGB').tobytes())
                small_panel = self.ThumbnailImagePanel(self.thumbnail_scroll_panel, pos=(0, 0),
                                                       size=(self.gx, int(self.gx * np.sqrt(2.0))), image=wximage,
                                                       page=num)

                big_image = pdf_image.resize((int(self.gx2), int(self.gx2 * np.sqrt(2.0))), Image.BICUBIC)
                wximage = wx.Image(big_image.size[0], big_image.size[1])
                wximage.SetData(big_image.convert('RGB').tobytes())

                main_panel = self.PdfImagePanel(self.pdf_scroll_panel, pos=(0, 0),
                                                size=(self.gx2 * ratio1, self.gx2 * np.sqrt(2.0) * ratio1),
                                                image=wximage, page=num)
                text_panel2 = self.TextPanel2(self.pdf_scroll_panel, pos=(0, 0),
                                              size=(self.gx2 * ratio1, 30), page=num, pageMax=self.pageMax,
                                              paperSize=self.pageSize[self.page - 1],
                                              orientation=self.pageOrientarion[self.page - 1])

            else:
                small_image = pdf_image.resize((int(self.gx * np.sqrt(2.0)), int(self.gx)), Image.BICUBIC)
                # wximage = wx.EmptyImage(image2.size[0], image2.size[1])
                wximage = wx.Image(small_image.size[0], small_image.size[1])
                wximage.SetData(small_image.convert('RGB').tobytes())
                small_panel = self.ThumbnailImagePanel(self.thumbnail_scroll_panel, pos=(0, 0),
                                                       size=(self.gx * np.sqrt(2.0), self.gx), image=wximage, page=num)

                big_image = pdf_image.resize((int(self.gx2), int(self.gx2 / np.sqrt(2.0))), Image.BICUBIC)
                wximage = wx.Image(big_image.size[0], big_image.size[1])
                wximage.SetData(big_image.convert('RGB').tobytes())
                main_panel = self.PdfImagePanel(self.pdf_scroll_panel, pos=(0, 0),
                                                size=(self.gx2 * np.sqrt(2.0) * ratio1, self.gx2 * ratio1),
                                                image=wximage, page=num)
                text_panel2 = self.TextPanel2(self.pdf_scroll_panel, pos=(0, 0),
                                              size=(self.gx2 * np.sqrt(2.0) * ratio1, 30), page=num,
                                              pageMax=self.pageMax,
                                              paperSize=self.pageSize[self.page - 1],
                                              orientation=self.pageOrientarion[self.page - 1])

            self.thumbnail_panel.append(small_panel)
            self.pdf_main_panel.append(main_panel)

            text_panel = self.TextPanel(self.thumbnail_scroll_panel, pos=(0, 0),
                                        size=(self.gx, 30), page=num, pageMax=self.pageMax,
                                        pageBreak=self.pageBreak[num])
            self.thumbnail_text.append(text_panel)

            # text_panel2 = self.TextPanel(self.pdf_scroll_panel, pos=(0, 0),
            #                              size=(self.gx2, 30), page = num, pageMax=self.pageMax)
            self.pdf_main_text.append(text_panel2)

            if self.AreaBox_n[num] > 0:
                for [a, p] in self.AreaBox:
                    if p - 1 == num:
                        a.boxDraw(main_panel)

            if self.miniBox_n[num] > 0:
                for [a, p] in self.miniBox:
                    if p - 1 == num:
                        a.boxDraw(small_panel)

            num += 1

        self.thumbnail_lyout()
        self.thumbnail_panel[self.page - 1].OnFocus()

        # self.thumbnail_scroll_panel.ScrollChildIntoView(self.thumbnail_panel[self.page - 1])

        self.pdf_panel_lyout()
        self.pdf_main_panel[self.page - 1].OnFocus()
        # self.pdf_scroll_panel.ScrollChildIntoView(self.pdf_main_panel[self.page - 1])
        # self.timer.Start(3000)

    # =======================[ サムネイル表示画面に画像を表示する処理 ]=========================================
    def thumbnail_lyout(self):
        self.v_layout = wx.BoxSizer(wx.VERTICAL)
        for i in range(self.pageMax):
            self.v_layout.Add(self.thumbnail_panel[i], 0, wx.ALIGN_CENTER)
            self.v_layout.Add(self.thumbnail_text[i], 0, wx.ALIGN_CENTER)

        self.thumbnail_scroll_panel.SetSizer(self.v_layout)
        self.thumbnail_scroll_panel.Update()
        self.thumbnail_scroll_panel.SetupScrolling()
        self.Refresh()
        # self.thumbnail_panel[self.page - 1].OnFocus()

    # =======================[ PDF表示画面に画像を表示する処理 ]=========================================
    def pdf_panel_lyout(self):
        self.v_layout_main = wx.BoxSizer(wx.VERTICAL)
        for i in range(self.pageMax):
            # self.v_layout_main.Add(self.pdf_main_panel[i], 0, wx.ALIGN_CENTER) # ALIGN_CENTER_HORIZONTAL
            # self.v_layout_main.Add(self.pdf_main_text[i], 0, wx.ALIGN_CENTER)
            self.v_layout_main.Add(self.pdf_main_panel[i], 0, wx.ALIGN_CENTER_HORIZONTAL)  # ALIGN_CENTER_HORIZONTAL
            self.v_layout_main.Add(self.pdf_main_text[i], 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.pdf_scroll_panel.SetSizer(self.v_layout_main)
        self.pdf_scroll_panel.Update()
        self.pdf_scroll_panel.SetupScrolling()
        self.Refresh()
        # self.pdf_panel[self.page - 1].OnFocus()

    #
    # =======================[ ページ数表示パネルのクラス ]=========================================
    class TextPanel(wx.Panel):
        '''
        イメージを貼り付けるパネル　xw.Panelを継承
        '''

        def __init__(self, parent, pos=(0, 0), size=(100, 100), page=0, pageMax=0, pageBreak=False):
            self.p = super().__init__(parent, size=size, pos=pos)
            self.page = page
            self.pageMax = pageMax
            self.pageBreak = pageBreak
            # font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            # text_layout = wx.BoxSizer(wx.VERTICAL)
            # text = wx.StaticText(self, wx.ID_ANY,
            #                      '[ page {}/{} ]'.format(self.page + 1, self.pageMax))
            # text.SetFont(font)
            # text_layout.Add(text, 0, wx.ALIGN_TOP)
            # self.SetSizer(text_layout)
            self.Label = str(self.page).zfill(3)
            self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClic)
            self.FileBreak()
            self.BreakChange = False

        def OnRightUp(self, event):
            if not hasattr(self, "popupID1"):  # 起動後、一度だけ定義する。
                self.popupID1 = wx.NewId()
                self.popupID2 = wx.NewId()

                self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
                self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)

            menu = wx.Menu()
            if self.pageBreak:
                menu.Append(self.popupID2, "文書の区切りを削除")
            else:
                menu.Append(self.popupID1, "文書の区切りを挿入")

            self.PopupMenu(menu)
            menu.Destroy()

        def OnDClic(self, event):
            if self.pageBreak:
                self.pageBreak = False
            else:
                self.pageBreak = True
            self.FileBreak()

        def OnPopupOne(self, event):
            self.pageBreak = True
            self.FileBreak()
            self.BreakChange = True

        def OnPopupTwo(self, event):
            self.pageBreak = False
            self.FileBreak()
            self.BreakChange = True

        def FileBreak(self):
            self.DestroyChildren()
            # self.SetSize(self.size)
            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            if self.pageBreak:
                text = wx.StaticText(self, wx.ID_ANY,
                                     '[ page {}/{} ===[Break]=== ]'.format(self.page + 1, self.pageMax))
            else:
                text = wx.StaticText(self, wx.ID_ANY,
                                     '[ page {}/{} ]'.format(self.page + 1, self.pageMax))
            text.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            text.Bind(wx.EVT_LEFT_DCLICK, self.OnDClic)
            text_layout = wx.BoxSizer(wx.VERTICAL)
            text.SetFont(font)
            text_layout.Add(text, 0, wx.ALIGN_TOP)
            self.SetSizer(text_layout)
            self.Refresh()

        #
        # =======================[ ページ数表示パネルのクラス ]=========================================

    class TextPanel2(wx.Panel):
        '''
        イメージを貼り付けるパネル　xw.Panelを継承
        '''

        def __init__(self, parent, pos=(0, 0), size=(100, 100), page=0, pageMax=0, pageBreak=False, paperSize='A4',
                     orientation='縦書き'):
            self.p = super().__init__(parent, size=size, pos=pos)
            self.page = page
            self.pageMax = pageMax
            self.pageBreak = pageBreak
            self.paperSize = paperSize
            self.orientation = orientation

            # font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            # text_layout = wx.BoxSizer(wx.VERTICAL)
            # text = wx.StaticText(self, wx.ID_ANY,
            #                      '[ page {}/{} ]'.format(self.page + 1, self.pageMax))
            # text.SetFont(font)
            # text_layout.Add(text, 0, wx.ALIGN_TOP)
            # self.SetSizer(text_layout)
            self.Label = str(self.page).zfill(3)
            self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            self.Bind(wx.EVT_LEFT_DCLICK, self.OnDClic)
            self.FileBreak()
            self.BreakChange = False

        def OnRightUp(self, event):
            if not hasattr(self, "popupID1"):  # 起動後、一度だけ定義する。
                self.popupID1 = wx.NewId()
                self.popupID2 = wx.NewId()

                self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
                self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)

            menu = wx.Menu()
            if self.pageBreak:
                menu.Append(self.popupID2, "文書の区切りを削除")
            else:
                menu.Append(self.popupID1, "文書の区切りを挿入")

            self.PopupMenu(menu)
            menu.Destroy()

        def OnDClic(self, event):
            if self.pageBreak:
                self.pageBreak = False
            else:
                self.pageBreak = True
            self.FileBreak()

        def OnPopupOne(self, event):
            self.pageBreak = True
            self.FileBreak()
            self.BreakChange = True

        def OnPopupTwo(self, event):
            self.pageBreak = False
            self.FileBreak()
            self.BreakChange = True

        def FileBreak(self):
            self.DestroyChildren()
            # self.SetSize(self.size)
            font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

            if self.pageBreak:
                text = wx.StaticText(self, wx.ID_ANY,
                                     '[ page {}/{} サイス：{}:{} ===[Break]=== ]'.format(self.page + 1, self.pageMax,
                                                                                     self.paperSize, self.orientation))
            else:
                text = wx.StaticText(self, wx.ID_ANY,
                                     '[ page {}/{} サイス：{}:{}]'.format(self.page + 1, self.pageMax, self.paperSize,
                                                                      self.orientation))
            # text.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
            # text.Bind(wx.EVT_LEFT_DCLICK, self.OnDClic)
            text_layout = wx.BoxSizer(wx.VERTICAL)
            text.SetFont(font)
            text_layout.Add(text, 0, wx.ALIGN_TOP)
            self.SetSizer(text_layout)
            self.Refresh()

    #
    # =======================[ サムネイル表示パネルのクラス ]=========================================
    class ThumbnailImagePanel(wx.Panel):
        '''
        イメージを貼り付けるパネル　xw.Panelを継承
        '''

        def __init__(self, parent, pos=(0, 0), size=(100, 100), image=None, page=0):
            self.p = super().__init__(parent, size=size, pos=pos)
            # imageがあれば、ビットマップに変換してパネルに貼り付ける。無ければ、普通のパネルと同じ。
            if image != None:
                self.image = image
                self.image = self.image.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
                self.bitmap = self.image.ConvertToBitmap()
                self.Bind(wx.EVT_PAINT, self.OnPaint)
                self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
                # self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
                self.page = page
                self.focus = False
                self.w_length = size[0]
                self.h_length = size[1]
                self.width = 4
                self.color = 'grey'
                self.flag = 0
                self.Label = str(self.page).zfill(3)
                self.delete_flag = False

        # =======================[ フォーカスされたことを明示するために枠線を描画 ]=========================================
        def OnFocus(self):
            self.v_line1 = wx.Panel(self, size=(self.width, self.h_length), pos=(0, 0))
            self.v_line1.SetBackgroundColour(self.color)
            self.v_line2 = wx.Panel(self, size=(self.width, self.h_length), pos=(self.w_length - self.width, 0))
            self.v_line2.SetBackgroundColour(self.color)
            self.h_line1 = wx.Panel(self, size=(self.w_length, self.width), pos=(0, 0))
            self.h_line1.SetBackgroundColour(self.color)
            self.h_line2 = wx.Panel(self, size=(self.w_length, self.width), pos=(0, self.h_length - self.width))
            self.h_line2.SetBackgroundColour(self.color)
            self.focus = True

        # =======================[ 枠線を削除 ]=========================================
        def OffFocus(self):
            try:
                self.v_line1.Destroy()
                self.v_line2.Destroy()
                self.h_line1.Destroy()
                self.h_line2.Destroy()
                self.focus = False
            except:
                pass

        # =======================[ 再描画イベント処理（画像の貼り付け） ]=========================================
        def OnPaint(self, event=None):
            # ビットマップの描画をOnPaint（再描画時）割り込み処理の時に行う。
            deviceContext = wx.PaintDC(self)
            deviceContext.Clear()
            deviceContext.DrawBitmap(self.bitmap, 0, 0, True)

        # =======================[ マウスの右クリックの処理　フロートメニューの表示 ]=========================================
        def OnRightUp(self, event):
            if not hasattr(self, "popupID1"):  # 起動後、一度だけ定義する。
                self.popupID1 = wx.NewId()
                self.popupID2 = wx.NewId()

                self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
                self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)

            menu = wx.Menu()
            menu.Append(self.popupID1, "時計回りに90°回転")
            menu.Append(self.popupID2, "反時計回りに90°回転")

            self.PopupMenu(menu)
            menu.Destroy()

        # =======================[ メニュー１の処理（時計回りの回転） ]=========================================
        def OnPopupOne(self, event):
            self.flag1 = -90

        # =======================[ メニュー２の処理（反時計回りの回転） ]=========================================
        def OnPopupTwo(self, event):
            self.flag1 = 90

        # =======================[ 回転処理のフラグのプロパティーの読み込む ]=========================================
        @property
        def flag(self):
            return self.flag1

        # =======================[ 回転処理のフラグのプロパティーの書込 ]=========================================
        @flag.setter
        def flag(self, f):
            self.flag1 = f

    #
    # =======================[ PDF表示パネルのクラス ]=========================================
    class PdfImagePanel(wx.Panel):
        '''
        イメージを貼り付けるパネル　xw.Panelを継承
        '''

        def __init__(self, parent, pos=(0, 0), size=(100, 100), image=None, page=0, psize='A4', orientation='縦書き'):
            self.p = super().__init__(parent, size=size, pos=pos)
            # imageがあれば、ビットマップに変換してパネルに貼り付ける。無ければ、普通のパネルと同じ。
            if image != None:
                image = image.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
                self.bitmap = image.ConvertToBitmap()
                self.Bind(wx.EVT_PAINT, self.OnPaint)
                # self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
                # self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
                self.page = page
                self.focus = False
                self.w_length = size[0]
                self.h_length = size[1]
                self.width = 4
                self.color = 'grey'
                self.Label = str(self.page).zfill(3)
                self.flag = 0
                self.pageSize = psize
                self.orientation = orientation

        # =======================[ フォーカスされたことを明示するために枠線を描画 ]=========================================
        def OnFocus(self):
            self.v_line1 = wx.Panel(self, size=(self.width, self.h_length), pos=(0, 0))
            self.v_line1.SetBackgroundColour(self.color)
            self.v_line2 = wx.Panel(self, size=(self.width, self.h_length), pos=(self.w_length - self.width, 0))
            self.v_line2.SetBackgroundColour(self.color)
            self.h_line1 = wx.Panel(self, size=(self.w_length, self.width), pos=(0, 0))
            self.h_line1.SetBackgroundColour(self.color)
            self.h_line2 = wx.Panel(self, size=(self.w_length, self.width), pos=(0, self.h_length - self.width))
            self.h_line2.SetBackgroundColour(self.color)
            self.focus = True

        # =======================[ 枠線を削除 ]=========================================
        def OffFocus(self):
            try:
                self.v_line1.Destroy()
                self.v_line2.Destroy()
                self.h_line1.Destroy()
                self.h_line2.Destroy()
                self.focus = False
            except:
                pass

        # =======================[ 再描画イベント処理（画像の貼り付け） ]=========================================
        def OnPaint(self, event=None):
            # ビットマップの描画をOnPaint（再描画時）割り込み処理の時に行う。
            deviceContext = wx.PaintDC(self)
            deviceContext.Clear()
            deviceContext.DrawBitmap(self.bitmap, 0, 0, True)

        # =======================[ マウスの右クリックの処理　フロートメニューの表示 ]=========================================
        # 削除
        #
        # def OnRightUp(self, event):
        #     if not hasattr(self, "popupID2"):  # 起動後、一度だけ定義する。
        #         self.popupID1 = wx.NewId()
        #         self.popupID2 = wx.NewId()
        #
        #         self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
        #         self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
        #
        #     menu = wx.Menu()
        #     menu.Append(self.popupID1, "時計回りに90°回転")
        #     menu.Append(self.popupID2, "反時計回りに90°回転")
        #
        #     self.PopupMenu(menu)
        #     menu.Destroy()
        #
        # # def OnLeftDown(self, event):
        # #     print(self.page + 1)
        #
        # def OnPopupOne(self, event):
        #     # (sw ,sh) = self.Size
        #     # self.SetSize((sh, sw))
        #     # self.OffFocus()
        #     # self.h_length = sw
        #     # self.w_length = sh
        #     # self.SetPosition((0,0))
        #     # self.image = self.image.Rotate90(clockwise=True)
        #     # self.image = self.image.Scale(sh, sw, wx.IMAGE_QUALITY_HIGH)
        #     # self.bitmap = self.image.ConvertToBitmap()
        #     # self.OnFocus()
        #     self.flag1 = -90

        # def OnPopupTwo(self, event):
        #     self.flag1 = 90
        #     # print('Application will quit.')
        #     # self.frm.Close()

    def ocr_button_handler1(self, event):
        self.execOCR()

    def cnn_button_handler(self, event):
        self.execCNN()

    def analysis_button_handler(self, event):
        t1 = self.text_analysis()
        self.result_text2.Value = t1

    def result_save_button_handler(self, event):
        self.result_save()

    def result_load_button_handler(self, event):
        self.result_load()

    # =======================[ 読み取り範囲ボックスの追加 ]=========================================
    def box_ADD_title_button_handler(self, event):
        self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=0)

    def box_ADD_date_button_handler(self, event):
        self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=1)

    def box_ADD_name_button_handler(self, event):
        self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=2)

    def box_ADD_doc_button_handler(self, event):
        self.box_ADD(pos1=SMALL_BOX_P1, pos2=SMALL_BOX_P2, kind=3)

    # =======================[ 読み取り範囲ボックスの全削除 ]=========================================
    def box_DEL_all_buttonn_handler(self, event):
        self.box_DEL()

    def box_DEL_last_buttonn_handler(self, event):
        self.box_DEL_last()

    def box_save_button_handler(self, event):
        self.box_save()

    def box_load_button_handler(self, event):
        self.box_load()

    # =======================[ 読み取り範囲ボックスの追加 ]=========================================
    def box_ADD(self, pos1=(5, 5), pos2=(95, 95), kind=0):
        self.AreaBox_total_n += 1
        self.AreaBox_n[self.page - 1] += 1
        self.AreaBox.append([ReadAreaBox(self.pdf_main_panel[self.page - 1], pos1=pos1,
                                         pos2=pos2,
                                         width=AREA_BOX_LINE_WIDTH, kind=kind, num=self.AreaBox_total_n), self.page])
        self.AreaBox_kind.append(kind)
        self.AreaBox_page.append(self.page)

        self.miniBox_total_n += 1
        self.miniBox_n[self.page - 1] += 1
        self.miniBox.append([MiniBox(self.thumbnail_panel[self.page - 1], pos1=pos1,
                                     pos2=pos2,
                                     width=MINI_BOX_LINE_WIDTH, kind=kind, num=self.miniBox_total_n), self.page])
        self.miniBox_kind.append(kind)
        self.miniBox_page.append(self.page)

        if self.AreaBox_total_n > 0:
            self.ocr_button1.Enabled = True
            self.cnn_button.Enabled = True
            self.box_DEL_all_button.Enabled = True
            self.box_DEL_last_button.Enabled = True

    # =======================[ 読み取り範囲ボックスの追加 ]=========================================
    def box_ADD2(self, pos1=(5, 5), pos2=(95, 95), kind=0, page=1):
        self.AreaBox_total_n += 1
        self.AreaBox_n[page - 1] += 1
        self.AreaBox.append([ReadAreaBox(self.pdf_main_panel[page - 1], pos1=pos1,
                                         pos2=pos2,
                                         width=AREA_BOX_LINE_WIDTH, kind=kind, num=self.AreaBox_total_n), page])
        self.AreaBox_page.append(page)

        self.miniBox_total_n += 1
        self.miniBox_n[page - 1] += 1
        self.miniBox.append([MiniBox(self.thumbnail_panel[page - 1], pos1=pos1,
                                     pos2=pos2,
                                     width=MINI_BOX_LINE_WIDTH, kind=kind, num=self.miniBox_total_n), page])
        self.miniBox_page.append(page)

        if self.AreaBox_total_n > 0:
            self.ocr_button1.Enabled = True
            self.cnn_button.Enabled = True
            self.box_DEL_all_button.Enabled = True
            self.box_DEL_last_button.Enabled = True

    # =======================[ 読み取り範囲ボックスの全削除 ]=========================================
    def box_DEL(self):
        for i in range(self.pageMax):
            if self.AreaBox_n[i] > 0:
                self.pdf_main_panel[i].DestroyChildren()
                self.AreaBox_n[i] = 0
        self.AreaBox_total_n = 0
        self.AreaBox = []
        self.AreaBox_kind = []

        for i in range(self.pageMax):
            if self.miniBox_n[i] > 0:
                self.thumbnail_panel[i].DestroyChildren()
                self.miniBox_n[i] = 0
        self.miniBox_total_n = 0
        self.miniBox = []
        self.miniBox_kind = []

        self.result_text1.Value = ''
        self.result_text2.Value = ''
        self.menu_bar.Enable(ID_OCR, False)
        self.menu_bar.Enable(ID_ANALYSIS, False)
        self.ocr_button1.Enabled = False
        self.cnn_button.Enabled = False
        self.analysis_button.Enabled = False
        self.box_DEL_all_button.Enabled = False
        self.box_DEL_last_button.Enabled = False

        self.pdf_main_panel[self.page - 1].OnFocus()
        self.thumbnail_panel[self.page - 1].OnFocus()

    # =======================[ 最後の読み取り範囲ボックスの削除 ]=========================================
    def box_DEL_last(self):
        if self.AreaBox_total_n == 1:
            self.box_DEL()
        elif self.AreaBox_total_n > 1:
            pos1 = []
            pos2 = []
            kind = []
            page = []
            for (a, p) in self.AreaBox:
                pos1.append(a.possion1)
                pos2.append(a.possion2)
                kind.append(a.kind)
                page.append(p)

            self.box_DEL()

            n = len(page) - 1
            self.AreaBox_total_n = 0
            self.miniBox_total_n = 0
            for i in range(n):
                self.box_ADD2(pos1=pos1[i], pos2=pos2[i], kind=kind[i], page=page[i])

            self.result_text1.Value = ''
            self.result_text2.Value = ''
            self.menu_bar.Enable(ID_OCR, True)
            self.menu_bar.Enable(ID_ANALYSIS, False)
            self.ocr_button1.Enabled = True
            self.cnn_button.Enabled = True
            self.analysis_button.Enabled = False
            self.box_DEL_all_button.Enabled = True
            self.box_DEL_last_button.Enabled = True

            self.pdf_main_panel[self.page - 1].OnFocus()
            self.thumbnail_panel[self.page - 1].OnFocus()

    # =======================[ 読み取り範囲ボックスの保存 ]=========================================
    def box_save(self):

        if self.AreaBox_total_n > 0:
            self.timer.Stop()  # 処理が終わるまでタイマーを止める。

            if os.path.exists(self.box_data_dir) == False:  # ディレクトリーが存在しない場合作成する。
                os.mkdir(self.box_data_dir)

            self.iDir = os.getcwd()  # カレントディレクトリーの読込
            os.chdir(self.box_data_dir)
            self.boxFile = 'box_data1.box'
            self.iDir2 = os.getcwd()  # 変更後のディレクトリーの読込
            openFileDialog = wx.FileDialog(self, "ボックスデータファイルの保存", self.iDir2, self.boxFile,
                                           "BOX files (*.box)|*.box",
                                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            _filename = ''
            openFileDialog.ShowModal()
            _filename = openFileDialog.GetPath()

            if _filename != '':
                with open(_filename, mode='w') as f:
                    # f.write('{}\n'.format(self.AreaBox_total_n))
                    for (b, p) in self.AreaBox:
                        a = '{},{},{},{},{},{}\n'.format(b.possion1[0], b.possion1[1], b.possion2[0], b.possion2[1],
                                                         b.kind, p)
                        f.write(a)
                # page_success = True
                # self.pdf1 = PdfPages(_filename)

            os.chdir(self.iDir)
            self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    # =======================[ 読み取り範囲ボックスの読み込み ]=========================================
    def box_load(self):
        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        iDir = self.box_data_dir
        filter = "BOX files (*.box)|*.box"
        dlg = wx.FileDialog(None, 'select files', iDir, filter, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            # すでにボックスがある場合はすべて消去
            if self.AreaBox_total_n > 0:
                self.box_DEL()

            file = dlg.GetPaths()
            data = open(file[0], mode='r')
            n = 0
            self.AreaBox_total_n = 0
            for line in data:
                line = line.replace('\n', '')
                a = line.split(',')
                pos1 = (float(a[0]), float(a[1]))
                pos2 = (float(a[2]), float(a[3]))
                kind = int(a[4])
                page = int(a[5])
                self.box_ADD2(pos1=pos1, pos2=pos2, kind=kind, page=page)
                n += 1

            self.menu_bar.Enable(ID_OCR, True)
            self.ocr_button1.Enabled = True
            self.cnn_button.Enabled = True
            self.box_DEL_all_button.Enabled = True
            self.box_DEL_last_button.Enabled = True

        self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    # =======================[ 読み取り範囲ボックスの全削除 ]=========================================
    def execOCR(self):

        self.timer.Stop()  # 処理が終わるまでタイマーを止める。

        er = errata()
        self.result_text1.Value = ''
        # 2.OCRエンジンの取得
        tools = pyocr.get_available_tools()
        tool = tools[0]

        self.title_text = []
        self.date_text = []
        self.name_text = []
        self.doc_text = []
        result = ''
        result2 = ''
        n = 0
        for [box, p] in self.AreaBox:
            n += 1
            p1 = box.possion1
            p2 = box.possion2
            kind = box.kind
            # self.pdf_images[i]
            im = self.pdf_images[p - 1]
            h1 = im.height
            w1 = im.width
            y1 = int(p1[1] * 0.01 * h1)
            x1 = int(p1[0] * 0.01 * w1)
            y2 = int(p2[1] * 0.01 * h1)
            x2 = int(p2[0] * 0.01 * w1)
            im_crop = im.crop((x1, y1, x2, y2))

            # plt.imshow(im_crop)
            # plt.show()
            builder = pyocr.builders.TextBuilder(tesseract_layout=6)
            # builder = pyocr.builders.LineBoxBuilder(tesseract_layout=6)
            result = tool.image_to_string(im_crop, lang="jpn", builder=builder)
            # result = result.replace(' ', '', 500)
            result = er.exec_errata(text=result)
            print(result)
            # result += '\n'

            if kind == 0:
                self.title_text.append(result)
            elif kind == 1:
                self.date_text.append(result)
            elif kind == 2:
                self.name_text.append(result)
            elif kind == 3:
                self.doc_text.append(result)

        if len(self.title_text) > 0:
            result2 += '=====[ title ]=====\n'
            for t in self.title_text:
                result2 += t

        if len(self.date_text) > 0:
            result2 += '=====[ date ]=====\n'
            for t in self.date_text:
                result2 += t

        if len(self.name_text) > 0:
            result2 += '=====[ name ]=====\n'
            for t in self.name_text:
                result2 += t

        if len(self.doc_text) > 0:
            result2 += '=====[ doc ]=====\n'
            for t in self.doc_text:
                result2 += t

        self.result_text1.Value = result2
        self.analysis_button.Enabled = True
        self.menu_bar.Enable(ID_ANALYSIS, True)
        self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    # =======================[ 手書き文字認識 ]=========================================
    def execCNN(self):

        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        kf = kanji_find()
        # img, img3, text = kf.kanji_text(image_main, PLOT_FLAG=True)
        er = errata()
        self.result_text1.Value = ''
        # 2.OCRエンジンの取得
        # tools = pyocr.get_available_tools()
        # tool = tools[0]

        self.title_text = []
        self.date_text = []
        self.name_text = []
        self.doc_text = []
        result = ''
        result2 = ''
        n = 0
        for [box, p] in self.AreaBox:
            n += 1
            p1 = box.possion1
            p2 = box.possion2
            kind = box.kind
            # self.pdf_images[i]
            im = self.pdf_images[p - 1]
            h1 = im.height
            w1 = im.width
            y1 = int(p1[1] * 0.01 * h1)
            x1 = int(p1[0] * 0.01 * w1)
            y2 = int(p2[1] * 0.01 * h1)
            x2 = int(p2[0] * 0.01 * w1)
            im_crop = im.crop((x1, y1, x2, y2))

            # plt.imshow(im_crop)
            # plt.show()
            # builder = pyocr.builders.TextBuilder(tesseract_layout=6)
            # builder = pyocr.builders.LineBoxBuilder(tesseract_layout=6)
            # result = tool.image_to_string(im_crop, lang="jpn", builder=builder)
            # result = result.replace(' ', '', 500)
            img, img3, result = kf.kanji_text(im_crop, PLOT_FLAG=False)
            result = er.exec_errata(text=result)
            print(result)
            # result += '\n'

            if kind == 0:
                self.title_text.append(result)
            elif kind == 1:
                self.date_text.append(result)
            elif kind == 2:
                self.name_text.append(result)
            elif kind == 3:
                self.doc_text.append(result)

        if len(self.title_text) > 0:
            result2 += '=====[ title ]=====\n'
            for t in self.title_text:
                result2 += t

        if len(self.date_text) > 0:
            result2 += '=====[ date ]=====\n'
            for t in self.date_text:
                result2 += t

        if len(self.name_text) > 0:
            result2 += '=====[ name ]=====\n'
            for t in self.name_text:
                result2 += t

        if len(self.doc_text) > 0:
            result2 += '=====[ doc ]=====\n'
            for t in self.doc_text:
                result2 += t

        self.result_text1.Value = result2
        self.analysis_button.Enabled = True
        self.menu_bar.Enable(ID_ANALYSIS, True)
        self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    # =======================[ 解析結果の保存 ]=========================================
    def result_save(self):
        text = self.result_text2.Value
        if text != '':
            self.timer.Stop()  # 処理が終わるまでタイマーを止める。

            if os.path.exists(self.save_dir) == False:  # ディレクトリーが存在しない場合作成する。
                os.mkdir(self.save_dir)

            self.iDir = os.getcwd()  # カレントディレクトリーの読込
            os.chdir(self.save_dir)
            name1 = os.path.splitext(os.path.basename(self.fname[0]))[0]
            if name1[-2:] == '-1':
                self.save_name = name1[:-2] + '.csv'
            else:
                self.save_name = name1 + '.csv'

            self.iDir2 = os.getcwd()  # 変更後のディレクトリーの読込
            openFileDialog = wx.FileDialog(self, "解析結果の保存", self.iDir2, self.save_name,
                                           "csv files (*.csv)|*.csv",
                                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

            _filename = ''
            openFileDialog.ShowModal()
            _filename = openFileDialog.GetPath()

            if _filename != '':
                with open(_filename, mode='w', encoding='utf-8') as f:
                    f.write(text)

            os.chdir(self.iDir)
            self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開

    # =======================[ 解析結果の読込 ]=========================================
    def result_load(self):
        self.timer.Stop()  # 処理が終わるまでタイマーを止める。
        iDir = self.save_dir
        filter = "DATA files (*.csv)|*.csv"
        dlg = wx.FileDialog(None, 'select files', iDir, filter, style=wx.FD_OPEN)

        if dlg.ShowModal() == wx.ID_OK:
            file = dlg.GetPaths()
            data = open(file[0], mode='r', encoding='utf-8')
            n = 0
            text = ''
            files = []

            for line in data:
                result = line.replace('\n', '')
                a = result.split(',')
                kind = a[0]
                if kind != '項目':
                    text += line
                    if kind == "pdf":
                        files.append(a[1])

            if len(files)>0:
                self.pdf_list = files
                self.pdf_read2()

            self.result_text2.Value = text

            self.menu_bar.Enable(ID_OCR, True)
            self.ocr_button1.Enabled = True
            self.cnn_button.Enabled = True
            self.box_DEL_all_button.Enabled = True
            self.box_DEL_last_button.Enabled = True
            self.result_save_button.Enabled = True

        self.timer.Start(TIMER_INTERVAL1)  # タイマーの再開


    # =======================[ テキストの形態解析 ]=========================================
    def text_analysis(self):
        ocr = self.result_text1.Value
        if ocr != '':
            token_filters = []
            char_filters = []
            tokenizer = Tokenizer(self.user_dic, udic_enc="utf8")
            analyzer = Analyzer(char_filters, tokenizer, token_filters)

            self.title_text = []
            self.date_text = []
            self.name_text = []
            self.doc_text = []

            ocr = ocr.splitlines()
            kind = 0
            for line in ocr:
                if line == '=====[ title ]=====':
                    kind = 0
                elif line == '=====[ date ]=====':
                    kind = 1
                elif line == '=====[ name ]=====':
                    kind = 2
                elif line == '=====[ doc ]=====':
                    kind = 3
                else:
                    if kind == 0:
                        self.title_text.append(line)
                    elif kind == 1:
                        self.date_text.append(line)
                    elif kind == 2:
                        self.name_text.append(line)
                    elif kind == 3:
                        self.doc_text.append(line)

            result = ''
            if len(self.title_text) > 0:
                for line in self.title_text:
                    self.title = line
                    self.kind = 'その他'
                    for cat in self.caregory:
                        if line.count(cat):
                            self.kind = cat
                            break
                    if self.kind == 'その他':
                        for cat in self.caregory2:
                            if line.count(cat):
                                self.kind = cat + '議事録'
                                break
                    result += '分類,' + self.kind + '\n'
                    result += 'タイトル,' + self.title + '\n'
                    break

            if len(self.date_text) > 0:
                for line in self.date_text:
                    self.title = line
                    day_list = self.day_find(line)
                    if len(day_list) > 0:
                        self.day = year_convart(day_list[0])
                        result += '作成日,' + self.day + '\n'
                    break

            if len(self.name_text) > 0:
                text = ''
                for line in self.name_text:
                    text += line + '\n'
                self.name_list = []
                if text != '':
                    nameflag = False
                    name = ''
                    for token in analyzer.analyze(text):
                        if token.base_form != '\n':
                            t1 = str(token).replace('\t', ',')
                            t2 = t1.split(',')
                            if t2[3] == '人名' and t2[4] == '一般':
                                name = t2[0]
                            else:
                                if nameflag != True:
                                    if t2[4] == '姓':
                                        name = t2[0]
                                        nameflag = True
                                else:
                                    if t2[4] == '名' or t2[3] == '役職':
                                        name += t2[0]
                                    nameflag = False

                        if name != '' and nameflag == False:
                            self.name_list.append(name)
                            result += '出席者,' + name + '\n'
                            name = ''

            if len(self.doc_text) > 0:
                text = ''
                for line in self.doc_text:
                    text += line + '\n'
                lines = text.splitlines()
                self.docu_list = []
                j = 0
                for line in lines:
                    if line != '':
                        # if line.count('資料') > 0 or line.count('議案')>0:
                        # if line[0:2] == '資料':
                        # t = line.replace('資料', '')
                        # if t[0:1].isdecimal():
                        #     t = t[1:]
                        self.docu_list.append(line)
                        result += '資料,' + line + '\n'

            # self.ocr_text = []
            # if ocr != '':
            #     ocr = ocr.splitlines()
            #     a = ''
            #     for line in ocr:
            #         if line[0:5] != '=====':
            #             a += line + '\n'
            #         else:
            #             if a != '':
            #                 self.ocr_text.append(a)
            #                 a = ''
            #     if a != '':
            #         self.ocr_text.append(a)
            #
            #     n = len(self.ocr_text)
            #     if n > 0:
            #
            #         token_filters = []
            #         char_filters = []
            #         tokenizer = Tokenizer(self.user_dic, udic_enc="utf8")
            #         analyzer = Analyzer(char_filters, tokenizer, token_filters)
            #         # result = '項目,データ\n'
            #         result = ''
            #         t2 = ''
            #         for i in range(n):
            #
            #             if i == 0:
            #                 text = self.ocr_text[i]
            #                 lines = text.splitlines()
            #                 j=0
            #                 for line in lines:
            #                     if line != '':
            #                         if j == 0:
            #                             self.title = line
            #                             self.kind = 'その他'
            #                             for cat in self.caregory:
            #                                 if self.title.count(cat):
            #                                     self.kind = cat
            #                                     break
            #                             result += '分類,' + self.kind + '\n'
            #                             result += 'タイトル,' + self.title + '\n'
            #                         else:
            #                             day_list = self.day_find(line)
            #                             if len(day_list) > 0:
            #                                 self.day = year_convart(day_list[0])
            #                                 result += '作成日,' + self.day + '\n'
            #                     j += 1
            #
            #             elif i == 1:
            #                 text = self.ocr_text[i]
            #                 self.name_list = []
            #                 if text != '':
            #                     nameflag = False
            #                     name = ''
            #                     for token in analyzer.analyze(text):
            #                         if token.base_form != '\n':
            #                             t1 = str(token).replace('\t', ',')
            #                             t2 = t1.split(',')
            #                             if nameflag != True:
            #                                 if t2[4]=='姓':
            #                                     name = t2[0]
            #                                     nameflag = True
            #                             else:
            #                                 if t2[4] == '名' or t2[3]=='役職':
            #                                     name += t2[0]
            #                                 nameflag = False
            #
            #                         if name != '' and nameflag == False:
            #                             self.name_list.append(name)
            #                             result += '出席者,' + name + '\n'
            #                             name = ''
            #             elif i == 2:
            #                 text = self.ocr_text[i]
            #                 lines = text.splitlines()
            #                 self.docu_list = []
            #                 j = 0
            #                 for line in lines:
            #                     if line != '':
            #                         if line.count('配付資料') == 0:
            #                             if line.count('資料')>0:
            #                                 t = line.replace('資料', '')
            #                                 if t[0:1].isdecimal():
            #                                     t = t[1:]
            #                                 self.docu_list.append(t)
            #                                 result += '資料,' + t + '\n'

            for pdf in self.pdf_list:
                result += 'pdf,' + pdf + '\n'

            self.menu_bar.Enable(ID_SAVE, True)
            self.result_save_button.Enabled = True

        else:
            result = ''

        return result

    # =======================[ テキストから日付を見つける ]=========================================
    def day_find(self, content):
        # import re
        pattern = ['\d{4}年\d+月\d+日',
                   '昭和\d+年\d+月\d+日', '昭和元年\d+月\d+日',
                   '平成\d+年\d+月\d+日', '平成元年\d+月\d+日',
                   '令和\d+年\d+月\d+日', '令和元年\d+月\d+日',
                   'H\.\d+\.\d+\.\d+'
                   ]
        day_list = []
        for p1 in pattern:
            search_result = re.findall(p1, content, re.S)
            if len(search_result) > 0:
                for d1 in search_result:
                    day_list.append(d1)

        return list(set(day_list))

    # =======================[ テキストから文書を見つける ]=========================================
    def doc_find(self, content, part):
        # import re
        doc_list = []
        if content != '' and part != '':
            pattern = '\D+' + part
            content2 = content.splitlines()
            for c1 in content2:
                c2 = c1.split()
                if len(c2) > 3:
                    # if c2[3] == '名詞-固有名詞-一般':
                    if c2[1] == '名詞' and c2[2] == '固有名詞' and c2[3] == '一般':
                        search_result = re.findall(pattern, c2[0], re.S)
                        if len(search_result) > 0:
                            for d1 in search_result:
                                doc_list.append(d1)

        return set(doc_list)

    # =======================[ テキストから部署を見つける ]=========================================
    def group_find(self, content, part):
        # import re
        group_list = []
        if content != '' and part != '':
            pattern = '\D+' + part
            content2 = content.splitlines()
            for c1 in content2:
                c2 = c1.split()
                if len(c2) > 3:
                    if c2[1] == '名詞' and c2[2] == '固有名詞' and c2[3] == '組織':
                        # if c2[3] == '名詞-固有名詞-組織':
                        search_result = re.findall(pattern, c2[0], re.S)
                        if len(search_result) > 0:
                            for d1 in search_result:
                                group_list.append(d1)

        return set(group_list)

    # =======================[ テキストから固有名詞を見つける ]=========================================
    def name_find(self, content):
        # import re
        name_list = []
        if content != '':
            content2 = content.splitlines()
            for c1 in content2:
                c2 = c1.split()
                if len(c2) > 3:
                    if c2[1] == '名詞' and c2[2] == '固有名詞' and c2[3] == '人名' and c2[4] == '一般':
                        # if c2[3] == '名詞-固有名詞-人名-一般':
                        name_list.append(c2[0])

        return set(name_list)  # 重複データを削除


if __name__ == '__main__':
    app = wx.App()
    fx = FRAME_WIDTH
    fy = FRAME_HEIGHT
    s1 = wx.Size(fx, fy)
    # frame = MainFrame(None, wx.ID_ANY, u'PDF読込プログラム', size=s1)
    frame = MainFrame(None, wx.ID_ANY, u'手書きPDF読込プログラム', size=s1,
                      style=wx.STATIC_BORDER | wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.CLIP_CHILDREN | wx.MINIMIZE_BOX)
    # frame = MainFrame(None, wx.ID_ANY, u'PDF読込プログラム', size=s1 ,style = wx.STATIC_BORDER)

    frame.Show()
    app.MainLoop()