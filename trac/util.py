# -*- coding: iso8859-1 -*-
#
# Copyright (C) 2003, 2004 Edgewall Software
# Copyright (C) 2003, 2004 Jonas Borgstr�m <jonas@edgewall.com>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Jonas Borgstr�m <jonas@edgewall.com>

from __future__ import generators

import os
import sys
import time
import tempfile
import re

TRUE =  ['yes', '1', 1, 'true',  'on',  'aye']
FALSE = ['no',  '0', 0, 'false', 'off', 'nay']

CRLF = '\r\n'


def wiki_escape_newline(text):
    return text.replace(os.linesep, '[[BR]]' + os.linesep)

def enum(iterable):
    """
    Python 2.2 doesn't have the enumerate() function, so we provide a simple
    implementation here.
    """
    idx = 0
    for item in iter(iterable):
        yield idx, item
        idx += 1

def escape(text):
    """Escapes &, <, > and \""""
    if not text:
        return ''
    return str(text).replace('&', '&amp;') \
                    .replace('<', '&lt;') \
                    .replace('>', '&gt;') \
                    .replace('"', '&#34;')

def unescape(text):
    """Reverses Escapes &, <, > and \""""
    if not text:
        return ''
    return str(text).replace('&#34;', '"') \
                    .replace('&gt;', '>') \
                    .replace('&lt;', '<') \
                    .replace('&amp;', '&') 

def get_first_line(text, maxlen):
    """
    returns the first line of text. If the line is longer then
    maxlen characters it is truncated. The line is also html escaped.
    """
    lines = text.splitlines()
    line  = lines[0]
    if len(lines) > 1:
        return escape(line[:maxlen] + '...')
    elif len(line) > maxlen-3:
        return escape(line[:maxlen] + '...')
    else:
        return escape(line)

def lstrip(text, skip):
    """Python2.1 doesn't support custom skip characters"""
    while text:
        if text[0] in skip:
            text = text[1:]
        else:
            break
    return text

def rstrip(text, skip):
    """Python2.1 doesn't support custom skip characters"""
    while text:
        if text[-1] in skip:
            text = text[:-1]
        else:
            break
    return text

def strip(text, skip):
    """Python < 2.2.2 doesn't support custom skip characters"""
    return lstrip(rstrip(text, skip), skip)

def to_utf8(text, charset='iso-8859-15'):
    """Convert a string to utf-8, assume the encoding is either utf-8 or latin1"""
    try:
        # Do nothing if it's already utf-8
        u = unicode(text, 'utf-8')
        return text
    except UnicodeError:
        try:
            # Use the user supplied charset if possible
            u = unicode(text, charset)
        except UnicodeError:
            # This should always work
            u = unicode(text, 'iso-8859-15')
        return u.encode('utf-8')

def href_join(u1, *tail):
    """Join a list of url components and removes redundant '/' characters"""
    for u2 in tail:
        u1 = rstrip(u1, '/') + '/' + lstrip(u2, '/')
    return u1

def sql_escape(text):
    """
    Escapes the given string so that it can be safely used in an SQL
    statement
    """
    return text.replace("'", "''").replace("\\", "\\\\")

def sql_to_hdf (db, sql, hdf, prefix):
    """
    Execute a sql query and insert the first result column
    into the hdf at the given prefix
    """
    cursor = db.cursor()
    cursor.execute(sql)
    for idx, row in enum(cursor):
        hdf['%s.%d.name' % (prefix, idx)] = row[0]

def hdf_add_if_missing(hdf, prefix, value):
    """Loop through the hdf values and add @value if id doesn't exist"""
    node = hdf.getObj(prefix + '.0')
    i = 0
    while node:
        child = node.child()
        if child and child.value() == value:
            return
        node = node.next()
        i += 1
    hdf.setValue(prefix + '.%d.name' % i, value)

def shorten_line(text, maxlen = 75):
    if not text:
        return ''
    i = text.find('[[BR]]')
    j = text.find('\n')
    if i > -1 and i < maxlen:
        shortline = text[:i]+' ...'
    elif j > -1 and j < maxlen:
        shortline = text[:j]+' ...'
    elif len(text) < maxlen:
        shortline = text
    else:
        i = text[:maxlen].rfind(' ')
        if i == -1:
            i = maxlen
        shortline = text[:i]+' ...'
    return shortline

def hex_entropy(bytes=32):
    import md5
    import random
    return md5.md5(str(random.random() + time.time())).hexdigest()[:bytes]

def http_date(t):
    t = time.gmtime(t)
    weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
              'Oct', 'Nov', 'Dec']
    return '%s, %d %s %04d %02d:%02d:%02d GMT' % (
           weekdays[t.tm_wday], t.tm_mday, months[t.tm_mon - 1], t.tm_year,
           t.tm_hour, t.tm_min, t.tm_sec)

def pretty_size(size):
    jump = 512
    if size is None:
        return ''
    if size < jump:
        unit = 'bytes'
    else:
        size /= 1024.0
        if size < jump:
            unit = 'kB'
        else:
            size /= 1024.0
            if size < jump:
                unit = 'MB'
            else:
                size /= 1024.0
                if size < jump:
                    unit = 'GB'
                else:
                    unit = 'TB'
    return ('%.1f %s' % (size, unit)).replace('.0','')


def pretty_timedelta(time1, time2=None):
    """Calculate time delta (inaccurately, only for decorative purposes ;-) for
    prettyprinting. If time1 is None, the current time is used."""
    if not time1: time1 = time.time()
    if not time2: time2 = time.time()
    if time1 > time2:
        time2, time1 = time1, time2
    units = ((3600 * 24 * 365, 'year',   'years'),
             (3600 * 24 * 30,  'month',  'months'),
             (3600 * 24 * 7,   'week',   'weeks'),
             (3600 * 24,       'day',    'days'),
             (3600,            'hour',   'hours'),
             (60,              'minute', 'minutes'))
    age_s = int(time2 - time1)
    if age_s < 60:
        return '%i second%s' % (age_s, age_s > 1 and 's' or '')
    for u, unit, unit_plural in units:
        r = float(age_s) / float(u)
        if r >= 0.9:
            r = int(round(r))
            return '%d %s' % (r, r == 1 and unit or unit_plural)
    return ''

def create_unique_file(path):
    """Create a new file. An index is added if the path exists"""
    parts = os.path.splitext(path)
    idx = 1
    while 1:
        try:
            flags = os.O_CREAT + os.O_WRONLY + os.O_EXCL
            if hasattr(os, 'O_BINARY'):
                flags += os.O_BINARY
            return path, os.fdopen(os.open(path, flags), 'w')
        except OSError:
            idx += 1
            # A sanity check
            if idx > 100:
                raise Exception('Failed to create unique name: ' + path)
            path = '%s.%d%s' % (parts[0], idx, parts[1])

def get_reporter_id(req):
    name = req.session.get('name', None)
    email = req.session.get('email', None)
    
    if req.authname != 'anonymous':
        return req.authname
    elif name and email:
        return '%s <%s>' % (name, email)
    elif not name and email:
        return email
    else:
        return req.authname

def get_date_format_hint():
    t = time.localtime(0)
    t = (1999, 10, 29, t[3], t[4], t[5], t[6], t[7], t[8])
    tmpl = time.strftime('%x', t)
    return tmpl.replace('1999', 'YYYY', 1).replace('99', 'YY', 1) \
               .replace('10', 'MM', 1).replace('29', 'DD', 1)

def get_datetime_format_hint():
    t = time.localtime(0)
    t = (1999, 10, 29, 23, 59, 58, t[6], t[7], t[8])
    tmpl = time.strftime('%x %X', t)
    return tmpl.replace('1999', 'YYYY', 1).replace('99', 'YY', 1) \
               .replace('10', 'MM', 1).replace('29', 'DD', 1) \
               .replace('23', 'hh', 1).replace('59', 'mm', 1) \
               .replace('58', 'ss', 1)


class TracError(Exception):
    def __init__(self, message, title=None, show_traceback=0):
        Exception.__init__(self, message)
        self.message = message
        self.title = title
        self.show_traceback = show_traceback


class NaivePopen:
   """
   This is a deadlock-safe version of popen that returns
   an object with errorlevel, out (a string) and err (a string).
   (capturestderr may not work under windows.)
   Example: print Popen3('grep spam','\n\nhere spam\n\n').out
   """
   def __init__(self,command,input=None,capturestderr=None):
       outfile=tempfile.mktemp()
       command="( %s ) > %s" % (command,outfile)
       if input:
           infile=tempfile.mktemp()
           open(infile,"w").write(input)
           command=command+" <"+infile
       if capturestderr:
           errfile=tempfile.mktemp()
           command=command+" 2>"+errfile
       self.errorlevel=os.system(command) >> 8
       self.out=open(outfile,"r").read()
       os.remove(outfile)
       if input:
           os.remove(infile)
       self.err = None
       if capturestderr:
           self.err=open(errfile,"r").read()
           os.remove(errfile)


def wrap(t, cols=75, initial_indent='', subsequent_indent='',
         linesep=os.linesep):
    try:
        import textwrap
        t = t.strip().replace('\r\n', '\n').replace('\r', '\n')
        wrapper = textwrap.TextWrapper(cols, replace_whitespace = 0,
                                       break_long_words = 0,
                                       initial_indent = initial_indent,
                                       subsequent_indent = subsequent_indent)
        wrappedLines = []
        for line in t.split('\n'):
            wrappedLines += wrapper.wrap(line.rstrip()) or ['']
        return linesep.join(wrappedLines)

    except ImportError:
        return t


def safe__import__(module_name):
    """
    Safe imports: rollback after a failed import.
    
    Initially inspired from the RollbackImporter in PyUnit,
    but it's now much simpler and works better for our needs.
    
    See http://pyunit.sourceforge.net/notes/reloading.html
    """
    already_imported = sys.modules.copy()
    try:
        return __import__(module_name, globals(), locals(), [])
    except Exception, e:
        for modname in sys.modules.copy():
            if not already_imported.has_key(modname):
                del(sys.modules[modname])
        raise e


class Deuglifier(object):
    def __new__(cls):
        self = object.__new__(cls)
        if not hasattr(cls, '_compiled_rules'):
            cls._compiled_rules = re.compile('(?:' + '|'.join(cls.rules()) + ')')
        self._compiled_rules = cls._compiled_rules
        return self
    
    def format(self, indata):
        return re.sub(self._compiled_rules, self.replace, indata)

    def replace(self, fullmatch):
        for mtype, match in fullmatch.groupdict().items():
            if match:
                if mtype == 'font':
                    return '<span>'
                elif mtype == 'endfont':
                    return '</span>'
                return '<span class="code-%s">' % mtype

class Pager:
    def __init__(self, limit, skip):
        self.limit = limit
        self.skip = skip
        self.count = self.skipped = 0

    def skipping(self):
        if self.skip and self.skipped < self.skip:
            self.skipped += 1
            return True
        else:
            return False

    def next(self):
        self.count += 1
        if self.limit and self.count > self.limit:
            return False
        else:
            return True
