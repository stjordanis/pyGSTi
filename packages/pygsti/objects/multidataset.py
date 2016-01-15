""" Defines the MultiDataSet class and supporting classes and functions """
import numpy as _np
import cPickle as _pickle
from collections import OrderedDict as _OrderedDict

from gatestring import GateString as _GateString
from dataset import DataSet as _DataSet
import dataset as _ds

class MultiDataSet_KeyValIterator:
  """ Iterator class for datasetName,DataSet pairs of a MultiDataSet """
  def __init__(self, multidataset):
    self.multidataset = multidataset
    self.countsDictIter = multidataset.countsDict.__iter__()

  def __iter__(self):
    return self

  def next(self):
    datasetName = self.countsDictIter.next()
    return datasetName, _DataSet(self.multidataset.counts[datasetName], gateStringIndices=self.multidataset.gsIndex,
                                spamLabelIndices=self.multidataset.slIndex, bStatic=True)
  

class MultiDataSet_ValIterator:
  """ Iterator class for DataSets of a MultiDataSet """
  def __init__(self, multidataset):
    self.multidataset = multidataset
    self.countsDictIter = multidataset.countsDict.__iter__()
    self.countIter = dataset.counts.__iter__()

  def __iter__(self):
    return self

  def next(self):
    datasetName = self.countsDictIter.next()
    return _DataSet(self.multidataset.counts[datasetName], gateStringIndices=self.multidataset.gsIndex,
                    spamLabelIndices=self.multidataset.slIndex, bStatic=True)


class MultiDataSet:
  """ 
  The MultiDataSet class allows for the combined access and storage of 
  several static DataSets that contain the same gate strings (in the same order).
  It is designed to behave similarly to a dictionary of DataSets, so that
  a DataSet is obtained by (Note that datasetName may be a tuple):
  
  dataset = multiDataset[datasetName]
  """

  def __init__(self, countsDict=None, 
               gateStrings=None, gateStringIndices=None, 
               spamLabels=None, spamLabelIndices=None,
               fileToLoadFrom=None):
    """ 
    Initialize a MultiDataSet.
      
    Parameters
    ----------
    countsDict : ordered dictionary, optional
      Keys specify dataset names.  Values are 2D numpy arrays which specify counts. Rows of the arrays
      correspond to gate strings and columns to spam labels.

    gateStrings : list of (tuples or GateStrings), optional
      Each element is a tuple of gate labels or a GateString object.  Indices for these strings
      are assumed to ascend from 0.  These indices must correspond to rows/elements of counts (above).
      Only specify this argument OR gateStringIndices, not both.

    gateStringIndices : ordered dictionary, optional
      An OrderedDict with keys equal to gate strings (tuples of gate labels) and values equal to
      integer indices associating a row/element of counts with the gate string.  Only
      specify this argument OR gateStrings, not both.

    spamLabels : list of strings, optional
      Specifies the set of spam labels for the DataSet.  Indices for the spam labels
      are assumed to ascend from 0, starting with the first element of this list.  These
      indices will index columns of the counts array/list.  Only specify this argument
      OR spamLabelIndices, not both.

    spamLabelIndices : ordered dictionary, optional
      An OrderedDict with keys equal to spam labels (strings) and value  equal to 
      integer indices associating a spam label with a column of counts.  Only 
      specify this argument OR spamLabels, not both.

    fileToLoadFrom : string or file object, optional
      Specify this argument and no others to create a MultiDataSet by loading
      from a file (just like using the load(...) function).
    """

    #Optionally load from a file
    if fileToLoadFrom is not None:
      assert(countsDict is None and gateStrings is None and gateStringIndices is None and spamLabels is None and spamLabelIndices is None)
      self.load(fileToLoadFrom)
      return

    # self.gsIndex  :  Ordered dictionary where keys = gate strings (tuples), values = integer indices into counts
    if gateStringIndices is not None:
      self.gsIndex = gateStringIndices
    elif gateStrings is not None:
      if len(gateStrings) > 0 and isinstance(gateStrings[0], _GateString):
        self.gsIndex = _OrderedDict( [(gs.tup,i) for (i,gs) in enumerate(gateStrings) ] )
      else:
        self.gsIndex = _OrderedDict( [(gs,i) for (i,gs) in enumerate(gateStrings) ] )
    else:
      self.gsIndex = None

    # self.slIndex  :  Ordered dictionary where keys = spam labels (strings), values = integer indices into counts
    if spamLabelIndices is not None:
      self.slIndex = spamLabelIndices
    elif spamLabels is not None:
      self.slIndex = _OrderedDict( [(sl,i) for (i,sl) in enumerate(spamLabels) ] )
    else: 
      self.slIndex = None

    if self.gsIndex:  #Note: tests if not none and nonempty
      assert( min(self.gsIndex.values()) >= 0)
    if self.slIndex:  #Note: tests if not none and nonempty
      assert( min(self.slIndex.values()) >= 0)

    # self.countsDict : a dictionary of 2D numpy arrays, each corresponding to a DataSet.  Rows = gate strings, Cols = spam labels      
    #                   ( keys = dataset names, values = 2D counts array of corresponding dataset )
    if countsDict is not None:
      self.countsDict = _OrderedDict( [ (name,counts) for name,counts in countsDict.iteritems() ] ) #copy OrderedDict but share counts arrays
      if self.gsIndex:  #Note: tests if not none and nonempty
        minIndex = min(self.gsIndex.values())
        maxIndex = max(self.gsIndex.values())
        for dsName,counts in self.countsDict.iteritems():
          assert( counts.shape[0] > maxIndex and counts.shape[1] == len(self.slIndex) )
    else:
      self.countsDict = _OrderedDict()

  
  def __iter__(self):
    return self.countsDict.__iter__() #iterator over gate strings

  def __len__(self):
    return len(self.countsDict)

  def __getitem__(self, datasetName):  #return a static DataSet
    return _DataSet(self.countsDict[datasetName], gateStringIndices=self.gsIndex, spamLabelIndices=self.slIndex, bStatic=True)

  def __setitem__(self, datasetName, dataset):
    self.addDataset(datasetName, dataset)

  def __contains__(self, datasetName):
    return datasetName in self.countsDict

  def keys(self):
    """ Returns a list of the keys (dataset names) of this MultiDataSet """
    return self.countsDict.keys()

  def has_key(self, datasetName):
    """ Test whether this MultiDataSet contains a given dataset name """
    return datasetName in self.countsDict

  def iteritems(self):
    """ Iterator over (dataset name, DataSet) pairs """
    return MultiDataSet_KeyValIterator(self)
    
  def itervalues(self):
    """ Iterator over DataSets corresponding to each dataset name """
    return MultiDataSet_ValIterator(self)

  def getDatasetsSum(self, *datasetNames):
    """
    Generate a new DataSet by combining the counts of multiple member Datasets.
    
    Parameters
    ----------
    datasetNames : one or more dataset names.

    Returns
    -------
    DataSet
        a single DataSet containing the summed counts of each of the datasets
        named by the parameters.
    """
    summedCounts = None
    if len(datasetNames) == 0: raise ValueError("Must specify at least one dataset name")
    for datasetName in datasetNames:
      if datasetName not in self:
        raise ValueError("No dataset with the name '%d' exists" % datasetName)

      if summedCounts is None:
        summedCounts = self.countsDict[datasetName].copy()
      else:
        summedCounts += self.countsDict[datasetName]
        
    return _DataSet(summedCounts, gateStringIndices=self.gsIndex,
                    spamLabelIndices=self.slIndex, bStatic=True)

  def addDataset(self, datasetName, dataset):
    """ 
    Add a DataSet to this MultiDataSet.  The dataset
    must be static and conform with the gate strings passed
    upon construction or those inherited from the first 
    dataset added.

    Parameters
    ----------
    datasetName : string
        The name to give the added dataset (i.e. the key the new
        data set will be referenced by).

    dataset : DataSet
        The data set to add.
    """
    
    #first test if dataset is compatible
    if not dataset.bStatic: 
      raise ValueError("Cannot add dataset: only static DataSets can be added to a MultiDataSet")
    if self.gsIndex is not None and dataset.gsIndex != self.gsIndex:
      raise ValueError("Cannot add dataset: gate strings and/or their indices do not match") 
    if self.slIndex is not None and dataset.slIndex != self.slIndex:
      raise ValueError("Cannot add dataset: spam labels and/or their indices do not match")

    if self.gsIndex:  #Note: tests if not none and nonempty
        maxIndex = max(self.gsIndex.values())
        assert( dataset.counts.shape[0] > maxIndex and dataset.counts.shape[1] == len(self.slIndex) )

    self.countsDict[datasetName] = dataset.counts

    if self.gsIndex is None: 
      self.gsIndex = dataset.gsIndex
      if len(self.gsIndex) > 0:
        assert( min(self.gsIndex.values()) >= 0)

    if self.slIndex is None: 
      self.slIndex = dataset.slIndex
      if len(self.slIndex) > 0:
        assert( min(self.slIndex.values()) >= 0)


  def addDatasetCounts(self, datasetName, datasetCounts):
    """ 
    Directly add a full set of counts for a specified dataset.

    Parameters
    ----------
    datasetName : string
        Counts are added for this data set.  This can be a new name, in
        which case this method adds a new data set to the MultiDataSet.

    datasetCounts: numpy array
        A 2D array with rows = gate strings and cols = spam labels, to this
        MultiDataSet.  The shape of dataSetCounts is checked for compatibility.
    """
    
    if self.gsIndex:  #Note: tests if not none and nonempty
        maxIndex = max(self.gsIndex.values())
        assert( datasetCounts.shape[0] > maxIndex and datasetCounts.shape[1] == len(self.slIndex) )
    self.countsDict[datasetName] = dataset.counts

  def __str__(self):
    s  = "MultiDataSet containing: %d datasets, each with %d strings\n" % (len(self), len(self.gsIndex) if self.gsIndex is not None else 0)
    s += " Dataset names = " + ", ".join(self.keys()) + "\n"
    s += " SPAM labels = " + ", ".join(self.slIndex.keys() if self.slIndex is not None else [])
    if self.gsIndex is not None:
       s += "\nGate strings: \n" + "\n".join( map(str,self.gsIndex.keys()) )
    return s + "\n"


  def copy(self):
    """ Make a copy of this MultiDataSet """
    return MultiDataSet(self.countsDict, gateStringIndices=self.gsIndex, spamLabelIndices=self.slIndex)


  def __getstate__(self):
    toPickle = { 'gsIndexKeys': map(_ds.compressGateLabelTuple, self.gsIndex.keys() if self.gsIndex else []),
                 'gsIndexVals': self.gsIndex.values() if self.gsIndex else [],
                 'slIndex': self.slIndex,
                 'countsDict': self.countsDict }
    return toPickle

  def __setstate__(self, state_dict):
    self.gsIndex = _OrderedDict( zip( map(_ds.expandGateLabelTuple, state_dict['gsIndexKeys']), state_dict['gsIndexVals']) )
    self.slIndex = state_dict['slIndex']
    self.countsDict = state_dict['countsDict']

  def save(self, fileOrFilename):
    """ 
    Save this MultiDataSet to a file.

    Parameters
    ----------
    fileOrFilename : file or string
        Either a filename or a file object.  In the former case, if the
        filename ends in ".gz", the file will be gzip compressed.
    """

    toPickle = { 'gsIndexKeys': map(_ds.compressGateLabelTuple, self.gsIndex.keys() if self.gsIndex else []),
                 'gsIndexVals': self.gsIndex.values() if self.gsIndex else [],
                 'slIndex': self.slIndex,
                 'countsKeys': self.countsDict.keys() }  #Don't pickle countsDict numpy data b/c it's inefficient
    
    bOpen = (type(fileOrFilename) == str)
    if bOpen:
        if fileOrFilename.endswith(".gz"):
            import gzip as _gzip
            f = _gzip.open(fileOrFilename,"wb")
        else:
            f = open(fileOrFilename,"wb")
    else: 
        f = fileOrFilename

    _pickle.dump(toPickle,f)
    for key,data in self.countsDict.iteritems():
        _np.save(f, data)
    if bOpen: f.close()


  def load(self, fileOrFilename):
    """
    Load MultiDataSet from a file, clearing any data is contained previously.
    
    Parameters
    ----------
    fileOrFilename : file or string
        Either a filename or a file object.  In the former case, if the
        filename ends in ".gz", the file will be gzip uncompressed as it is read.
    """
    bOpen = (type(fileOrFilename) == str)
    if bOpen:
        if fileOrFilename.endswith(".gz"):
            import gzip as _gzip
            f = _gzip.open(fileOrFilename,"rb")
        else:
            f = open(fileOrFilename,"rb")
    else: 
        f = fileOrFilename

    state_dict = _pickle.load(f)
    self.gsIndex = _OrderedDict( zip( map(_ds.expandGateLabelTuple, state_dict['gsIndexKeys']), state_dict['gsIndexVals']) )
    self.slIndex = state_dict['slIndex']
    self.countsDict = _OrderedDict()
    for key in state_dict['countsKeys']:
        self.countsDict[key] = _np.lib.format.read_array(f) #np.load(f) doesn't play nice with gzip
    if bOpen: f.close()
