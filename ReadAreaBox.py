# -*- coding: utf-8 -*-
'''

プログラム名：ReadAreaBox.py

画像の中から読み取り範囲をマウスで設定するクラス

バージョン：1.0

python 3.7.1

作成：2020/3 完山

カーソルの形
wx.StockCursor
https://wxpython.org/Phoenix/docs/html/wx.StockCursor.enumeration.html
StockCursor列挙体は以下の値を提供します。

説明    値
wx.CURSOR_NONE
wx.CURSOR_ARROW    標準の矢印カーソル。
wx.CURSOR_RIGHT_ARROW    右向きの標準矢印カーソル。
wx.CURSOR_BULLSEYE    ブルズアイカーソル。
wx.CURSOR_CHAR    長方形の文字カーソル。
wx.CURSOR_CROSS    十字カーソル。
wx.CURSOR_HAND    ハンドカーソル
wx.CURSOR_IBEAM    Iビームカーソル（垂直線）。
wx.CURSOR_LEFT_BUTTON    左ボタンが押された状態のマウスを表します。
wx.CURSOR_MAGNIFIER    拡大鏡アイコン。
wx.CURSOR_MIDDLE_BUTTON    中央のボタンが押された状態のマウスを表します。
wx.CURSOR_NO_ENTRY    無記入記号カーソル。
wx.CURSOR_PAINT_BRUSH    絵筆カーソル。
wx.CURSOR_PENCIL    鉛筆のカーソル
wx.CURSOR_POINT_LEFT    左向きのカーソル。
wx.CURSOR_POINT_RIGHT    右向きのカーソル。
wx.CURSOR_QUESTION_ARROW    矢印と疑問符
wx.CURSOR_RIGHT_BUTTON    右ボタンが押された状態のマウスを表します。
wx.CURSOR_SIZENESW    NE-SW指すサイズ変更カーソル。
wx.CURSOR_SIZENS    NS指すサイズ変更カーソル。
wx.CURSOR_SIZENWSE    NW-SE指すサイズ変更カーソル。
wx.CURSOR_SIZEWE    WE指すサイズ変更カーソル。
wx.CURSOR_SIZING    一般的なサイズ変更カーソル。
wx.CURSOR_SPRAYCAN    スプレースキャンカーソル。
wx.CURSOR_WAIT    待機カーソル
wx.CURSOR_WATCH    ウォッチカーソル
wx.CURSOR_BLANK    透明カーソル
wx.CURSOR_DEFAULT    標準X11カーソル（wxGTKのみ）
wx.CURSOR_COPY_ARROW    MacOSテーマプラス矢印（Macのみ）。
wx.CURSOR_ARROWWAIT    標準の矢印付きの待機カ

'''


import wx

class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        # wx.Frame.__init__(self, *args, **kwargs)
        super().__init__(*args, **kwargs)
        self.panel = wx.Panel(self, size = self.GetSize(), pos=(0,0))

        image = wx.Image('理事会議事録カラー.jpg')
        self.panel2 = ImagePanel(self.panel, size=self.GetSize() - (40, 60), pos=wx.Point(20, 40), image=image)

        self.pos_button = wx.Button(self.panel, wx.ID_ANY, 'ポイント', pos=(50, 0), size=(100, 40))
        self.Bind(wx.EVT_BUTTON, self.pos_button_handler, self.pos_button)  # イベントを設定

        self.Area1 = ReadAreaBox(self.panel2, pos1=(5, 5),
                                 pos2=(95, 95),
                                 width=3, color='green')
        # self.Area2 = ReadAreaBox(self.panel2, pos1=(5, 55),
        #                          pos2=(95, 95),
        #                          width=3, color='red')

    def pos_button_handler(self, evt):
        print(self.Area1.pos1, self.Area1.pos2)

class ImagePanel(wx.Panel):
    '''
    イメージを貼り付けるパネル　xw.Panelを継承
    '''
    def __init__(self, parent, pos=(0,0), size=(100,100), image=None):
        super().__init__(parent, size=size, pos=pos)
        # imageがあれば、ビットマップに変換してパネルに貼り付ける。無ければ、普通のパネルと同じ。
        if image != None:
            image = image.Scale(size[0], size[1], wx.IMAGE_QUALITY_HIGH)
            self.bitmap = image.ConvertToBitmap()
            self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, event=None):
        # ビットマップの描画をOnPaint（再描画時）割り込み処理の時に行う。
        deviceContext = wx.PaintDC(self)
        deviceContext.Clear()
        deviceContext.DrawBitmap(self.bitmap, 0, 0, True)


class MiniBox:
    '''
    画像の中から読み取り範囲をマウスで設定するクラス
    version 1.0
    2020/03/05
    coded by kanyama
    '''

    def __init__(self, panel, pos1=(5, 5), pos2=(95,95), width=1, kind=0, num=0):
        '''
        :param panel:   範囲を設定するパネル(wx.Panel)
        :param pos1:    左上側のポイント座標（パネルの寸法に対するパーセントで設定する）
        :param pos2:    右下側のポイント座標（パネルの寸法に対するパーセントで設定する）
        :param width:   線の太さ（単位：ポイント、3ポイントがデフォルト）
        :param color:   線の色（例：'green' , 'red' , 'yellow')
        '''
        #
        #  pos1 p1-----p2
        #       |       |
        #       |       |
        #       p3-----p4 pos2
        #

        # 送られてきたパネルをクラス共有変数に代入
        self.panel = panel
        self._kind = kind
        if kind == 0:
            self.color = 'green'
        elif kind == 1:
            self.color = 'cyan'
        elif kind == 2:
            self.color = 'pink'
        elif kind == 3:
            self.color = 'yellow'
        else:
            self.color = 'red'
        self.width = width
        self.num = num
        self.pos1 = pos1
        self.pos2 = pos2

        self.boxDraw(panel)

    def boxDraw(self, panel):
        self.panel = panel
        #
        # 四隅の座標（パーセント）をポイント単位に変換
        self.p1 = (int(self.panel.Size[0] * self.pos1[0] / 100), int(self.panel.Size[1] * self.pos1[1] / 100))
        self.p2 = (int(self.panel.Size[0] * self.pos2[0] / 100), int(self.panel.Size[1] * self.pos1[1] / 100))
        self.p3 = (int(self.panel.Size[0] * self.pos1[0] / 100), int(self.panel.Size[1] * self.pos2[1] / 100))
        self.p4 = (int(self.panel.Size[0] * self.pos2[0] / 100), int(self.panel.Size[1] * self.pos2[1] / 100))

        # 左側垂直線
        self.v_line1 = wx.Panel(self.panel, size=(self.width, (self.p3[1] - self.p1[1])), pos=self.p1)
        self.v_line1.SetBackgroundColour(self.color)
        # self.x_max = self.panel.Size[0] - self.width
        # self.OnMouseSetting(self.v_line1, mouse_flag=wx.CURSOR_SIZEWE, func=self.v_line1_move)

        # 右側垂直線
        self.v_line2 = wx.Panel(self.panel, size=(self.width, (self.p4[1] - self.p2[1]) + self.width), pos=self.p2)
        self.v_line2.SetBackgroundColour(self.color)
        # self.x_max = self.panel.Size[0] - self.width
        # self.OnMouseSetting(self.v_line2, mouse_flag=wx.CURSOR_SIZEWE, func=self.v_line2_move)

        # 上側水平線
        self.h_line1 = wx.Panel(self.panel, size=((self.p2[0] - self.p1[0]), self.width), pos=self.p1)
        self.h_line1.SetBackgroundColour(self.color)
        # self.y_max = self.panel.Size[1] - self.width
        # self.OnMouseSetting(self.h_line1, mouse_flag=wx.CURSOR_SIZENS, func=self.h_line1_move)

        # 下側水平線
        self.h_line2 = wx.Panel(self.panel, size=((self.p4[0] - self.p3[0]) + self.width, self.width), pos=self.p3)
        self.h_line2.SetBackgroundColour(self.color)
        # self.y_max = self.panel.Size[1] - self.width
        # self.OnMouseSetting(self.h_line2, mouse_flag=wx.CURSOR_SIZENS, func=self.h_line2_move)

class ReadAreaBox:
    '''
    画像の中から読み取り範囲をマウスで設定するクラス
    version 1.0
    2020/03/05
    coded by kanyama
    '''

    def __init__(self, panel, pos1=(5, 5), pos2=(95,95), width=3, kind=0, num=0):
        '''
        :param panel:   範囲を設定するパネル(wx.Panel)
        :param pos1:    左上側のポイント座標（パネルの寸法に対するパーセントで設定する）
        :param pos2:    右下側のポイント座標（パネルの寸法に対するパーセントで設定する）
        :param width:   線の太さ（単位：ポイント、3ポイントがデフォルト）
        :param color:   線の色（例：'green' , 'red' , 'yellow')
        '''
        #
        #  pos1 p1-----p2
        #       |       |
        #       |       |
        #       p3-----p4 pos2
        #

        # 送られてきたパネルをクラス共有変数に代入
        self.panel = panel
        self._kind = kind
        if kind == 0:
            self.color = 'green'
        elif kind == 1:
            self.color = 'cyan'
        elif kind == 2:
            self.color = 'pink'
        elif kind == 3:
            self.color = 'yellow'
        else:
            self.color = 'red'
        self.width = width
        self.num = num
        self.pos1 = pos1
        self.pos2 = pos2
        self._flag = False

        self.boxDraw(panel)

    def boxDraw(self, panel):
        self.panel = panel
        #
        # 四隅の座標（パーセント）をポイント単位に変換
        self.p1 = (int(self.panel.Size[0] * self.pos1[0] / 100), int(self.panel.Size[1] * self.pos1[1] / 100))
        self.p2 = (int(self.panel.Size[0] * self.pos2[0] / 100), int(self.panel.Size[1] * self.pos1[1] / 100))
        self.p3 = (int(self.panel.Size[0] * self.pos1[0] / 100), int(self.panel.Size[1] * self.pos2[1] / 100))
        self.p4 = (int(self.panel.Size[0] * self.pos2[0] / 100), int(self.panel.Size[1] * self.pos2[1] / 100))

        # # 送られてきた線の幅をクラス共有変数に代入
        # self.width = width

        # ハンドル 全体を移動させるハンドル
        self.handle_w = 24 # self.width * 8
        self.handle_h = 9  # self.width * 3
        self.handle = wx.Panel(self.panel, size=(self.handle_w, self.handle_h),
                               pos=((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))
        self.handle.SetBackgroundColour(self.color)
        self.w_max = self.panel.Size[0] - self.width
        self.h_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.handle, mouse_flag=wx.CURSOR_HAND, func=self.handle_move)
        # self.OnMouseSetting(self.handle, mouse_flag=wx.EVT_RIGHT_UP, func=self.OnRightUp)
        font1 = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.handleText = wx.StaticText(self.handle, wx.ID_ANY,
                                       '{}'.format(self.num), pos=(self.handle_w*1/3, 0))
        self.handleText.SetFont(font1)

        # 左側垂直線
        self.v_line1 = wx.Panel(self.panel, size=(self.width, (self.p3[1] - self.p1[1])), pos=self.p1)
        self.v_line1.SetBackgroundColour(self.color)
        self.x_max = self.panel.Size[0] - self.width
        self.OnMouseSetting(self.v_line1, mouse_flag=wx.CURSOR_SIZEWE, func=self.v_line1_move)

        # 右側垂直線
        self.v_line2 = wx.Panel(self.panel, size=(self.width, (self.p4[1] - self.p2[1]) + self.width), pos=self.p2)
        self.v_line2.SetBackgroundColour(self.color)
        self.x_max = self.panel.Size[0] - self.width
        self.OnMouseSetting(self.v_line2, mouse_flag=wx.CURSOR_SIZEWE, func=self.v_line2_move)

        # 上側水平線
        self.h_line1 = wx.Panel(self.panel, size=((self.p2[0] - self.p1[0]), self.width), pos=self.p1)
        self.h_line1.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.h_line1, mouse_flag=wx.CURSOR_SIZENS, func=self.h_line1_move)

        # 下側水平線
        self.h_line2 = wx.Panel(self.panel, size=((self.p4[0] - self.p3[0]) + self.width, self.width), pos=self.p3)
        self.h_line2.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.h_line2, mouse_flag=wx.CURSOR_SIZENS, func=self.h_line2_move)

        # Point No1
        self.Point1 = wx.Panel(self.panel, size=(self.width * 3, self.width * 3), pos=(self.p1[0] - self.width, self.p1[1] - self.width))
        self.Point1.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.Point1, mouse_flag=wx.CURSOR_SIZENWSE, func=self.point1_move)

        # Point No2
        self.Point2 = wx.Panel(self.panel, size=(self.width * 3, self.width * 3), pos=(self.p2[0] - self.width, self.p2[1] - self.width))
        self.Point2.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.Point2, mouse_flag=wx.CURSOR_SIZENESW, func=self.point2_move)

        # Point No3
        self.Point3 = wx.Panel(self.panel, size=(self.width * 3, self.width * 3), pos=(self.p3[0] - self.width, self.p3[1] - self.width))
        self.Point3.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.Point3, mouse_flag=wx.CURSOR_SIZENESW, func=self.point3_move)

        # Point No4
        self.Point4 = wx.Panel(self.panel, size=(self.width * 3, self.width * 3), pos=(self.p4[0] - self.width, self.p4[1] - self.width))
        self.Point4.SetBackgroundColour(self.color)
        self.y_max = self.panel.Size[1] - self.width
        self.OnMouseSetting(self.Point4, mouse_flag=wx.CURSOR_SIZENWSE, func=self.point4_move)

    #　ハンドル　===================================================

    def handle_move(self, mousePos, prevMousePos):
        wndPos = self.handle.GetPosition()
        pp1 = self.Point1.GetPosition()
        pp2 = self.Point2.GetPosition()
        pp3 = self.Point3.GetPosition()
        pp4 = self.Point4.GetPosition()
        vv1 = self.v_line1.GetPosition()
        vv2 = self.v_line2.GetPosition()
        hh1 = self.h_line1.GetPosition()
        hh2 = self.h_line2.GetPosition()

        xx1 = prevMousePos[0] - mousePos[0]
        yy1 = prevMousePos[1] - mousePos[1]
        xmin = self.p1[0] - self.width
        xmax = self.p2[0] + self.width
        ymin = self.p1[1] - self.width * 3
        ymax = self.p3[1] + self.width
        x1 = xmin - xx1
        x2 = xmax - xx1
        y1 = ymin - yy1
        y2 = ymax - yy1
        if x1 >= 0 and x2 <= self.w_max and y1 >= 0 and y2 <= self.h_max:
            self.p1 = (self.p1[0] - xx1, self.p1[1] - yy1)
            self.p2 = (self.p2[0] - xx1, self.p2[1] - yy1)
            self.p3 = (self.p3[0] - xx1, self.p3[1] - yy1)
            self.p4 = (self.p4[0] - xx1, self.p4[1] - yy1)
            self.handle.Move(wndPos - (prevMousePos - mousePos))
            self.Point1.Move(pp1 - (prevMousePos - mousePos))
            self.Point2.Move(pp2 - (prevMousePos - mousePos))
            self.Point3.Move(pp3 - (prevMousePos - mousePos))
            self.Point4.Move(pp4 - (prevMousePos - mousePos))
            self.v_line1.Move(vv1 - (prevMousePos - mousePos))
            self.v_line2.Move(vv2 - (prevMousePos - mousePos))
            self.h_line1.Move(hh1 - (prevMousePos - mousePos))
            self.h_line2.Move(hh2 - (prevMousePos - mousePos))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    #　垂直線　No.1　===================================================

    def v_line1_move(self, mousePos, prevMousePos):
        wndPos = self.v_line1.GetPosition()
        pp1 = self.Point1.GetPosition()
        pp3 = self.Point3.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        x_min = self.width
        x_max = self.p2[0] - self.handle_w
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        if x1 >= x_min and x1 <= x_max :
            self.p1 = (x1, self.p1[1])
            self.p3 = (x1, self.p3[1])
            self.v_line1.Move(self.p1)
            self.h_line1.SetSize((self.p2[0] - self.p1[0], self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.Point1.Move((pp1[0] - xx1, pp1[1]))
            self.Point3.Move((pp3[0] - xx1, pp3[1]))

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    #　垂直線　No.2　===================================================

    def v_line2_move(self, mousePos, prevMousePos):
        wndPos = self.v_line2.GetPosition()
        pp2 = self.Point2.GetPosition()
        pp4 = self.Point4.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        x_min = self.p1[0] + self.handle_w
        x_max = self.w_max - self.width
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        if x1 >= x_min and x1 <= x_max :
            self.p2 = (x1, self.p2[1])
            self.p4 = (x1, self.p4[1])
            self.v_line2.Move(self.p2)
            self.h_line1.SetSize((self.p2[0] - self.p1[0], self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.Point2.Move((pp2[0] - xx1, pp2[1]))
            self.Point4.Move((pp4[0] - xx1, pp4[1]))

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    #　水平線　No.1　===================================================

    def h_line1_move(self, mousePos, prevMousePos):
        wndPos = self.h_line1.GetPosition()
        pp1 = self.Point1.GetPosition()
        pp2 = self.Point2.GetPosition()
        yy1 = prevMousePos[1] - mousePos[1]
        y_min = self.handle_h
        y_max = self.p3[1] - self.width
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if y1 >= y_min and y1 <= y_max :
            self.p1 = (self.p1[0], y1)
            self.p2 = (self.p2[0], y1)
            self.h_line1.Move(self.p1)
            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1] + self.width))
            self.v_line2.Move(self.p2)

            self.Point1.Move((pp1[0], pp1[1] - yy1))
            self.Point2.Move((pp2[0], pp2[1] - yy1))

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    #　水平線　No.2　===================================================

    def h_line2_move(self, mousePos, prevMousePos):
        wndPos = self.h_line2.GetPosition()
        pp3 = self.Point3.GetPosition()
        pp4 = self.Point4.GetPosition()
        yy1 = prevMousePos[1] - mousePos[1]
        y_min = self.p1[1] + self.width
        y_max = self.h_max - self.width
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if y1 >= y_min and y1 <= y_max:
            self.p3 = (self.p3[0], y1)
            self.p4 = (self.p4[0], y1)
            self.h_line2.Move(self.p3)
            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1] + self.width))
            self.v_line2.Move(self.p2)

            self.Point3.Move((pp3[0], pp3[1] - yy1))
            self.Point4.Move((pp4[0], pp4[1] - yy1))

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    # Point No.1 =============================================

    def point1_move(self, mousePos, prevMousePos):
        wndPos = self.Point1.GetPosition()
        pp2 = self.Point2.GetPosition()
        pp3 = self.Point3.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        yy1 = prevMousePos[1] - mousePos[1]
        x_min = 0
        x_max = self.p2[0] - self.handle_w
        y_min = self.handle_h
        y_max = self.p3[1] - self.width * 2
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if x1 >= x_min and x1 <= x_max and y1 >= y_min and y1 <= y_max:
            self.p1 = (self.p1[0] - xx1, self.p1[1] - yy1)
            self.p2 = (self.p2[0], self.p2[1] - yy1)
            self.p3 = (self.p3[0] - xx1, self.p3[1])
            self.Point1.Move(wndPos - (prevMousePos - mousePos))
            self.Point2.Move((pp2[0], pp2[1] - yy1))
            self.Point3.Move((pp3[0] - xx1, pp3[1]))

            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1]))
            self.v_line2.Move(self.p2)
            self.h_line1.SetSize((self.p2[0] - self.p1[0] + self.width, self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    # Point No.2 =============================================

    def point2_move(self, mousePos, prevMousePos):
        wndPos = self.Point2.GetPosition()
        pp1 = self.Point1.GetPosition()
        pp4 = self.Point4.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        yy1 = prevMousePos[1] - mousePos[1]
        x_min = self.p1[0] + self.handle_w
        x_max = self.w_max
        y_min = self.handle_h
        y_max = self.p4[1] - self.width * 2
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if x1 >= x_min and x1 <= x_max and y1 >= y_min and y1 <= y_max:
            self.p2 = (self.p2[0] - xx1, self.p2[1] - yy1)
            self.p1 = (self.p1[0], self.p1[1] - yy1)
            self.p4 = (self.p4[0] - xx1, self.p4[1])
            self.Point2.Move(wndPos - (prevMousePos - mousePos))
            self.Point1.Move((pp1[0], pp1[1] - yy1))
            self.Point4.Move((pp4[0] - xx1, pp4[1]))

            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1]))
            self.v_line2.Move(self.p2)
            self.h_line1.SetSize((self.p2[0] - self.p1[0] + self.width, self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    # Point No.3 =============================================

    def point3_move(self, mousePos, prevMousePos):
        wndPos = self.Point3.GetPosition()
        pp1 = self.Point1.GetPosition()
        pp4 = self.Point4.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        yy1 = prevMousePos[1] - mousePos[1]
        x_min = 0
        x_max = self.p4[0] - self.handle_w
        y_min = self.p1[1] + self.width
        y_max = self.h_max - self.width
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if x1 >= x_min and x1 <= x_max and y1 >= y_min and y1 <= y_max:
            self.p3 = (self.p3[0] - xx1, self.p3[1] - yy1)
            self.p1 = (self.p1[0] - xx1, self.p1[1])
            self.p4 = (self.p4[0], self.p4[1] - yy1)
            self.Point3.Move(wndPos - (prevMousePos - mousePos))
            self.Point1.Move((pp1[0] - xx1, pp1[1]))
            self.Point4.Move((pp4[0], pp4[1] - yy1))

            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1]))
            self.v_line2.Move(self.p2)
            self.h_line1.SetSize((self.p2[0] - self.p1[0] + self.width, self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    # Point No.4 =============================================

    def point4_move(self, mousePos, prevMousePos):
        wndPos = self.Point4.GetPosition()
        pp2 = self.Point2.GetPosition()
        pp3 = self.Point3.GetPosition()
        xx1 = prevMousePos[0] - mousePos[0]
        yy1 = prevMousePos[1] - mousePos[1]
        x_min = self.p3[0] + self.handle_w
        x_max = self.w_max - self.width * 2
        y_min = self.p2[1] + self.width * 2
        y_max = self.h_max - self.width * 2
        x1 = wndPos[0] - (prevMousePos[0] - mousePos[0])
        y1 = wndPos[1] - (prevMousePos[1] - mousePos[1])
        if x1 >= x_min and x1 <= x_max and y1 >= y_min and y1 <= y_max:
            self.p4 = (self.p4[0] - xx1, self.p4[1] - yy1)
            self.p2 = (self.p2[0] - xx1, self.p2[1])
            self.p3 = (self.p3[0], self.p3[1] - yy1)
            self.Point4.Move(wndPos - (prevMousePos - mousePos))
            self.Point2.Move((pp2[0] - xx1, pp2[1]))
            self.Point3.Move((pp3[0], pp3[1] - yy1))

            self.v_line1.SetSize((self.width, self.p3[1] - self.p1[1]))
            self.v_line1.Move(self.p1)
            self.v_line2.SetSize((self.width, self.p4[1] - self.p2[1]))
            self.v_line2.Move(self.p2)
            self.h_line1.SetSize((self.p2[0] - self.p1[0] + self.width, self.width))
            self.h_line1.Move(self.p1)
            self.h_line2.SetSize((self.p4[0] - self.p3[0] + self.width, self.width))
            self.h_line2.Move(self.p3)

            self.handle.Move(((self.p1[0]+self.p2[0])/2 - self.handle_w/2, self.p1[1] - self.handle_h))

            self.pos1 = (self.p1[0] * 100 / self.panel.Size[0], self.p1[1] * 100 / self.panel.Size[1])
            self.pos2 = (self.p4[0] * 100 / self.panel.Size[0], self.p4[1] * 100 / self.panel.Size[1])

        self._flag = True

    # ポイントのプロパティー
    @property
    def possion1(self):
        return self.pos1
        # return (self.p1[0] / self.panel.Size[0] * 100, self.p1[1] / self.panel.Size[1] * 100)

    @property
    def possion2(self):
        return self.pos2
        # return (self.p4[0] / self.panel.Size[0] * 100, self.p4[1] / self.panel.Size[1] * 100)

    # 種類のプロパティー
    @property
    def kind(self):
        return self._kind

    # 変更のプロパティー
    @property
    def flag(self):
        return self._flag

    @flag.setter
    def flag(self, v):
        self._flag = v

    # boxに対してマウスの割り込み処理の設定を行うクラス
    class OnMouseSetting:
        def __init__(self, box, mouse_flag=wx.CURSOR_ARROW, func=None ):
            self.isDragStarted = False
            self.box=box
            self.mousu_flag = mouse_flag
            self.func = func
            self.box.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
            self.box.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
            self.box.Bind(wx.EVT_MOTION, self.OnMouseMove)
            self.box.Bind(wx.EVT_ENTER_WINDOW, self.OnActivate)
            self.box.Bind(wx.EVT_LEAVE_WINDOW, self.OffActivate)

        def OnLeftDown(self, evt):
            self.isDragStarted = True
            self.box.CaptureMouse()
            self.prevMousePos = evt.GetPosition()
            evt.Skip()

        def OnLeftUp(self, evt):
            self.isDragStarted = False
            if self.box.HasCapture():
                self.box.ReleaseMouse()
            evt.Skip()

        def OnMouseMove(self, evt):
            if evt.Dragging() and evt.LeftIsDown() and self.isDragStarted:
                self.mousePos = evt.GetPosition()

                self.func(self.mousePos, self.prevMousePos)

            evt.Skip()

        def OnActivate(self, evt):
            # カーソルの形が待つのになる
            self.box.SetCursor(wx.StockCursor(self.mousu_flag))

        def OffActivate(self, evt):
            # カーソルの形が待つのになる
            self.box.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))


if __name__ == '__main__':
    app = wx.App()
    frame1 = MainFrame(None, -1, 'Title', size = (500, 700))
    frame1.Show()
    app.MainLoop()