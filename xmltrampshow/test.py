import pdb
import xmltrampShow
import os

doc = xmltrampShow.Namespace('urn:partner.soap.sforce.com')
soapenv = xmltrampShow.Namespace('http://schemas.xmlsoap.org/soap/envelope/')
xsi = xmltrampShow.Namespace('http://www.w3.org/2001/XMLSchema-instance')

with open('movies.xml', 'r') as fo:
    res = xmltrampShow.parse(fo.read())

#print(repr(res))
#pdb.set_trace()
#print('res level: {}'.format(res.getMaxLevel()))
#print(res[:])
#result = res[soapenv.Body][0]
#print(result[:])
def nprint(ss):
    print(ss, end='')

class StackShow:
    def __init__(self, tramp):
        self.columns, self.lines = os.get_terminal_size()
        self.kk = 14
        self.strs = 'abcdefghijklmnopqrstuvwxyz'

    def getStr(self, nss, num, inte, rem):
        if num <= inte:
            return nss[(num-1) * 10 : (num-1) * 10 + 10]
        elif num == inte + 1:
            return '{}{}'.format(nss[inte*10 : ], ' ' * (10-rem))
        else:
            return ' ' * 10

    def getBlock(self, ss):
        nss = ss[:40]
        inte, rem = divmod(len(nss), 10)
        length = 12
        line1, line6 = '{}{}{}'.format('|', '-' * 10, '|'), '{}{}{}'.format('|', '-' * 10, '|')
        line2, line3, line4, line5 = ['{}{}{}'.format('|', self.getStr(nss, vl, inte, rem), '|') for vl in range(1, 5)]
        return line1, line2, line3, line4, line5, line6

    def showBlock(self, ss, num):
        line1, line2, line3, line4, line5, line6 = self.getBlock(ss)
        val = 'line{}'.format(num)
        nprint(eval(val))

    def run(self):
        self.kk += 12
        print()
        nprint('-' * self.columns)
        nprint('| Temp:');nprint(' ' * (self.columns-8));nprint('|');
        nprint('-' * self.columns)
        nprint('|');nprint(' ' * (self.columns-2));nprint('|')
        nprint('|');nprint(' ' * (self.columns-2));nprint('|')
        nprint('|');nprint(' ' * (self.columns-2));nprint('|')
        nprint('|');nprint(' ' * (self.columns-2));nprint('|')
        nprint('|');nprint(' ' * (self.columns-2));nprint('|')
        nprint('-' * self.columns)
        nprint('*' * self.columns)
        nprint('* Stack:  bottom >------> top');nprint(' ' * (self.columns-30));nprint('*');
        nprint('*' * self.columns)
        nprint('>');nprint('|');nprint('-' * 10);nprint('|');self.showBlock(self.strs, 1);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('>');nprint('|');nprint('A' * 10);nprint('|');self.showBlock(self.strs, 2);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('>');nprint('|');nprint('B' * 10);nprint('|');self.showBlock(self.strs, 3);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('>');nprint('|');nprint('C' * 10);nprint('|');self.showBlock(self.strs, 4);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('>');nprint('|');nprint('D' * 10);nprint('|');self.showBlock(self.strs, 5);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('>');nprint('|');nprint('-' * 10);nprint('|');self.showBlock(self.strs, 6);nprint(' ' * (self.columns-self.kk));nprint('>')
        nprint('*' * self.columns)
        
        i = 0
        while i < (int(self.lines) - 24):
            print()
            i += 1

if __name__ == '__main__':
    show = StackShow(res)
    #show.run()