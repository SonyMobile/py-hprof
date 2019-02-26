'''hprof.record holds all the top-level hprof record classes.

The create() function can be used to create a record from an HprofFile and address, though you'll
probably be better off with HprofFile.dumps() or HprofFile.records().
'''

from ._base import create, Record, Unhandled
from ._utf8 import Utf8
from ._classload import ClassLoad
from ._heapdump import HeapDumpSegment, HeapDumpEnd
