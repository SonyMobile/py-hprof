'''hprof.heap holds record classes for interpreting records inside hprof.record.HeapDumpSegment.

The create() function can be used to create a record from an HprofFile and address. However, records
created in this way will be of limited use, since they will not have a reference to their Heap.
You'll probably be better off using hprof.Heap.objects() or hprof.Dump.records().
'''

from ._arrayrecords import Array, ObjectArray, PrimitiveArray
from ._classrecord import Class, FieldDecl, StaticField
from ._heapdumpinfo import HeapDumpInfo
from ._heaprecord import HeapRecord, Allocation, create
from ._roots import GcRoot, UnknownRoot, ThreadRoot, GlobalJniRoot, LocalJniRoot, JavaStackRoot, NativeStackRoot, VmInternalRoot, InternedStringRoot, StickyClassRoot, MonitorRoot
from ._objectrecord import Object
