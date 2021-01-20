# -*- coding: utf-8 -*-

from parser import parse

if __name__ == '__main__':
    titles, data = parse('/home/stsav012/Downloads/log 210120 154531.vcl')
    print(titles)
    print(data[-1])
