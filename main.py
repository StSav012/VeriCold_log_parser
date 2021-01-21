# -*- coding: utf-8 -*-
import sys

if __name__ == '__main__':
    try:
        import gui
    except ImportError as ex:
        tb = sys.exc_info()[2]
        print(ex.with_traceback(tb))
        if 'qt' in str(ex.with_traceback(tb)).casefold():
            print('Ensure that PyQt5-sip and PyQt5 are installed')
    except SyntaxError:
        print('Get a newer Python!')
    else:
        gui.run()
