import cv2
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('WXAgg')
import numpy as np
import os
# import plaidml.keras
# plaidml.keras.install_backend()
import keras
from keras.models import load_model
from scipy import signal
from jiscode import jiscode
import pickle
from jFont import *

# openCVで日本語ファイル名を読み込むことができないバグ対策のための関数
#   cv.imread(f) の代わりに imread(f) を使用すること。
#
def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
    try:
        n = np.fromfile(filename, dtype)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        print(e)
        return None

#   cv.imwrite(f) の代わりに imwrite(f) を使用すること。
def imwrite(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

class kanji_find:
    def __init__(self):
        self.model_filename = 'etl9b_model15-1_32_2048_100_02.h5'
        # self.model_filename = 'etl9b_model12-1_32_2048_150_01.h5'
        # self.model_filename = 'etl9b_model8-1_32_2048_150_01.h5'
        # self.model_filename = 'etl9b_model7-2_32_2048_150_01.h5'
        # self.model_filename = 'etl9b_model3-2_32_2048_120_01.h5'
        # self.model_filename = 'etl9b_model13_32_2048_100_01.h5'

        self.model = load_model(self.model_filename)
        self.jis_code_file = 'ETL9B_KANA_JIS_CODE.picle'
        (self.code_mat) = pickle.load(open(self.jis_code_file, "rb"))

    def kanji_text(self, _image_main = None, PLOT_FLAG = False):
        image_main = np.array(_image_main)
        image_copy = np.copy(image_main)  # 画像の複製を作成

        image_gray = cv2.cvtColor(image_main, cv2.COLOR_BGR2GRAY)  # 画像をカラーからグレイスケールに変換
        threshold1 = 210
        # 二値化(閾値220を超えた画素を255にする（白黒画像にする）。
        ret, image_monotone = cv2.threshold(image_gray, threshold1, 255, cv2.THRESH_BINARY)  # THRESH_BINARY_INV
        h0, w0 = image_monotone.shape[:2]

        # 幅ddポイントの白線を四周を画く（不要な線を消すため）
        dd = 10
        z1 = np.full((dd, w0), 255)  # 幅dd、長さw0の横線
        image_monotone[0:dd, :] = z1  # 上端
        image_monotone[h0 - dd:h0, :] = z1  # 下端
        z2 = np.full((h0, dd), 255)  # 幅dd、長さw0の縦線
        image_monotone[:, 0:dd] = z2  # 左端
        image_monotone[:, w0 - dd:w0] = z2  # 右端

        # 次数gauss_nのガウスフィルターによる画像のぼかし処理
        gauss_n = 101
        image_monotone2 = cv2.GaussianBlur(image_monotone, ksize=(gauss_n, gauss_n), sigmaX=0)

        # 白黒画像の反転処理
        image_inv = cv2.bitwise_not(image_monotone2)

        # 画像の横線の数値の合計を計算
        ysum = np.zeros(h0)
        for i in range(h0):
            ysum[i] = np.sum(image_inv[i, :])

        # 次数numで移動平均計算
        num = 30  # 移動平均の個数
        b = np.ones(num) / num  # ウインドウ
        ysum = np.convolve(ysum, b, mode='same')  # 移動平均
        ysum = ysum / np.max(ysum) * w0 / 2  # 移動平均の最大値が画像の幅の１／２になるよう調整（グラフを見やすくするため）

        if PLOT_FLAG:  # 移動平均値の作図
            plt.imshow(image_monotone)
            plt.plot(ysum, np.arange(h0))

        # ピーク値のインデックスを取得
        maxid = signal.argrelmax(ysum, order=num)[0]  # 最大値
        minid = signal.argrelmin(ysum, order=num)[0]  # 最小値

        if len(maxid) > 0:
            x1 = []
            y1 = []
            for id in maxid:
                x1.append(ysum[id])
                y1.append(id)

            if PLOT_FLAG:
                plt.plot(x1, y1, marker='o', linestyle='None')

            if len(minid) > 0:
                x2 = []
                y2 = []
                for id in minid:
                    x2.append(ysum[id])
                    y2.append(id)
                if PLOT_FLAG:
                    plt.plot(x2, y2, marker='o', linestyle='None')
            else:
                pass

            lh1 = []
            lh2 = []
            hh = 0
            n = len(maxid)
            for i in range(n - 1):
                lh1.append(hh)
                y = (maxid[i] + maxid[i + 1]) // 2
                if PLOT_FLAG:
                    plt.plot([0, w0], [y, y])
                lh2.append(y)
                hh = y + 1
            lh1.append(hh)
            lh2.append(h0)

            esy = int(0.01 * np.max(ysum))
            for i in range(len(ysum)):
                if ysum[i] > esy:
                    lh1[0] = i - 5
                    if lh1[0] < 0:
                        lh1[0] = 0
                    break

            for i in range(maxid[n - 1], len(ysum)):
                if ysum[i] < esy:
                    lh2[n - 1] = i + 5
                    if lh2[n - 1] > h0:
                        lh2[n - 1] = h0
                    break

        if PLOT_FLAG:
            plt.show()

        img2 = []
        img4 = []
        hh2 = []
        for i in range(n):
            img1 = image_monotone[lh1[i]:lh2[i], :]  # 行毎のイメージの切り出し
            hh2.append(lh2[i] - lh1[i] + 1)  # 行毎の高さの保存

            inv1 = cv2.bitwise_not(img1)
            inv2 = np.copy(inv1)

            xsum = np.zeros(w0)
            for j in range(w0):
                xsum[j] = np.sum(inv1[:, j])
            h = lh2[i] - lh1[i]
            num = 20  # 移動平均の個数
            # b = np.ones(num) / num
            b = signal.parzen(num)
            xsum = np.convolve(xsum, b, mode='same')  # 移動平均
            xsum = xsum / np.max(xsum) * hh2[i]

            xmaxid = signal.argrelmax(xsum, order=40)[0]  # 最大値
            xminid = signal.argrelmin(xsum, order=5)[0]  # 最小値

            if PLOT_FLAG:
                plt.imshow(img1)

                plt.plot(np.arange(w0), xsum)

                if len(xminid) > 0:
                    for s in xminid:
                        plt.plot([s, s], [0, hh2[i]])

                plt.show()

                plt.subplot(2, 1, 1)

            dst = cv2.GaussianBlur(img1, ksize=(gauss_n, gauss_n), sigmaX=0)

            if PLOT_FLAG:
                plt.imshow(dst)

            inv = cv2.bitwise_not(dst)
            h2 = hh2[i]
            # print(h2)
            ysum = np.zeros(h2)
            for j in range(h2):
                ysum[j] = np.sum(inv[:, j])

            num = 10  # 移動平均の個数
            # b = np.ones(num) / num
            b = signal.parzen(num)
            ysum = np.convolve(ysum, b, mode='same')  # 移動平均
            ysum = ysum / np.max(ysum) * w0

            # ピーク値のインデックスを取得
            ymaxid2 = signal.argrelmax(xsum, order=5)[0]  # 最大値

            if PLOT_FLAG:
                if len(ymaxid2) > 0:
                    for s in ymaxid2:
                        plt.plot([0, w0], [s, s])
                        ph = s
                        break

            xsum = np.zeros(w0)
            for j in range(w0):
                xsum[j] = np.sum(inv[:, j])
            num = 50  # 移動平均の個数
            # b = np.ones(num) / num
            b = signal.parzen(num)
            xsum = np.convolve(xsum, b, mode='same')  # 移動平均
            xsum = xsum / np.max(xsum) * hh2[i]

            # ピーク値のインデックスを取得
            xmaxid2 = signal.argrelmax(xsum, order=15)[0]  # 最大値

            xminid2 = signal.argrelmin(xsum, order=30)[0]  # 最小値

            if PLOT_FLAG:
                if len(xmaxid2) > 0:
                    for s in xmaxid2:
                        plt.plot([s, s], [0, hh2[i]])

            if len(xminid2) > 0:
                pos1 = []
                pos2 = []
                pos1.append(0)

                mn = len(xmaxid2)
                for i in range(mn - 1):
                    flag1 = False
                    for s in xminid2:
                        if s > xmaxid2[i] and s < xmaxid2[i + 1]:
                            pos1.append(s)
                            pos2.append(s)
                            flag1 = True
                            break

                    if flag1 == False:
                        s = int((xmaxid2[i] + xmaxid2[i + 1]) / 2)
                        pos1.append(s)
                        pos2.append(s)
                pos2.append(w0)

            else:
                pos1 = []
                pos2 = []
                pos1.append(0)

                mn = len(xmaxid2)
                for i in range(mn - 1):
                    s = int((xmaxid2[i] + xmaxid2[i + 1]) / 2)
                    pos1.append(s)
                    pos2.append(s)
                pos2.append(w0)

            if PLOT_FLAG:
                plt.subplot(2, 1, 2)

            n2 = len(pos1)
            # print(pos1)
            # print(pos2)
            chr_image = []
            for j in range(n2):
                img2 = img1[:, pos1[j]:pos2[j]]
                gray = img2
                gray = cv2.GaussianBlur(gray, (3, 3), 1)
                img2 = cv2.threshold(gray, threshold1, 255, cv2.THRESH_BINARY_INV)[1]

                # 輪郭を抽出 --- (*3)
                cnts = cv2.findContours(img2,
                                        cv2.RETR_LIST,
                                        cv2.CHAIN_APPROX_SIMPLE)[0]
                w_limit = pos2[j] - pos1[j]
                result = []
                result2 = []
                for pt in cnts:
                    x, y, w, h = cv2.boundingRect(pt)
                    # 大きすぎる小さすぎる領域を除去 --- (*5)
                    result2.append([x, y, w, h])
                    if not ((10 < w < h2) and (4 < h < h2)): continue
                    result.append([x, y, w, h])
                # 抽出した輪郭が左側から並ぶようソート --- (*6)
                result = sorted(result, key=lambda x: x[0])

                # print(result)
                # if len(result) == 0:
                #     print(result2)

                if len(result) > 0:
                    xmax = 0
                    xmin = 10000
                    ymax = 0
                    ymin = 10000
                    for x, y, w, h in result:
                        if xmin > x:
                            xmin = x
                        if xmax < x + w:
                            xmax = x + w
                        if ymin > y:
                            ymin = y
                        if ymax < y + h:
                            ymax = y + h

                    ww = xmax - xmin
                    hh = ymax - ymin
                    if ww > hh:
                        ymin = ymin - int((ww - hh) / 2)
                        ymax = ymax + int((ww - hh) / 2)
                    else:
                        xmin = xmin - int((hh - ww) / 2)
                        xmax = xmax + int((hh - ww) / 2)

                    # 検出された範囲を余分に広げる。
                    dd = 3  # 範囲を余分にとるドット数
                    xmax += dd
                    if xmax > w0: xmax = w0
                    xmin -= dd
                    if xmin < 0: xmin = 0
                    ymax += dd
                    if ymax > h2: ymax = h2
                    ymin -= dd
                    if ymin < 0: ymin = 0

                    www = xmax - xmin
                    hhh = ymax - ymin
                    if www / hhh > 1.5:
                        xmin1 = xmin
                        xmax1 = xmin + h2
                        ymin1 = ymin
                        ymax1 = ymax

                        xmin2 = xmax1
                        xmax2 = xmax
                        wwww = int((h2 - (xmax2 - xmin2)) / 2)
                        ymin2 = ymin + wwww
                        ymax2 = ymax - wwww

                        # print('****')
                        # print(xmin1, xmax1, ymin1, ymax1)
                        # print(xmin2, xmax2, ymin2, ymax2)

                        if PLOT_FLAG:
                            # plt.subplot(2, 1, 2)
                            cv2.rectangle(inv1, (xmin1 + pos1[j], ymin1), (xmax1 + pos1[j], ymax1), (255, 255, 255), 2)
                            cv2.rectangle(inv1, (xmin2 + pos1[j], ymin2), (xmax2 + pos1[j], ymax2), (255, 255, 255), 2)

                        chr_image.append(inv2[ymin1:ymax1, xmin1 + pos1[j]:xmax1 + pos1[j]])
                        chr_image.append(inv2[ymin2:ymax2, xmin2 + pos1[j]:xmax2 + pos1[j]])
                    else:

                        # print(xmin, xmax, ymin, ymax)
                        if PLOT_FLAG:
                            # plt.subplot(2, 1, 2)
                            cv2.rectangle(inv1, (xmin + pos1[j], ymin), (xmax + pos1[j], ymax), (255, 255, 255), 2)

                        chr_image.append(inv2[ymin:ymax, xmin + pos1[j]:xmax + pos1[j]])

            if PLOT_FLAG:
                plt.imshow(inv1)
                plt.show()

            img4.append(chr_image)

        if PLOT_FLAG:
            ln = len(img4)

            m = 5
            for im in img4:
                if len(im)>m : m = len(im)
            i = 0
            for im in img4:
                j = 0
                for c in im:
                    j += 1
                    k = m * i + j
                    plt.subplot(ln, m, k)
                    plt.imshow(c)
                    plt.axis('off')

                i += 1

        im_rows = 32  # 画像の縦ピクセルサイズ
        im_cols = 32  # 画像の横ピクセルサイズ
        im_color = 1  # 画像の色空間/グレイスケール
        jis1 = jiscode()

        # self.model = load_model(self.model_filename)
        ch = []

        text = ''
        for im3 in img4:
            im1 = []
            for im in im3:
                im2 = cv2.resize(im, (im_rows, im_cols))
                im1.append(im2)

            im3 = np.array(im1)
            X_test = im3.reshape(-1, im_rows, im_cols, im_color)
            X_test = X_test.astype('float32') / 255

            # self.model = load_model(self.model_filename)

            y1 = self.model.predict(X_test, verbose=1)
            # ch = []
            code = []
            for y in y1:
                # print('max={} , index={}'.format(np.max(y), np.argmax(y)))
                s1 = np.argsort(y)[::-1]
                for i in range(10):
                    cn = self.code_mat[s1[i]]
                    c1 = chr(jis1.jis2uni(cn))
                    y1 = y[s1[i]]
                    print('{0:}({1:.3f}),'.format(c1, y1), end='')
                    # print(chr(jis.jis2uni(code_mat[s1[i]]))+' ', end='')
                print()
                # ch.append(chr(48 + np.argmax(y)))
                c = self.code_mat[np.argmax(y)]
                code.append(c)
                c2 = jis1.jis2uni(c)
                ch.append(chr(c2))
                text += chr(c2)

            text += '\n'

        # plt.show()
        # print(text)
        return image_copy, img4, text


if __name__ == '__main__':

    # home = os.path.expanduser('~')
    home = 'X:\kanyama'
    # ハガキ画像を指定して領域を抽出
    # cnts, img, img3 = detect_zipno("手書き数字1.jpg")
    # cnts, img, img3= detect_zipno("手書き数字＆かなカナ.tif")
    # cnts, img, img3 = detect_tegaki_moji(home + "/BOX_IMAGE/手書き文字認識用サンプル2/手書き文字認識用サンプル2_name_1.png")
    # cnts, img, img3 = detect_zipno("理事会議事録カラー.jpg")
    # cnts, img, img3 = detect_zipno("第2回理事会議事録グレー.jpg")
    # cnts, img, img3 = detect_zipno("理事会議事録白黒.tif")

    fname = home + '\手書き文字認識用サンプル2/手書き文字認識用サンプル2_doc_2.png'
    image_main = imread(fname)

    kf = kanji_find()
    img, img3, text = kf.kanji_text(image_main, PLOT_FLAG=True)
    print(text)
    # code_mat = kf.code_mat
    # jis_code_file = 'E:/DATA/ETL/ETL9B/ETL9BJISCODE.picle'
    # (code_mat) = pickle.load(open(jis_code_file, "rb"))
    # 画面に抽出結果を描画
    # plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # plt.savefig("detect-zip.png", dpi=200)
    # plt.show()

    # img4 = []
    # k=0
    # gn = sum([len(v) for v in img3])
    # for i in range(len(img3)):
    #     im1 = img3[i]
    #     for j in range(len(im1)):
    #         im2 = np.array(im1[j])
    #         # gray = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
    #         gray = im2
    #         gray = cv2.GaussianBlur(gray, (3, 3), 1)
    #         im2 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)[1]
    #         img4.append(im2)
    #         k += 1
    #         if k<= 35:
    #             plt.subplot(7, 5, k)
    #             plt.imshow(cv2.cvtColor(im2, cv2.COLOR_BGR2RGB))
    #     # plt.axis('off')
    # plt.show()
    #
    # im_rows = 32  # 画像の縦ピクセルサイズ
    # im_cols = 32  # 画像の横ピクセルサイズ
    # im_color = 1  # 画像の色空間/グレイスケール
    # in_shape = (im_rows, im_cols, im_color)
    # out_size = 10
    #
    # model = load_model('E:/DATA/ETL/ETL9B/etl9b_model3_32_2048_100_01.h5')
    #
    # # X_test = img4.reshape(-1, im_rows, im_cols, im_color)
    # im1 = []
    # for im in img4:
    #     im2 = cv2.resize(im,(im_rows, im_cols))
    #     im1.append(im2)
    #
    # im3 = np.array(im1)
    # X_test = im3.reshape(-1, im_rows, im_cols, im_color)
    # X_test = X_test.astype('float32') / 255
    # y1 = model.predict(X_test, verbose=1)
    # jis1 = jiscode()
    # ch = []
    # code = []
    # for y in y1:
    #     # print('max={} , index={}'.format(np.max(y), np.argmax(y)))
    #     s1 = np.argsort(y)[::-1]
    #     for i in range(10):
    #         cn = code_mat[s1[i]]
    #         c1 = chr(jis1.jis2uni(cn))
    #         y1 = y[s1[i]]
    #         print('{0:}({1:.3f}),'.format(c1, y1), end='')
    #         # print(chr(jis.jis2uni(code_mat[s1[i]]))+' ', end='')
    #     print()
    #     # ch.append(chr(48 + np.argmax(y)))
    #     c = code_mat[np.argmax(y)]
    #     code.append(c)
    #     c2 = jis1.jis2uni(c)
    #     ch.append(chr(c2))
    #
    # k = 0
    # moji = ''
    # fp1 = mincho_font_set(6,1.0)
    # for i in range(len(img3)):
    #     im1 = img3[i]
    #     for j in range(len(im1)):
    #         im2 = np.array(im1[j])
    #
    #         if k<=34:
    #             plt.subplot(7, 5, k + 1)
    #             # plt.imshow(im1)
    #             plt.imshow(cv2.cvtColor(im2, cv2.COLOR_BGR2RGB))
    #             plt.axis('off')
    #             plt.title('char={}'.format(ch[k]), FontProperties=fp1)
    #             moji += ch[k]
    #             k += 1
    #
    #     if i < len(im3-1):
    #         moji += '\n'
    #
    # print(moji)
    # plt.show()