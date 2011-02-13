import StringIO, re, decimal, urllib2, xml.dom.minidom, datetime
from lxml.html import ElementSoup
from models import StockPropertyValue, Company, Sector, StockPropertyValueHistory
import stockscreener.settings as settings

def get_opener(other=None):
    """
    The purpose of the opener method is to create an URL-opener, which
    is using proxy if I am at vejleHS network, and no proxy if I am 
    at home (with direct Internet connection)
    """
    handlers = []
    # if settings has USE_PROXY set, then we use the ntmlaps proxy
    if settings.USE_PROXY:
        proxy_handler = urllib2.ProxyHandler({'http':'127.0.0.1:5865'})
        handlers.append(proxy_handler)

    if other is not None:
        handlers.append(other)

    # build the opener and return it
    opener = urllib2.build_opener(*handlers)
    return opener

def usd_to_value(value):
    """
    USD to value handles the case where a field contains a $ symbol at the start.
    """
    if value is None:
        return None

    value = value.strip()

    if value.startswith('$'):
        return value[1:]
    else:
        return value

def convert_ssi_units(value):
    """
    convert SSI units handles converting from SSI units (k=kilo, m=mega, g=giga) to
    a number I can save in the database.

    Eg. it expands something like: 1234k => 1234000 or 1M => 1000000
    """
    ssi = {'k': decimal.Decimal(1000),
           'm': decimal.Decimal(1000000),
           'g': decimal.Decimal(1000000000)}

    # use Regular expresssion.
    # [0-9.,]+ matches numbers and . and , - eg. 19,123.20 or 19 or 123,220 or 12.000
    # [MmGgKk] matches 'M' or 'm' or 'G' or 'g' or 'K' or 'k'
    # " *" matches 0 or more spaces.
    # ( ) means to extract the values, it is extracting a number and a unit
    m = re.match('^([0-9.,]+) *([MmGgKk])', value)
    
    if m is None:
        return value
    else:
        # get the extracted values
        val, unit = m.group(1), m.group(2)
        return decimal.Decimal(val.replace(',','')) * ssi[unit.lower()]

class Extractor:
    """
    Extractor class will handle the task to get a value for a stock property, given
    a company, and a stock property, using the following steps:

    1) download the page from the stock property "url" field (download method).
    2) find the value in the downloaded HTML page (execute_xpath method)
    3) convert the value from the HTML page into something usable (execute_converter method)

    The extract method does all these steps, and also has a simple cache function, so
    I do not download the same page many times (it only caches one web-page)
    """

    last_page = None
    last_url = None

    def extract(self, company, stock_property):

        symbol = company.reuters_symbol

        # download page, cache last page
        url = stock_property.url.replace('SYMBOL', symbol)
        if self.last_url == url:
            html = self.last_page
        else:
            html = self.download(url)
            self.last_url = url
            self.last_page = html
            
        # extract the value from page
        value = self.execute_xpath(html, stock_property.xml_path)
        if value is None:
            return None
        
        # convert the extracted value
        converted = self.execute_converter(value,stock_property)
        if converted is None:
            return None

        # Old values finding
        try:
            sp_value = StockPropertyValue.objects.get(stock_property = stock_property,
                                                      symbol = company)
            sp_value.value = converted

        except StockPropertyValue.DoesNotExist:
            sp_value = StockPropertyValue(stock_property = stock_property,
                                          value = converted,
                                          symbol = company)

        sp_value.save()

        # create historical item.
        hist_values = StockPropertyValueHistory.objects.filter(current_value = sp_value).order_by('-historical_date')

        # there is no historical value yet, or the first (sorted, so newest) is
        # not the same as the value we converted.
        if len(hist_values) == 0 or hist_values[0].historical_value != converted:
            hist_value = StockPropertyValueHistory(current_value=sp_value,
                                                   historical_value=converted,
                                                   historical_date=datetime.date.today())
            hist_value.save()

        return sp_value

    # download the url and save it in object
    def download(self, url):
        opener = get_opener()
        fd = opener.open(url)
        html = fd.read()
        fd.close()
        return html

    # evaluate the xpath and save it in object.
    def execute_xpath(self, html, xml_path):
        # parse the html
        doc = ElementSoup.parse(StringIO.StringIO(html))
        elem = doc.xpath(xml_path)

        # if there is no element, return None, otherwise return the contents.        
        if elem is None or len(elem) == 0:
            return None
        else:
            return elem[0].text

    def execute_converter(self, value,stock_property):
        # setup ssi function in local scope
        SSI = convert_ssi_units
        # setup USD function in local scop
        USD = usd_to_value
        # setup value as 'x' variable
        x = value
        # evaluate x using the convert_expession of the the stock property
        converted = eval(stock_property.convert_expression)
        # return as decimal, if it is already, then do nothing, otherwise try to convert
        try:
            if isinstance(converted, decimal.Decimal):
                return converted
            else:
                return decimal.Decimal(str(converted).replace(',',''))
        except:
            return None

# Task number - 4 
class SymbolsClient:
    """
    SymbolsClient is a client for the web-service offered by Freyr, which contains
    a list of companies.
    """

    # define how we map from Freyr data to my size flag.
    SIZE_MAP = dict(LARGE='L', MID='M', SMALL='S')

    URL = 'http://beta.freyr.dk/freyrhelp/companies'
    
    def __init__(self, url=None):
        if url is not None:
            self.URL = url

    def get_document_fd(self):
        """
        Helper method to create URL opener which provides a username and password
        (is required for the Freyr webservice)
        """
        
        # create password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.URL, 'demo', 'prototype')

        # create digest auth handler with the password manager
        handler = urllib2.HTTPDigestAuthHandler(password_mgr)

        # create url opener with the digest auth handler
        opener = get_opener(handler)

        # try to open the URL
        fd = opener.open(self.URL)

        return fd

    def load_symbols(self):
        """
        Loads the symbols from Freyr, parses the XML, and saves as Company/Sector objects
        into the database.
        """
        
        document = xml.dom.minidom.parse(self.get_document_fd())

        # for each "company" element in the XML
        for element in document.getElementsByTagName("company"):

            # get values from the "company" XML
            name = self.__elem_value(element, 'name')
            currency = self.__elem_value(element, 'currency')
            exchange = self.__elem_value(element, 'exchange')
            size = self.__elem_value(element, 'size')
            sector = self.__elem_value(element, 'sector')
            symbol = self.__elem_value(element, 'symbol')
            isin = self.__elem_value(element, 'isin')
            reuters_symbol_guess = self.__elem_value(element, 'reuters-symbol-guess')

            # if some value is not there, then continue to next "company"
            if name is None or currency is None or exchange is None or size is None \
                    or sector is None or symbol is None or isin is None \
                    or reuters_symbol_guess is None:
                continue

            # print "Company=%s" % name.encode('ascii', 'ignore')

            # get the sector to save for
            s_obj = self.get_sector_by_name(sector)

            # find symbols in database
            symbols = Company.objects.filter(symbol=symbol)

            # if there are some symbols
            if len(symbols) > 0:
                # then update all
                for symbol in symbols:
                    symbol.name = name
                    symbol.currency = currency
                    symbol.size = self.SIZE_MAP[size]
                    symbol.exchange = exchange
                    symbol.sector = s_obj
                    symbol.isin = isin
                    symbol.reuters_symbol_guess = reuters_symbol_guess
                    symbol.save()

            # otherwise, save the new symbol
            else:
                s = Company(name=name, currency=currency,
                            exchange=exchange, size=self.SIZE_MAP[size],
                            sector=s_obj, symbol=symbol,
                            isin=isin, reuters_symbol_guess=reuters_symbol_guess)
                s.save()

    def get_sector_by_name(self, name):
        """
        Finds a sector by its name, if not found, then create the Sector and return
        the newly created Sector.
        """
        try:
            return Sector.objects.get(name=name)
        except Sector.DoesNotExist:
            sector = Sector(name=name)
            sector.save()
            return sector

    def __elem_value(self, elem, to_find):
        """
        Finds an element by its name, and returns a string containing its content
        (content is the childNodes joined together)
        """
        found = elem.getElementsByTagName(to_find)
        if len(found) == 0:
            return None
        else:
            return "".join([ n.nodeValue for n in found[0].childNodes]).strip()
