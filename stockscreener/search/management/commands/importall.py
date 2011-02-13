
from django.core.management.base import LabelCommand
from optparse import make_option
from stockscreener.search.models import Company, StockProperty
from stockscreener.search.extractor import Extractor

class Command(LabelCommand):

    help = 'Import all stock properties for one symbol.'
    args = '[number]'
    label = 'number'

    requires_model_validation = True

    extractor = Extractor()
    
    def handle_label(self, number, directory=None, **options):

        stock_properties = StockProperty.objects.all()
        symbols = Company.objects.all()

        print "Symbols=%d, Properties=%d" % (len(symbols), len(stock_properties))

        number = int(number)

        count = 1
        for symbol in symbols:

            if count > number:
                break

            count = count+1
            
            for stock_property in stock_properties:
                found = self.extractor.extract(symbol, stock_property)
                print "Extracting %s for %s -> %s" % (stock_property.name, symbol.symbol, str(found))

            
