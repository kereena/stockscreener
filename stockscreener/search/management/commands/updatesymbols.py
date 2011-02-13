
from django.core.management.base import BaseCommand
from optparse import make_option
from stockscreener.search.extractor import SymbolsClient

class Command(BaseCommand):

    help = 'Update the cached symbols data from Freyr webservice'

    requires_model_validation = True

    symbolsclient = SymbolsClient()
    
    def handle(self, *args, **options):

        self.symbolsclient.load_symbols()

        print "All OK ;-)"            
