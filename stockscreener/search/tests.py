
from django.test import TestCase
import unittest, datetime

from decimal import Decimal
from models import StockProperty, StockPropertyValue, Company, Sector, StockPropertyValueHistory
from extractor import Extractor, SymbolsClient
from DistrGraph import GraphHelper, GroupedValue
from forms import SearchForm
import StringIO
from search import query, MinMaxCriteria

#
# Build a test company to work with
#
def build_test_company(symbol='TEST', sector='Toilet equipment'):
    try:
        s = Sector.objects.get(name=sector)
    except Sector.DoesNotExist:
        s = Sector(name=sector)
        s.save()

    c = Company(name='Test A/S',symbol=symbol,
                reuters_symbol_guess='TEST.CO',
                currency='DKK',
                exchange='CSE',
                size='S',
                isin='DK012346699',
                sector=s)
    c.save()
    return s, c

def build_test_property(name='Test'):
        sp = StockProperty(name=name,url='http://www.google.com',xml_path='.//title',convert_expression='10')
        sp.save()
        return sp

def build_test_value(company, property, value):
    v = StockPropertyValue(symbol=company, stock_property=property, value=Decimal(str(value)))
    v.save()
    return v

class Task_21_Test(unittest.TestCase):

    def setUp(self):
        self.s, self.c = build_test_company('TEST', 'Oil')
        self.p = build_test_property('PERatio')
        self.p.convert_expression = 'x'

    def tearDown(self):
        self.p.delete()
        self.c.delete()
        self.s.delete()

    def testSavingHistory(self):
        def download1(url):
            return "<title>123</title>"

        def download2(url):
            return "<title>321</title>"

        def download3(url):
            return "<title>456</title>"

        e = Extractor()
        e.download = download1
        e.extract(self.c, self.p)
        v = StockPropertyValue.objects.get(stock_property=self.p)
        print "v", v
        self.assertEquals(1, StockPropertyValueHistory.objects.filter(current_value=v).count())

        e = Extractor()
        e.download = download2
        e.extract(self.c, self.p)
        v = StockPropertyValue.objects.get(stock_property=self.p)
        print "v", v
        self.assertEquals(2, StockPropertyValueHistory.objects.filter(current_value=v).count())

        e = Extractor()
        e.extract(self.c, self.p)
        v = StockPropertyValue.objects.get(stock_property=self.p)
        print "v", v
        self.assertEquals(2, StockPropertyValueHistory.objects.filter(current_value=v).count())

        e = Extractor()
        e.download = download3
        e.extract(self.c, self.p)
        v = StockPropertyValue.objects.get(stock_property=self.p)
        print "v", v
        self.assertEquals(3, StockPropertyValueHistory.objects.filter(current_value=v).count())


class Task_20_test(unittest.TestCase):

    def setUp(self):
        self.s, self.c = build_test_company('TEST', 'Oil')
        self.p = build_test_property('PE/Ratio')
        self.v = build_test_value(self.c, self.p, '10.0')

    def tearDown(self):
        self.v.delete()
        self.p.delete()
        self.c.delete()
        self.s.delete()

    def testHistoryExists(self):
        
        h = StockPropertyValueHistory(current_value = self.v,
                                      historical_value = Decimal('11.1'),
                                      historical_date = datetime.date.today())

        h.save()

        self.assertEquals(1, StockPropertyValueHistory.objects.all().count())
        self.assertEquals(1, StockPropertyValue.objects.get(id=self.v.id).stockpropertyvaluehistory_set.all().count())

        h.delete()

        self.assertEquals(0, StockPropertyValue.objects.get(id=self.v.id).stockpropertyvaluehistory_set.all().count())


class Task_19_Test(unittest.TestCase):

    def testSearchFormSubmittingCorrect(self):

        from django.test.client import Client

        c = Client()

        page = c.get('/search/')
        self.assertEquals(200, page.status_code)

        self.assertTrue('action="/search/result/"' in page.content)

class Task_18_Test(unittest.TestCase):

    def setUp(self):

        # build companies
        self.s1, self.c1 = build_test_company('TEST1', 'Oil')
        self.s2, self.c2 = build_test_company('TEST2', 'Gold')

        # build properties
        self.p1 = build_test_property('PE/Ratio')
        self.p2 = build_test_property('SharesOut')

        self.v1 = build_test_value(self.c1, self.p1, '10.0')
        self.v2 = build_test_value(self.c1, self.p2, '10000')
        self.v3 = build_test_value(self.c2, self.p1, '15.0')
        self.v4 = build_test_value(self.c2, self.p2, '5000')

    def tearDown(self):
        # clear database again
        self.v1.delete()
        self.v2.delete()
        self.v3.delete()
        self.v4.delete()
        self.p1.delete()
        self.p2.delete()
        self.c1.delete()
        self.c2.delete()
        self.s1.delete()
        self.s2.delete()
    
    def testResultView_all(self):
        from django.test.client import Client

        c = Client()

        page = c.post('/search/result/', {('min[%d]' % self.p1.id): '10',
                                          ('max[%d]' % self.p1.id): '14',
                                          'show_result': 'all'})


        self.assertEquals(200, page.status_code)

        print "content", page.content

        self.assertTrue('TEST1' in page.content)
        self.assertFalse('TEST2' in page.content)
        self.assertTrue(self.p1.name in page.content)
        self.assertTrue(self.p2.name in page.content)


    def testResultView_criteria(self):
        from django.test.client import Client

        c = Client()

        page = c.post('/search/result/', {('min[%d]' % self.p1.id): '10',
                                          ('max[%d]' % self.p1.id): '14',
                                          'show_result': 'criteria'})


        self.assertEquals(200, page.status_code)

        print "content", page.content

        self.assertTrue('TEST1' in page.content)
        self.assertFalse('TEST2' in page.content)
        self.assertTrue(self.p1.name in page.content)
        self.assertFalse(self.p2.name in page.content)

class Task_17_Test(unittest.TestCase):

    def setUp(self):

        # build companies
        self.s1, self.c1 = build_test_company('TEST1', 'Oil')
        self.s2, self.c2 = build_test_company('TEST2', 'Gold')

        # build properties
        self.p1 = build_test_property('PE/Ratio')
        self.p2 = build_test_property('SharesOut')

        self.v1 = build_test_value(self.c1, self.p1, '10.0')
        self.v2 = build_test_value(self.c1, self.p2, '10000')
        self.v3 = build_test_value(self.c2, self.p1, '15.0')
        self.v4 = build_test_value(self.c2, self.p2, '5000')

    def tearDown(self):
        # clear database again
        self.v1.delete()
        self.v2.delete()
        self.v3.delete()
        self.v4.delete()
        self.p1.delete()
        self.p2.delete()
        self.c1.delete()
        self.c2.delete()
        self.s1.delete()
        self.s2.delete()

    def testQuery_No_Sector_Exchange(self):

        # this should not match any rows in test data.
        c = ( MinMaxCriteria(self.p1.id, Decimal("1000"), None), 
              MinMaxCriteria(self.p2.id, None, Decimal("10")) )

        print "c", c
        h, res = query(c)
        print "res", res
        self.assertEquals(0, len(res))

    def testQuery_One_Criteria_Two_Matches(self):

        # should match both companies, one criteria
        c = ( MinMaxCriteria(self.p1.id, Decimal("10.0"), Decimal("15.0")), )

        print "c", c

        h, res = query(c)

        print "res", res

        self.assertEquals(2, len(res))

    def testQuery_One_Criteria_One_Matches(self):

        # should match one company, one criteria
        c = ( MinMaxCriteria(self.p1.id, Decimal("10.0"), Decimal("14.9")), )
        h, res = query(c)
        self.assertEquals(1, len(res))

    def testQuery_More_Criteria_All_Matches(self):

        # should match two company, two criteria
        c = ( MinMaxCriteria(self.p1.id, Decimal("10.0"), Decimal("15.0")), 
              MinMaxCriteria(self.p2.id, Decimal("1"), Decimal("100000") ) )
        h, res = query(c)
        self.assertEquals(2, len(res))

    def testQuery_More_Criteria_One_Matches(self):

        # should match one company, two criteria
        c = ( MinMaxCriteria(self.p1.id, Decimal("10.0"), Decimal("15.0")), 
              MinMaxCriteria(self.p2.id, Decimal("1"), Decimal("100000") ))
        h, res = query(c)
        self.assertEquals(2, len(res))

    def testQuery_More_Criteria_Open_Intervals(self):

        c = ( MinMaxCriteria(self.p1.id, Decimal("10.0"), None), 
              MinMaxCriteria(self.p2.id, None, Decimal("100000") ) )
        h, res = query(c)
        self.assertEquals(2, len(res))

        c = ( MinMaxCriteria(self.p1.id, None, Decimal("15.0")), 
              MinMaxCriteria(self.p2.id, Decimal("1.0"), None ) )
        h, res = query(c)
        self.assertEquals(2, len(res))

        # check less more than 11.0 one company matches
        c = ( MinMaxCriteria(self.p1.id, Decimal("11.0"), None), )
        h, res = query(c)
        self.assertEquals(1, len(res))

        # check less less than 14.0 one company matches
        c = ( MinMaxCriteria(self.p1.id, None, Decimal("14.0")), )
        h, res = query(c)
        self.assertEquals(1, len(res))

        # check less less than 14.0 one company matches
        c = ( MinMaxCriteria(self.p1.id, None, Decimal("14.0")), 
              MinMaxCriteria(self.p2.id, None, Decimal("100000") ) )
        h, res = query(c)
        self.assertEquals(1, len(res))

        # check less less than 14.0 less than 6000, no company matches
        c = ( MinMaxCriteria(self.p1.id, None, Decimal("14.0")), 
              MinMaxCriteria(self.p2.id, None, Decimal("6000") ) )
        h, res = query(c)
        self.assertEquals(0, len(res))

class Task_16_Test(unittest.TestCase):
    """
    Task 16 is refactored into the other test cases that needed to be adjusted
    by the refactoring.
    """

    def testNothing(self):
        pass

class Task_15_Test(unittest.TestCase):

    def setUp(self):
        self.s, self.c = build_test_company()
        self.p = build_test_property('ThePropertyName')
        self.v1 = build_test_value(self.c, self.p, '10.1')
        self.v2 = build_test_value(self.c, self.p, '15.2')

    def tearDown(self):
        self.v1.delete()
        self.v2.delete()
        self.p.delete()
        self.c.delete()
        self.s.delete()

    def testView(self):

        from django.test.client import Client
        c = Client()

        page = c.get('/search/criteria/%d/' % self.p.id)

        # check the page looks as expected
        self.assertEquals(200, page.status_code)
        self.assertTrue('10.1' in page.content)
        self.assertTrue('15.2' in page.content)
        self.assertTrue('ThePropertyName' in page.content)

        self.assertTrue(('min[%d]' % self.p.id) in page.content)
        self.assertTrue(('max[%d]' % self.p.id) in page.content)

class Task_14_Test(unittest.TestCase):

    def testSearchForm(self):

        d = {
            'sector': 1,
            'min[1]': '1.5',
            'max[1]': '5.4',
            'min[10]': '10000000'
        }

        f = SearchForm(d)

        f.find_minmax_criteria(d)

        # self.assertEquals(1, f.cleaned_data['sector'])

        c = f.to_criteria()

        self.assertEquals(2, len(c))

    def testSearchFormView(self):

        from django.test.client import Client

        c = Client()

        page = c.get('/search/')
        self.assertEquals(200, page.status_code)

        self.assertTrue('Search now' in page.content)


#class Task_13_Test(unittest.TestCase):

#    def testUpdateSymbolsCommand(self):

#        from django.core.management import call_command

        # run the command
#        call_command('updatesymbols')

        # check that we got atleast 100 values
#        self.assertTrue(100 < Company.objects.all().count())

#        self.assertTrue(1 == Company.objects.filter(symbol='TDC').count())


#class Task_12_Test(unittest.TestCase):
#
#    def testLoadSymbols(self):

        # instantiate new symbolsclient object
 #       s = SymbolsClient()

        # try to load all symbols from Freyr into database
 #       s.load_symbols()

        # get all symbols in the database
 #       symbols = Company.objects.all()

 #       print symbols

        # there has to be more than 50 symbols in the list we got from database.
 #       self.assertTrue(len(symbols) > 50)

        # there has to be atleast 10 sectors
 #       self.assertTrue(len(Sector.objects.all()) >= 10)

class Task_11_Test(unittest.TestCase):

    def setUp(self):
        sp = StockProperty(name='Test',url='http://www.google.com',xml_path='.//title',convert_expression='10')
        sp.save()
        self.sp = sp

    def tearDown(self):
        self.sp.delete()

#    def testExtractCommand(self):

#        from django.core.management import call_command

        # run the command
#        call_command('importall', '5')

        # check that we got one value now.
#        self.assertEquals(5, StockPropertyValue.objects.all().count())


class Task_10_Test(unittest.TestCase):

#    def testLoadSymbolsReal(self):
        # create instance of SymbolsClient class
#        sc = SymbolsClient()

        # get the symbols
#        sc.load_symbols()

#        result = Company.objects.all()

        # check that we have atleast 10 symbols in the result
#        self.assertTrue(len(result) > 10)

#        symbols = [ r.reuters_symbol_guess for r in result ]

        # check that TDC is part of the symbols
#        self.assertTrue("TDC.CO" in symbols)

    def testGetParseSymbols_No_Network(self):

        def get_fake():
            xml = """<companies>
<company>
    <name>Autoliv Inc. SDB</name><currency>SEK</currency><exchange>STO</exchange><size>LARGE</size><sector>Consumer Discretionary</sector><symbol>ALIVa SDB</symbol><isin>SE0000382335</isin><reuters-symbol-guess>TEST.CO</reuters-symbol-guess>
</company>
<company>
    <name>Autoliv Inc. SDB</name><currency>SEK</currency><exchange>STO</exchange><size>LARGE</size><sector>Consumer Discretionary</sector><symbol>ALIVb SDB</symbol><isin>SE0000382335</isin><reuters-symbol-guess>TESTb.HE</reuters-symbol-guess>
</company>
</companies>"""
            print "Returning test XML", xml
            return StringIO.StringIO(xml)

        # create symbols client, set the download method to our fake method
        sc = SymbolsClient()
        sc.get_document_fd = get_fake

        sc.load_symbols()

        result = Company.objects.all()

        self.assertEquals(2, len(result))

        symbols = [ r.reuters_symbol for r in result ]
        
        self.assertTrue('TEST.CO' in symbols)
        self.assertTrue('TESTb.HE' in symbols)


class Task_09_Test(unittest.TestCase):

    def setUp(self):
        self.s, self.c = build_test_company()
        sp = StockProperty(name='Test',url='http://www.google.com',xml_path='.//title',convert_expression='10')
        sp.save()
        self.sp = sp

    def tearDown(self):
        self.sp.delete()
        self.c.delete()
        self.s.delete()

    def testExtractCommand(self):

        from django.core.management import call_command

        # run the command
        call_command('importone', self.c.symbol)

        # check that we got one value now.
        self.assertEquals(1, StockPropertyValue.objects.all().count())


class Task_08_Test(unittest.TestCase):

    def setUp(self):
        # create stock property for testing
        sp = StockProperty(name='Shares Out',url='http://www.google.com',xml_path='//test',convert_expression='x')
        sp.save()

        self.s, self.c = build_test_company()

        # create and save some values
        StockPropertyValue(stock_property = sp, symbol=self.c, value=1000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=2000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=3000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=4000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=5000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=6000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=7000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=8000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=9000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=0).save()

        self.sp = sp

    def tearDown(self):
        # delete all values
        for o in StockPropertyValue.objects.all():
            o.delete()
        # delete all properties
        for o in StockProperty.objects.all():
            o.delete()

        self.c.delete()
        self.s.delete()

    def testView(self):

        from views import distrgraph
        from django.http import HttpResponseRedirect

        # execute the view
        response = distrgraph(None, self.sp.id)

        # check we got http response redirect response
        self.assertTrue(isinstance(response, HttpResponseRedirect))

        # check the location is for charts
        loc = response['Location']
        self.assertTrue(loc.startswith('http://chart.apis.google.com'))
        

class Task_07_Test(unittest.TestCase):

    def testCreateGraphUrl(self):

        g = GraphHelper()

        data = ( GroupedValue(10, Decimal("0"), Decimal("1")),
                 GroupedValue(5, Decimal("1"), Decimal("2")),
                 GroupedValue(0, Decimal("2"), Decimal("3")),
                 GroupedValue(4, Decimal("3"), Decimal("4")),
                 GroupedValue(10, Decimal("4"), Decimal("5")) )

        url = g.create_graph_url(data, 0, 10, 220, 75)

        # check that the url is for google chart api
        self.assertTrue(url.startswith('http://chart.apis.google.com/chart?'))

        # check that the size is correct
        url.index('220x75')
        url.index('t:10,5,0,4,10')

    def testComplexGraph(self):

        g = GraphHelper()

        # create some random data.
        data = []
        fixed = []
        import random
        for i in range(100):
            v = random.randint(1, 50)
            fixed.append(str(v))
            data.append(GroupedValue(v, Decimal(str(i)), Decimal(str(i+1))))

        url = g.create_graph_url(data, 1, 50, 220, 75)

        self.assertTrue(url.startswith('http://chart.apis.google.com/chart?'))
        url.index(','.join(fixed))        

class Task_06_Test(unittest.TestCase):

    sp = None
    
    def setUp(self):

        self.s, self.c = build_test_company()
        
        # create stock property for testing
        sp = StockProperty(name='Shares Out',url='http://www.google.com',xml_path='//test',convert_expression='x')
        sp.save()

        # create and save some values
        StockPropertyValue(stock_property = sp, symbol=self.c, value=1000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=2000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=3000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=4000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=5000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=6000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=7000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=8000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=9000).save()
        StockPropertyValue(stock_property = sp, symbol=self.c, value=0).save()

        self.sp = sp

    def tearDown(self):
        # delete all values
        for o in StockPropertyValue.objects.all():
            o.delete()
        # delete all properties
        for o in StockProperty.objects.all():
            o.delete()

        self.c.delete()
        self.s.delete()

    def testCreateData(self):

        g = GraphHelper()

        data, y_min, y_max = g.create_data(1, 10, self.sp.id)

        self.assertEquals(10, y_min)
        self.assertEquals(10, y_max)
        self.assertEquals(1, len(data))

    def testCreateData_2_Points(self):

        g = GraphHelper()

        data, y_min, y_max = g.create_data(2, 10, self.sp.id)
        self.assertEquals(5, y_min)
        self.assertEquals(5, y_max)

        self.assertEquals(2, len(data))

    def testCreateData_10_Points(self):

        g = GraphHelper()

        data, y_min, y_max = g.create_data(10, 10, self.sp.id)
        self.assertEquals(1, y_min)
        self.assertEquals(1, y_max)

        self.assertEquals(10, len(data))

#
# Test for TNo=3
# Test that the models are initialized
#
class Task_03_Test(TestCase):

    fixtures = ['stock_properties.json']
    s = None

    def setUp(self):
        self.s, self.c = build_test_company()
        self.c.reuters_symbol_ok = 'TDC.CO'
        self.c.save()
        
    def tearDown(self):
        self.c.delete()
        self.s.delete()
    
    def testModelsExists(self):
        sps = StockProperty.objects.filter(url__startswith='http://www.reuters.com')
        self.assertEquals(3, len(sps))

    def testModelsWorking(self):

        sps = StockProperty.objects.filter(url__startswith='http://www.reuters.com')

        for sp in sps:
            print "Testing", sp
            Extractor().extract(self.c,sp)

        alist = StockPropertyValue.objects.all()
        print "list,length", len(alist)
        spvs = StockPropertyValue.objects.filter(symbol=self.c)
        self.assertEquals(3, len(spvs))

#
# Test for TNo=5
# Tests the extractor module functionality
#
class Task_05_Test(unittest.TestCase):

    o = None

    # setUp is running before each test
    def setUp(self):
        self.o = StockProperty(name="test", url="http://www.google.com/",
                              xml_path=".//title", convert_expression="int(x)")
        self.o.save()
        self.s = Sector(name='Toilet equipment')
        self.s.save()
        self.c = Company(name='Test A/S',symbol='TEST',
                         reuters_symbol_guess='TEST.CO',
                         currency='DKK',
                         exchange='CSE',
                         size='S',
                         isin='DK012346699',
                         sector=self.s)
        self.c.save()

    # tearDown is running after each test (fail or not)
    def tearDown(self):
        self.o.delete()
        self.c.delete()
        self.s.delete()

    def testDownload(self):
        ex = Extractor()
        a = ex.download('http://www.google.com/')
        google = "<title>Google</title>"
        a.index(google)

    def testExecuteXpath(self):
        ex = Extractor()
        # setup the html document (so we know it dont need to download a file)
        a=ex.execute_xpath('<html><head><title>Google</title></head><body>Hello</body></html>',
                           './/title')
        self.assertEquals("Google", a)

    def testConvertExpression(self):
        ex = Extractor()
        val = ex.execute_converter('10',self.o)
        self.assertEquals(10, val)

        # try with SSI conversion
        self.o.convert_expression = "SSI(x)"
        ex = Extractor()
        val = ex.execute_converter('10M',self.o)
        self.assertTrue(1000000 - val < 1)

    def testSaveDatabase(self):
        # extract a value (it should save)
        ex = Extractor()
        self.o.convert_expression = '101'
        val = ex.extract(self.c,self.o)
        self.assertEquals(101, val.value)
        self.assertEquals(self.c, val.symbol)

        # lookup values in database
        values = StockPropertyValue.objects.filter(stock_property = self.o)
        # there should be one value
        self.assertEquals(1, len(values))
        # get this value
        value = values[0]
        # check that the value is 10
        self.assertEquals(101, value.value)
        # check that the symbol is tdc.co
        self.assertEquals(self.c , value.symbol)


    # this test checks that if we extract the same symbol twice, then still
    # only one object should be in the database.
    def testSaveDatabase_02(self):
        ex = Extractor()
        self.o.convert_expression = '101'
        val = ex.extract(self.c,self.o)
        self.assertEquals(101, val.value)
        self.assertEquals(self.c, val.symbol)

        # there should be one value
        self.assertEquals(1, StockPropertyValue.objects.filter(stock_property = self.o).count())
        
        val = ex.extract(self.c,self.o)
        self.assertEquals(101, val.value)
        self.assertEquals(self.c, val.symbol)

        # there should STILL be one value
        self.assertEquals(1, StockPropertyValue.objects.filter(stock_property = self.o).count())
        
#
# Test for Task 2
# Stock property model
#
class StockPropertyTest(unittest.TestCase):

    def testInstantiation(self):
        from models import StockProperty
        o=StockProperty()

    def testCrud(self):
        from models import StockProperty
        # check that database is empty
        ol = StockProperty.objects.filter(name="test")
        self.assertEquals(0, len(ol))

        # create one object and save to datbase        
        o = StockProperty(name="test", url="http://google.com",xml_path="test path", convert_expression="convert")
        o.save()

        # show the id just for ourself
        print o.id

        # read from database
        o2 = StockProperty.objects.get(id=o.id)
        self.assertEquals("test", o2.name)
        self.assertEquals("http://google.com", o2.url)
        self.assertEquals("test path", o2.xml_path)
        self.assertEquals("convert", o2.convert_expression)
        
        # update object and save to datbase
        o2.name = "test2"
        o2.url = "http://www.yani.dk/"
        o2.xml_path = "//hej"
        o2.convert_expression = "blab"
        o2.save()

        # compare objects
        o3 = StockProperty.objects.get(id=o2.id)
        self.assertEquals(o.id, o3.id)
        self.assertEquals("test2", o3.name)
        self.assertEquals("http://www.yani.dk/", o3.url)
        self.assertEquals("//hej", o3.xml_path)
        self.assertEquals("blab", o3.convert_expression)
        
        # delete
        o3.delete()

        ol = StockProperty.objects.filter(name="test2")
        self.assertEquals(0, len(ol))


# Test for Task number 4.        
class StockPropertyValueTest(unittest.TestCase):

    c = None
    c2 = None
    s = None

    def setUp(self):
        self.s = Sector(name='Toilet equipment')
        self.s.save()
        self.c = Company(name='Test A/S',symbol='TEST',
                         reuters_symbol_guess='TEST.CO',
                         currency='DKK',
                         exchange='CSE',
                         size='S',
                         isin='DK012346699',
                         sector=self.s)
        self.c.save()

        self.c2 = Company(name='Test 2 Aps',symbol='TEST2',
                         reuters_symbol_guess='TEST2.CO',
                         currency='DKK',
                         exchange='CSE',
                         size='S',
                         isin='DK012346698',
                         sector=self.s)
        self.c2.save()
        

    def tearDown(self):
        self.c.delete()
        self.c2.delete()
        self.s.delete()

    def testInstantiation(self):
        from models import StockPropertyValue
        o=StockPropertyValue()

    def testCrud(self):
        from models import StockPropertyValue, StockProperty

        # check that database is empty
        ol = StockPropertyValue.objects.filter(symbol=self.c)
        self.assertEquals(0, len(ol))

		# create stock property
        s = StockProperty(name="test", url="http://google.com",xml_path="test path", convert_expression="convert")
        s.save()

        # create one object and save to datbase        
        o = StockPropertyValue(symbol=self.c, value=6, stock_property=s)
        o.save()

        # show the id just for ourself
        print o.id

        # read from database
        o2 = StockPropertyValue.objects.get(id=o.id)
        self.assertEquals(6, o2.value)
        self.assertEquals(self.c, o2.symbol)
        
        # update object and save to datbase
        o2.symbol = self.c2
        o2.value = 9
        o2.save()

        # compare objects
        o3 = StockPropertyValue.objects.get(id=o2.id)
        self.assertEquals(o.id, o3.id)
        self.assertEquals(9, o3.value)
        self.assertEquals(self.c2, o3.symbol)
        
        # delete
        o3.delete()

        # verify its gone
        ol = StockPropertyValue.objects.filter(symbol=self.c2)
        self.assertEquals(0, len(ol))

        
