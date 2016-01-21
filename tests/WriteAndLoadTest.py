import unittest
import pygsti
from pygsti.construction import std1Q_XYI as std
import numpy as np

class WriteAndLoadTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def assertArraysAlmostEqual(self,a,b):
        self.assertAlmostEqual( np.linalg.norm(a-b), 0 )


class TestWriteAndLoad(WriteAndLoadTestCase):

    def test_paramfile(self):
        d = {'a': 1, 'b': 2 }
        pygsti.io.write_parameter_file("temp_test_files/paramFile.json", d)
        d2 = pygsti.io.load_parameter_file("temp_test_files/paramFile.json")
        self.assertEqual(d,d2)

    def test_dataset_file(self):

        strList = pygsti.construction.gatestring_list( [(), ('Gx',), ('Gx','Gy') ] )
        weighted_strList = [ pygsti.obj.WeightedGateString((), weight=0.1), 
                             pygsti.obj.WeightedGateString(('Gx',), weight=2.0),
                             pygsti.obj.WeightedGateString(('Gx','Gy'), weight=1.5) ]
        pygsti.io.write_empty_dataset("temp_test_files/emptyDataset.txt", strList, numZeroCols=2, appendWeightsColumn=False)
        pygsti.io.write_empty_dataset("temp_test_files/emptyDataset2.txt", weighted_strList, 
                                  headerString='## Columns = myplus count, myminus count', appendWeightsColumn=True)

        with self.assertRaises(ValueError):
            pygsti.io.write_empty_dataset("temp_test_files/emptyDataset.txt", [ ('Gx',) ], numZeroCols=2) #must be GateStrings
        with self.assertRaises(ValueError):
            pygsti.io.write_empty_dataset("temp_test_files/emptyDataset.txt", strList, headerString="# Nothing ")
              #must give numZeroCols or meaningful header string (default => 2 cols)

        
        ds = pygsti.obj.DataSet(spamLabels=['plus','minus'])
        ds.add_count_dict( ('Gx',), {'plus': 10, 'minus': 90} )
        ds.add_count_dict( ('Gx','Gy'), {'plus': 40, 'minus': 60} )
        ds.done_adding_data()

        pygsti.io.write_dataset("temp_test_files/dataset_loadwrite.txt",
                                     pygsti.construction.gatestring_list(ds.keys())[0:10], ds) #write only first 10 strings
        ds2 = pygsti.io.load_dataset("temp_test_files/dataset_loadwrite.txt")
        ds3 = pygsti.io.load_dataset("temp_test_files/dataset_loadwrite.txt", cache=True) #creates cache file
        ds4 = pygsti.io.load_dataset("temp_test_files/dataset_loadwrite.txt", cache=True) #loads from cache file

        pygsti.io.write_dataset("temp_test_files/dataset_loadwrite.txt",
                                     pygsti.construction.gatestring_list(ds.keys()), ds, spamLabelOrder=['plus','minus'])
        ds5 = pygsti.io.load_dataset("temp_test_files/dataset_loadwrite.txt", cache=True) #rewrites cache file

        for s in ds:
            self.assertEqual(ds[s]['plus'],ds5[s]['plus'])
            self.assertEqual(ds[s]['minus'],ds5[s]['minus'])

        with self.assertRaises(ValueError):
            pygsti.io.write_dataset("temp_test_files/dataset_loadwrite.txt",ds.keys(), ds) #must be GateStrings
        with self.assertRaises(ValueError):
            pygsti.io.write_dataset("temp_test_files/dataset_loadwrite.txt",ds.keys(), ds) #must be GateStrings


    def test_multidataset_file(self):
        strList = pygsti.construction.gatestring_list( [(), ('Gx',), ('Gx','Gy') ] )
        pygsti.io.write_empty_dataset("temp_test_files/emptyMultiDataset.txt", strList,
                                           headerString='## Columns = ds1 plus count, ds1 minus count, ds2 plus count, ds2 minus count')

        multi_dataset_txt = \
"""## Columns = DS0 plus count, DS0 minus count, DS1 plus frequency, DS1 count total
{} 0 100 0 100
Gx 10 90 0.1 100
GxGy 40 60 0.4 100
Gx^4 20 80 0.2 100
"""
        open("temp_test_files/TestMultiDataset.txt","w").write(multi_dataset_txt)


        ds = pygsti.io.load_multidataset("temp_test_files/TestMultiDataset.txt")
        ds2 = pygsti.io.load_multidataset("temp_test_files/TestMultiDataset.txt", cache=True)
        ds3 = pygsti.io.load_multidataset("temp_test_files/TestMultiDataset.txt", cache=True) #load from cache

        pygsti.io.write_multidataset("temp_test_files/emptyMultiDataset2.txt", strList, ds)
        ds_copy = pygsti.io.load_multidataset("temp_test_files/emptyMultiDataset2.txt")
        self.assertEqual(ds_copy['DS0'][('Gx',)]['plus'], ds['DS0'][('Gx',)]['plus'] )
        self.assertEqual(ds_copy['DS0'][('Gx','Gy')]['minus'], ds['DS1'][('Gx','Gy')]['minus'] )


    def test_gatestring_list_file(self):
        strList = pygsti.construction.gatestring_list( [(), ('Gx',), ('Gx','Gy') ] )
        pygsti.io.write_gatestring_list("temp_test_files/gatestringlist_loadwrite.txt", strList, "My Header")
        strList2 = pygsti.io.load_gatestring_list("temp_test_files/gatestringlist_loadwrite.txt")
        pythonStrList = pygsti.io.load_gatestring_list("temp_test_files/gatestringlist_loadwrite.txt", readRawStrings=True)
        self.assertEqual(strList, strList2)
        self.assertEqual(pythonStrList[2], 'GxGy')

        with self.assertRaises(ValueError):
            pygsti.io.write_gatestring_list("temp_test_files/gatestringlist_bad.txt", [ ('Gx',)], "My Header") #Must be GateStrings


    def test_gatestring_list_file(self):
        strList = pygsti.construction.gatestring_list( [(), ('Gx',), ('Gx','Gy') ] )
        pygsti.io.write_gatestring_list("temp_test_files/gatestringlist_loadwrite.txt", strList, "My Header")
        strList2 = pygsti.io.load_gatestring_list("temp_test_files/gatestringlist_loadwrite.txt")
        self.assertEqual(strList, strList2)

        
    def test_gateset_file(self):
        pygsti.io.write_gateset(std.gs_target, "temp_test_files/gateset_loadwrite.txt", "My title")
        gs = pygsti.io.load_gateset("temp_test_files/gateset_loadwrite.txt")
        self.assertAlmostEqual(gs.frobeniusdist(std.gs_target), 0)

        gateset_m1m1 = pygsti.construction.build_gateset([2], [('Q0',)],['Gi','Gx','Gy'], 
                                                         [ "I(Q0)","X(pi/2,Q0)", "Y(pi/2,Q0)"],
                                                         rhoExpressions=["0"], EExpressions=["1"], 
                                                         spamLabelDict={'plus': (0,0), 'minus': (-1,-1) })
        pygsti.io.write_gateset(gateset_m1m1, "temp_test_files/gateset_m1m1_loadwrite.txt", "My title m1m1")
        gs_m1m1 = pygsti.io.load_gateset("temp_test_files/gateset_m1m1_loadwrite.txt")
        self.assertAlmostEqual(gs_m1m1.frobeniusdist(gateset_m1m1), 0)

        gateset_txt = """# Gateset file using other allowed formats
rho0
StateVec
1 0

rho1
DensityMx
0 0
0 1

E
StateVec
0 1

Gi
UnitaryMx
 1 0
 0 1

Gx
UnitaryMxExp
 0    pi/4
pi/4   0

Gy
UnitaryMxExp
 0       -1j*pi/4
1j*pi/4    0

Gx2
UnitaryMx
 0  1
 1  0

Gy2
UnitaryMx
 0   -1j
1j    0


IDENTITYVEC sqrt(2) 0 0 0
SPAMLABEL plus0 = rho0 E
SPAMLABEL plus1 = rho1 E
SPAMLABEL minus = remainder
"""
        open("temp_test_files/formatExample.gateset","w").write(gateset_txt)
        gs_formats = pygsti.io.load_gateset("temp_test_files/formatExample.gateset")
        #print gs_formats

        rotXPi   = pygsti.construction.build_gate( [2],[('Q0',)], "X(pi,Q0)").matrix
        rotYPi   = pygsti.construction.build_gate( [2],[('Q0',)], "Y(pi,Q0)").matrix
        rotXPiOv2   = pygsti.construction.build_gate( [2],[('Q0',)], "X(pi/2,Q0)").matrix        
        rotYPiOv2   = pygsti.construction.build_gate( [2],[('Q0',)], "Y(pi/2,Q0)").matrix        

        self.assertArraysAlmostEqual(gs_formats['Gi'], np.identity(4,'d'))
        self.assertArraysAlmostEqual(gs_formats['Gx'], rotXPiOv2)
        self.assertArraysAlmostEqual(gs_formats['Gy'], rotYPiOv2)
        self.assertArraysAlmostEqual(gs_formats['Gx2'], rotXPi)
        self.assertArraysAlmostEqual(gs_formats['Gy2'], rotYPi)

        self.assertArraysAlmostEqual(gs_formats.rhoVecs[0], 1/np.sqrt(2)*np.array([[1],[0],[0],[-1]],'d'))
        self.assertArraysAlmostEqual(gs_formats.rhoVecs[1], 1/np.sqrt(2)*np.array([[1],[0],[0],[1]],'d'))
        self.assertArraysAlmostEqual(gs_formats.EVecs[0], 1/np.sqrt(2)*np.array([[1],[0],[0],[-1]],'d'))

        #pygsti.print_mx( rotXPi )
        #pygsti.print_mx( rotYPi )
        #pygsti.print_mx( rotXPiOv2 )
        #pygsti.print_mx( rotYPiOv2 )



        
    def test_gatestring_dict_file(self):
        file_txt = "# Gate string dictionary\nF1 GxGx\nF2 GxGy"  #TODO: make a Writers function for gate string dicts
        open("temp_test_files/gatestringdict_loadwrite.txt","w").write(file_txt)

        d = pygsti.io.load_gatestring_dict("temp_test_files/gatestringdict_loadwrite.txt")
        self.assertEqual( tuple(d['F1']), ('Gx','Gx'))

        


if __name__ == "__main__":
    unittest.main(verbosity=2)

    
