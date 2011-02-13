
from django.core.management.base import LabelCommand
from optparse import make_option

class Command(LabelCommand):

    help = 'Import all stock properties for one symbol.'
    args = '[symbol]'
    label = 'symbol'

    requires_model_validation = True

    def handle_label(self, symbol, directory=None, **options):
        from django.conf import settings
        from stockscreener.search.models import StockProperty, Company
        from stockscreener.search.extractor import Extractor

        stock_properties = StockProperty.objects.all()

        for stock_property in stock_properties:

            found = Company.objects.filter(symbol=symbol)
            
            print "Extracting %s for %s" % (stock_property.name, symbol)
            # create instance of Extractor (construct an object of class Extractor)
            extractor = Extractor()
            # call method extract on the instance of Extractor
            extractor.extract(found[0], stock_property)

