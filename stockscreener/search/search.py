
from models import Company, StockPropertyValue, StockProperty

"""
This is the query to find the ID of the companies that are matching
the criterias.

Order by number gives the companies matching most criteria at the top.
"""
SEARCH_QUERY = """
        select t1.id from (
            select c.id as id, count(*) as number
              from search_company c left outer join
                   search_stockpropertyvalue v on c.id = v.symbol_id
                   left outer join search_stockproperty p on p.id = v.stock_property_id
             where ( CRITERIA )
               SECTOR
               EXCHANGE
             group by c.id
        ) t1
        where number >= CRITERIA_COUNT
        order by number
        limit 25
"""

class Result(object):
    """
    Result holds one search result, it holds the company (symbol), and the
    values user wants to see (all or the criteria)
    """
    values = None
    symbol = None

    def __init__(self, symbol, values):
        self.symbol = symbol
        self.values = values

class MinMaxCriteria(object):
    """
    Min max criteria is a helper class that handles the min and max values from the
    form for one criteria (stock property).

    The most important, it has a to_sql method, which converts into SQL that is
    placed (together with other criterias) in the SEARCH_QUERY instead of "CRITERIA".
    """

    stock_property_id = None
    min_value = None
    max_value = None

    def __init__(self, stock_property_id, min_value=None, max_value=None):
        self.stock_property_id = stock_property_id
        self.min_value = min_value
        self.max_value = max_value

    def __repr__(self):
        return "<id=%d min=%s max=%s>" % (self.stock_property_id, str(self.min_value), str(self.max_value))

    def __has_value(self, value, operator):
        if value is None:
            return ""
        else:
            return " and v.value %s %s" % (operator, str(value))

    def to_sql(self, qn_func):
        """
        Convert the min/max criteria to SQL criteria.
        """
        if self.min_value is None and self.max_value is None:
            return "( p.id = %d )" % (self.stock_property_id)
        else:
            return "( p.id = %d%s%s )" % \
                (self.stock_property_id,
                 self.__has_value(self.min_value, '>='),
                 self.__has_value(self.max_value, '<='))

def build_sector_criteria(qn, sector):
    """
    Handles creating sector criteria (SECTOR)
    """
    if sector is None or sector.strip() == '':
        return ""
    else:
        return " and c.sector_id = %s " % sector

def build_exchange_criteria(qn, exchange):
    """
    Handles creating exchange criteria (EXCHANGE)
    """
    if exchange is None or exchange.strip() == '':
        return ""
    else:
        return " and c.exchange = '%s'" % exchange

def query(criterias, sector=None, exchange=None, show='all'):
    """
    Query performs the actual query to the database. It builds SQL that 
    represents the query of the user with min/max criterias, sector, and exchange limitations.

    If there are any matching companies, then it filters which attributes to show ('all' or
    'criteria')

    Finally it returns the results as a list of Result objects.
    """

    # get database connection
    from django.db import connection
    cursor = connection.cursor()
    qn = connection.ops.quote_name

    # build criteria
    if len(criterias) == 0:
        sql_criteria = '1'
    else:
        sql_criteria = ' or '.join([ c.to_sql(qn) for c in criterias ])

    sql = SEARCH_QUERY.replace('CRITERIA_COUNT', str(len(criterias))).replace('CRITERIA', sql_criteria)
    sql = sql.replace('SECTOR', build_sector_criteria(qn, sector))
    sql = sql.replace('EXCHANGE', build_exchange_criteria(qn, exchange))

    print "SQL=", sql

    cursor.execute(sql)

    # get the headers to show
    if show == 'all':
        # show all properties
        headers = StockProperty.objects.all()
    else:
        # show criterias as properties
        headers = [ StockProperty.objects.get(id=c.stock_property_id) for c in criterias ]
    
    result_list = []
    for row in cursor.fetchall():
        symbol = Company.objects.get(id=row[0])
        vlist = StockPropertyValue.objects.filter(symbol=symbol)
        vmap = {}
        for value in vlist:
            vmap[value.stock_property_id] = value.value

        values = []
        for header in headers:
            if vmap.has_key(header.id):
                values.append(vmap[header.id])
            else:
                values.append(None)

        # print "values=", values
            
        result_list.append(Result(symbol, values))

    return headers, result_list

    
