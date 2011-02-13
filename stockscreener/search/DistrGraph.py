
from decimal import Decimal
from models import StockProperty, StockPropertyValue

# class to help with creating distribution graphs
class GraphHelper:

    # constructor    
    def __init__(self):        
        pass  

    #
    # method to create data for graph
    #
    # x_size is how many datapoints on the x axis of the graph
    # y_size is how many datapoints on the y axis of the graph
    #
    def create_data(self, x_size, y_size, stock_property_id):

        # find minimum and maximum values in the database
        values = StockPropertyValue.objects.filter(stock_property__id=stock_property_id).values_list('value',flat=True)

        a = min(values)
        b = max(values)

        # calculate how big is each x
        diff = (b - a) / x_size

        # result list of grouped values, its just empty now.        
        grouped_values = []

        # current start range is "a" (the minimum) in the beginning
        current_start_range = a

        # min and max values for y range
        y_min, y_max = None, None

        # find grouped values for each range
        for i in range(x_size):
            # calculate end range for this grouped value
            current_end_range = current_start_range + diff

            # ask database count of companies in database with value inside this range
            number_of_companies = StockPropertyValue.objects.filter(stock_property__id = stock_property_id,
                                                                    value__gte = current_start_range,
                                                                    value__lte = current_end_range).count()

            # update the min/max for Y range
            if y_min is None or number_of_companies < y_min:
                y_min = number_of_companies
            if y_max is None or number_of_companies > y_max:
                y_max = number_of_companies

            # create grouped value
            grouped_value = GroupedValue(number_of_companies, current_start_range, current_end_range)

            # add the grouped value to the result list
            grouped_values.append(grouped_value)

            # set the current start to current end, so next foreach loop iteration will start from there.
            current_start_range = current_end_range

        # return the result
        return (grouped_values, y_min, y_max)
 
    def create_graph_url(self, data, y_min, y_max, x_size, y_size):

        x_min = min([ d.start_range for d in data ])
        x_max = max([ d.end_range for d in data ])

        chd = 't:%s' % ','.join([ str(d.number_of_companies) for d in data ])
        chds = '%s,%s' % (str(y_min), str(y_max))
        
        params = {
            'chs': '%dx%d'% (x_size, y_size),
            'cht': 'lc',
            'chxt': 'x,y',
            'chxl': '0:|%s|%s|1:|%s|%s' % (str(x_min.normalize()), str(x_max.normalize()), str(y_min), str(y_max)),
            'chf': 'c,lg,90,76A4FB,0.5,ffffff,0|bg,s,EFEFEF',
            'chd': chd,
            'chds': chds
        }

        url_params = []
        for k in params.keys():
            url_params.append('='.join((k, params[k])))

        return 'http://chart.apis.google.com/chart?%s' % '&'.join(url_params)

# http://chart.apis.google.com/chart?chxt=x,y&chds=0,10&chd=t:10,5,0,4,10&chf=c,lg,90,76A4FB,0.5,ffffff,0|bg,s,EFEFEF&chs=300x100&cht=lc&chxl=0:0|5

# class to hold grouped values for use by the graph creation.
class GroupedValue:

    def __init__(self, number_of_companies, start_range, end_range):
        self.number_of_companies = number_of_companies
        self.start_range = start_range
        self.end_range = end_range

    def __repr__(self):
        return "GroupedValue s=%.2f, e=%.2f, c=%d" % (self.start_range, self.end_range, self.number_of_companies)

