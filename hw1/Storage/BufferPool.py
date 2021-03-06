import io, math, struct

from collections import OrderedDict
from struct      import Struct

from Catalog.Identifiers import PageId, FileId, TupleId
from Catalog.Schema      import DBSchema

import Storage.FileManager

class BufferPool:
  """
  A buffer pool implementation.

  Since the buffer pool is a cache, we do not provide any serialization methods.

  >>> schema = DBSchema('employee', [('id', 'int'), ('age', 'int')])
  >>> bp = BufferPool()
  >>> fm = Storage.FileManager.FileManager(bufferPool=bp)
  >>> bp.setFileManager(fm)

  # Check initial buffer pool size
  >>> len(bp.pool.getbuffer()) == bp.poolSize
  True

  """

  # Default to a 10 MB buffer pool.
  defaultPoolSize = 10 * (1 << 20)

  # Buffer pool constructor.
  #
  # REIMPLEMENT this as desired.
  #
  # Constructors keyword arguments, with defaults if not present:
  # pageSize       : the page size to be used with this buffer pool
  # poolSize       : the size of the buffer pool
  def __init__(self, **kwargs):
    self.pageSize     = kwargs.get("pageSize", io.DEFAULT_BUFFER_SIZE)
    self.poolSize     = kwargs.get("poolSize", BufferPool.defaultPoolSize)
    self.pool         = io.BytesIO(b'\x00' * self.poolSize)
    self.map = OrderedDict()
    self.mapfree = OrderedDict()
    ####################################################################################
    # DESIGN QUESTION: what other data structures do we need to keep in the buffer pool?





  def setFileManager(self, fileMgr):
    self.fileMgr = fileMgr

  # Basic statistics

  def numPages(self):
    return len(self.map)

  def numFreePages(self):
    return len(self.mapfree)
    #raise NotImplementedError

  def size(self):
    return self.poolSize

  def freeSpace(self):
    return self.numFreePages() * self.pageSize

  def usedSpace(self):
    return self.size() - self.freeSpace()


  # Buffer pool operations

  def hasPage(self, pageId):
    if(pageId in self.map):
        return True
    else:
        return False
    #raise NotImplementedError
  
  def insertPage(self,page):
      start = page.pageId.pageIndex * self.pageSize
      end = start + self.pageSize
      self.pool.getbuffer()[start:end] = page.pack()
      self.map[page.pageId] = page


  def getPage(self, pageId):
    if(self.hasPage(pageId)):
        start = pageId.pageIndex * self.pageSize
        end = start + self.pageSize
        page = self.pool.getbuffer()[start:end]
        self.map[pageId] = page
        #self.map.move_to_end(pageId)
    else:
        start = pageId.pageIndex * self.pageSize
        end = start + self.pageSize
        page = self.fileMgr.readPage(pageId,self.pool.getbuffer()[start:end])
        self.map[pageId] = page
        #self.insertPage(page)
        return page
    return page


    #raise NotImplementedError

  # Removes a page from the page map, returning it to the free 
  # page list without flushing the page to the disk.
  def discardPage(self, pageId):
    if(self.hasPage(pageId)):
        #self.map.pop(pageId,None)
        del self.map[pageId]
        while(self.hasPage(pageId)):
            del self.map[pageId]
        start = pageId.pageIndex * self.pageSize
        end = start + self.pageSize
        page = self.fileMgr.readPage(pageId,self.pool.getbuffer()[start:end])
        self.mapfree[pageId] = page 
    #else:
        #raise ValueError("This page is not in the buffer pool.")
    #raise NotImplementedError

  def flushPage(self, pageId):
    if(self.hasPage(pageId)):
        page = self.getPage(pageId)
        del self.map[pageId]
        view = io.BytesIO(page)
        pageClass =self.fileMgr.fileMap.get(pageId.fileId, None).pageClass()
        page2 = pageClass.unpack(pageId = pageId,buffer = view.getbuffer())
        self.fileMgr.writePage(page2)
        self.discardPage(pageId)
    else:
        raise ValueError("This page is not in the buffer pool.")
    #raise NotImplementedError

  # Evict using LRU policy. 
  # We implement LRU through the use of an OrderedDict, and by moving pages
  # to the end of the ordering every time it is accessed through getPage()
  def evictPage(self):
    if(self.usedSpace != 0):
        tup = self.map.popitem(last=True)
        self.mapfree.pop(tup[0],None)
        page = self.getPage(tup[0])
        del self.map[tup[0]]
        if(page[0] == 1):
            self.flushPage(tup[0])
    else:
        raise ValueError("There are no pages in the buffer pool.")
    #raise NotImplementedError

  # Flushes all dirty pages
  def clear(self):
    lst = []
    for pageId in self.map:
      lst.append(pageId)
    for pageId in lst:
      page = self.getPage(pageId)
      if(page[0] == 1):
        self.flushPage(pageId)
    #raise NotImplementedError

if __name__ == "__main__":
    import doctest
    doctest.testmod()
