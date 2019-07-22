"""xmltramp: Make XML documents easily accessible."""

from io import BytesIO
from xml.sax.handler import EntityResolver, DTDHandler, ContentHandler, ErrorHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces

import os, sys, time
import pdb

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    from builtins import range as xrange
    from io import StringIO
    from http import client as http_client
    from urllib.parse import urlparse
    from urllib.request import urlopen
    text_type = str
else:
    print('Please use Python3 to run this script.')
    sys.exit()

__version__ = "2.18"
__author__ = "Aaron Swartz"
__credits__ = "Many thanks to pjz, bitsko, and DanC."
__copyright__ = "(C) 2003-2006 Aaron Swartz. GNU GPL 2."


def isstr(f):
    return isinstance(f, str) or isinstance(f, text_type)


def islst(f):
    return isinstance(f, tuple) or isinstance(f, list)


empty = {'http://www.w3.org/1999/xhtml':
         ['img', 'br', 'hr', 'meta', 'link', 'base', 'param', 'input', 'col', 'area']}

nprint = lambda x: print(x, end='')

def quote(x, elt=True):
    if elt and '<' in x and len(x) > 24 and x.find(']]>') == -1:
        return "<![CDATA[{}]]>".format(x)
    else:
        x = x.replace('&', '&amp;').replace('<', '&lt;').replace(']]>', ']]&gt;')
    if not elt:
        x = x.replace('"', '&quot;')
    return x


class Element(object):
    def __init__(self, name, attrs=None, children=None, prefixes=None):
        if islst(name) and name[0] is None:
            name = name[1]
        if attrs:
            na = {}
            for k in attrs.keys():
                if islst(k) and k[0] is None:
                    na[k[1]] = attrs[k]
                else:
                    na[k] = attrs[k]
            attrs = na

        self._name = name
        self._attrs = attrs or {}
        self._dir = children or []

        prefixes = prefixes or {}
        self._prefixes = dict(zip(prefixes.values(), prefixes.keys()))

        if prefixes:
            self._dNS = prefixes.get(None, None)
        else:
            self._dNS = None

    def __repr__(self, recursive=0, multiline=0, inprefixes=None):
        def qname(name, inprefixes):
            if islst(name):
                if inprefixes[name[0]] is not None:
                    return inprefixes[name[0]] + ':' + name[1]
                else:
                    return name[1]
            else:
                return name

        def arep(a, inprefixes, addns=1):
            out = ''

            for p in sorted(self._prefixes.keys()):
                if p not in inprefixes.keys():
                    if addns:
                        out += ' xmlns'
                    if addns and self._prefixes[p]:
                        out += ':' + self._prefixes[p]
                    if addns:
                        out += '="{}"'.format(quote(p, False))
                    inprefixes[p] = self._prefixes[p]

            for k in sorted(a.keys()):
                out += ' ' + qname(k, inprefixes) + '="' + quote(a[k], False) + '"'

            return out

        inprefixes = inprefixes or {'http://www.w3.org/XML/1998/namespace': 'xml'}

        # need to call first to set inprefixes:
        attributes = arep(self._attrs, inprefixes, recursive)
        out = '<' + qname(self._name, inprefixes) + attributes

        if not self._dir and (self._name[0] in empty.keys() and
                              self._name[1] in empty[self._name[0]]):
            out += ' />'
            return out

        out += '>'

        if recursive:
            content = 0
            for x in self._dir:
                if isinstance(x, Element):
                    content = 1

            pad = '\n' + ('\t' * recursive)
            for x in self._dir:
                if multiline and content:
                    out += pad
                if isstr(x):
                    out += quote(x)
                elif isinstance(x, Element):
                    out += x.__repr__(recursive + 1, multiline, inprefixes.copy())
                else:
                    raise TypeError("I wasn't expecting {}.".format(repr(x)))
            if multiline and content:
                out += '\n' + ('\t' * (recursive - 1))
        else:
            if self._dir:
                out += '...'

        out += '</' + qname(self._name, inprefixes) + '>'

        return out

    def __str__(self):
        text = u''
        for x in self._dir:
            # "six.text_type" is unicode in Python 2 and str in Python 3.
            text += text_type(x)
        return ' '.join(text.split())

    def __getattr__(self, n):
        if n[0] == '_':
            raise AttributeError("Use foo['{}'] to access the child element.".format(n))
        if self._dNS:
            n = (self._dNS, n)
        for x in self._dir:
            if isinstance(x, Element) and x._name == n:
                return x
        raise AttributeError('No child element named {}'.format(repr(n)))

    def __hasattr__(self, n):
        for x in self._dir:
            if isinstance(x, Element) and x._name == n:
                return True
        return False

    def __setattr__(self, n, v):
        if n[0] == '_':
            self.__dict__[n] = v
        else:
            self[n] = v

    def __getitem__(self, n):
        if isinstance(n, int):  # d[1] == d._dir[1]
            return self._dir[n]
        elif isinstance(n, slice):
            # numerical slices
            if isinstance(n.start, int) or n == slice(None):
                return self._dir[n.start:n.stop]

            # d['foo':] == all <foo>s
            n = n.start
            if self._dNS and not islst(n):
                n = (self._dNS, n)
            out = []
            for x in self._dir:
                if isinstance(x, Element) and x._name == n:
                    out.append(x)
            return out
        else:  # d['foo'] == first <foo>
            if self._dNS and not islst(n):
                n = (self._dNS, n)
            for x in self._dir:
                if isinstance(x, Element) and x._name == n:
                    return x
            raise KeyError(n)

    def __setitem__(self, n, v):
        if isinstance(n, int):  # d[1]
            self._dir[n] = v
        elif isinstance(n, slice):
            # d['foo':] adds a new foo
            n = n.start
            if self._dNS and not islst(n):
                n = (self._dNS, n)

            nv = Element(n)
            self._dir.append(nv)

        else:  # d["foo"] replaces first <foo> and dels rest
            if self._dNS and not islst(n):
                n = (self._dNS, n)

            nv = Element(n)
            nv._dir.append(v)
            replaced = False

            todel = []
            for i in xrange(len(self)):
                if self[i]._name == n:
                    if replaced:
                        todel.append(i)
                    else:
                        self[i] = nv
                        replaced = True
            if not replaced:
                self._dir.append(nv)
            for i in sorted(todel, reverse=True):
                del self[i]

    def __delitem__(self, n):
        if isinstance(n, int):
            del self._dir[n]
        elif isinstance(n, slice):
            # delete all <foo>s
            n = n.start
            if self._dNS and not islst(n):
                n = (self._dNS, n)

            for i in reversed(range(len(self))):
                if self[i]._name == n:
                    del self[i]
        else:
            # delete first foo
            for i in range(len(self)):
                if self[i]._name == n:
                    del self[i]
                    break

    def __call__(self, *_pos, **_set):
        if _set:
            for k in _set.keys():
                self._attrs[k] = _set[k]
        if len(_pos) > 1:
            for i in range(0, len(_pos), 2):
                self._attrs[_pos[i]] = _pos[i + 1]
        if len(_pos) == 1:
            return self._attrs[_pos[0]]
        if len(_pos) == 0:
            return self._attrs

    def __len__(self):
        return len(self._dir)

    def getMaxLevel(self, son=None):
        if son is None:
            level = 0
            if len(self._dir) == 0:
                return level
            elif len(self._dir) == 1:
                if isinstance(self._dir[0], Element):
                    level = self.getMaxLevel(self._dir[0]) + 1
                return level
            else:
                ll = [self.getMaxLevel(ss) for ss in self._dir if isinstance(ss, Element)]
                if len(ll) > 0:
                    level = max(ll) + 1
                return level
        else:
            level = 0
            if len(son._dir) == 0:
                return level
            elif len(son._dir) == 1:
                if isinstance(son._dir[0], Element):
                    level = self.getMaxLevel(son._dir[0]) + 1
                return level
            else:
                ll = [self.getMaxLevel(ss) for ss in son._dir if isinstance(ss, Element)]
                if len(ll) > 0:
                    level = max(ll) + 1
                return level

class Namespace(object):
    def __init__(self, uri):
        self.__uri = uri

    def __getattr__(self, n):
        return (self.__uri, n)

    def __getitem__(self, n):
        return (self.__uri, n)

class StackShow:
    def __init__(self):
        self.columns, self.lines = os.get_terminal_size()
        self.vinte, self.vrem = divmod(self.columns, 12)
        self.vi, _ = divmod(self.columns, 2)
        self.sprint([], 'Initial an empty stack for parsing xml.', '')

    def getFirstLineMsg(self, operation, value):
        if isinstance(value, Element):
            return '{} --> Element is: {}'.format(operation, repr(value))
        elif isinstance(value, str):
            return '{} --> str is: {}'.format(operation, value)

    def getMsgBox(self, msg):
        row_length = self.vi - 2
        total_length = row_length * 6
        nmsg = msg[0:total_length]
        length = len(msg)
        nvi, nvr = divmod(length, row_length)
        def gg(nss, num, inte, rem):
            nonlocal row_length
            if num <= inte:
                return nss[(num-1)*row_length : (num-1)*row_length+row_length]
            elif num == inte + 1:
                return '{}{}'.format(nss[inte*row_length : ], ' ' * (row_length-rem))
            else:
                return ' ' * row_length
        line1, line2, line3, line4, line5, line6 = ['{}'.format(gg(nmsg, vl, nvi, nvr)) for vl in range(1, 7)]
        return line1, line2, line3, line4, line5, line6

    def getBlock(self, ss):
        def getStr(nss, num, inte, rem):
            if num <= inte:
                return nss[(num-1)*10 : (num-1)*10+10]
            elif num == inte + 1:
                return '{}{}'.format(nss[inte*10 : ], ' ' * (10-rem))
            else:
                return ' ' * 10
        nss = ss[:40]
        inte, rem = divmod(len(nss), 10)
        line1, line6 = '{}{}{}'.format('|', '-' * 10, '|'), '{}{}{}'.format('|', '-' * 10, '|')
        line2, line3, line4, line5 = ['{}{}{}'.format('|', getStr(nss, vl, inte, rem), '|') for vl in range(1, 5)]
        return line1, line2, line3, line4, line5, line6

    def sprint(self, stack, operation, value):
        length = len(stack)
        if length == 0:
            nprint('-' * self.columns)
            nprint('| Message: '); nprint(operation); nprint(' ' * (self.columns-12-len(operation))); nprint('|')
            nprint('-' * self.columns)
            def pr1():
                nprint('|'); nprint(' ' * (self.columns-2)); nprint('|')
            [pr1() for _ in range(6)]
            nprint('-' * self.columns)
            nprint('*' * self.columns)
            nprint('* Stack:  bottom >------> top');nprint(' ' * (self.columns-30));nprint('*')
            nprint('*' * self.columns)
            def pr2():
                nprint('>'); nprint(' ' * (self.columns-2)); nprint('>')
            [pr2() for _ in range(6)]
            nprint('*' * self.columns)
        elif length <= self.vinte:
            msgbox = self.getFirstLineMsg(operation, value)
            nline1, nline2, nline3, nline4, nline5, nline6 = self.getMsgBox(msgbox)

            nprint('-' * self.columns)
            nprint('| Message: '); nprint(operation); nprint(' ' * (self.columns-12-len(operation)));nprint('|')
            nprint('-' * self.columns)
            def pr3(line):
                nprint('|'); nprint(line); nprint('|'); nprint(' ' * (self.columns-1-self.vi)); nprint('|')
            for v in range(1,7):
                pr3(eval('nline{}'.format(v)))
            nprint('-' * self.columns)
            nprint('*' * self.columns)
            nprint('* Stack:  bottom >------> top'); nprint(' ' * (self.columns-30)); nprint('*')
            nprint('*' * self.columns)

            L1, L2, L3, L4, L5, L6 = '>', '>', '>', '>', '>', '>'
            
            for i in range(length):
                line1, line2, line3, line4, line5, line6 = self.getBlock(repr(stack[i]))
                #for j in range(1,7):
                #    exec('L{} += line{}'.format(j, j))
                L1 += line1
                #exec('L1=L1+line1')
                L2 += line2
                L3 += line3
                L4 += line4
                L5 += line5
                L6 += line6
            pdb.set_trace()
            tail = ' ' * (self.columns-2-length*12) + '>'
            expr = "L8='''{}'''".format(eval("L1+tail"))
            exec(expr)
            print(L8)
            #L1 += tail
            L2 += tail
            L3 += tail
            L4 += tail
            L5 += tail
            L6 += tail
            for ll in range(1,7):
                nprint(eval('L{}'.format(ll)))
            nprint('*' * self.columns)

        else:
            print('Beyond screen width, cannot show it to you, please use a lower layer xml.')

        [print() for i in range(self.lines-22)]
        time.sleep(2)

    def printStack(self, stack=None):
        pass

class Seeder(EntityResolver, DTDHandler, ContentHandler, ErrorHandler):
    def __init__(self):
        self.stack = []
        self.ch = ''
        self.prefixes = {}
        self.show = StackShow()
        ContentHandler.__init__(self)

    def startPrefixMapping(self, prefix, uri):
        if prefix not in self.prefixes:
            self.prefixes[prefix] = []
        self.prefixes[prefix].append(uri)

    def endPrefixMapping(self, prefix):
        self.prefixes[prefix].pop()
        # szf: 5/15/5
        if len(self.prefixes[prefix]) == 0:
            del self.prefixes[prefix]

    def startElementNS(self, name, qname, attrs):
        ch = self.ch
        self.ch = ''
        if ch and not ch.isspace():
            self.stack[-1]._dir.append(ch)

        attrs = dict(attrs)
        newprefixes = {}
        for k in self.prefixes.keys():
            newprefixes[k] = self.prefixes[k][-1]

        self.stack.append(Element(name, attrs, prefixes=newprefixes.copy()))
        self.show.sprint(self.stack.copy(), 'Stack IN',  self.stack[-1])

    def characters(self, ch):
        # This is called only by sax (never directly) and the string ch is
        # everytimes converted to text_type (unicode) by sax.
        self.ch += ch

    def endElementNS(self, name, qname):
        ch = self.ch
        self.ch = ''
        if ch and not ch.isspace():
            self.stack[-1]._dir.append(ch)
            self.show.sprint(self.stack.copy(), 'Stack top add text',  ch)

        element = self.stack.pop()
        self.show.sprint(self.stack.copy(), 'Stack POP', element)
        if self.stack:
            self.stack[-1]._dir.append(element)
            self.show.sprint(self.stack.copy(), 'Stack top add Element', element)
        else:
            self.result = element


def seed(fileobj):
    seeder = Seeder()
    parser = make_parser()
    parser.setFeature(feature_namespaces, 1)
    parser.setContentHandler(seeder)
    parser.parse(fileobj)
    return seeder.result


def parse(text):
    """Parse XML to tree of Element.

    text: XML in unicode or byte string
    """
    return seed(StringIO(text) if isinstance(text, text_type) else BytesIO(text))


