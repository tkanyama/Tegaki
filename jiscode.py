# -*- coding: utf-8 -*-

class jiscode():

    def __init__(self):

        self.shift_jis = []
        self.jisx0208 = []
        self.unicode = []
        with open("JIS0208.txt", "r") as f:
            for line in f:
                if line[0] == "#":
                    pass
                else:
                    sjis, jisx, unic, _ = line.strip().split("\t")
                    self.shift_jis.append(int(sjis, 16))
                    self.jisx0208.append(int(jisx, 16))
                    self.unicode.append(int(unic, 16))

    def jis2uni(self, n=0):
        if n <= 127:
            return n
        else:
            return self.unicode[self.jisx0208.index(n)]

    def jis2shift_jis(self, n=0):
        if n <= 127:
            return n
        else:
            return self.shift_jis[self.jisx0208.index(n)]

    def uni2shift_jis(self, n=0):
        if n <= 127:
            return n
        else:
            return self.shift_jis[self.unicode.index(n)]

    def uni2jis(self, n=0):
        if n <= 127:
            return n
        else:
            return self.jisx0208[self.unicode.index(n)]

    def shift_jis2jis(self, n=0):
        if n <= 127:
            return n
        else:
            return self.jisx0208[self.shift_jis.index(n)]

    def shift_jis2uni(self, n=0):
        if n <= 127:
            return n
        else:
            return self.unicode[self.shift_jis.index(n)]

if __name__ == '__main__':
    j1 = jiscode()
    c1 = j1.jis2uni(0x2422)
    print("{:x}".format(c1))
    print(chr(c1))
    c2 = j1.uni2jis(c1)
    print("{:x}".format(c2))