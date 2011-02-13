from django.db import models

"""
This module, models.py, contains the Model classes that we will
use to map to the database.
"""

class Sector(models.Model):
    """
    Sector describes a field that a company can belong to.
    """

    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

class Company(models.Model):
    """
    Company holds information about the companies, eg. their name,
    their stock symbol, what currency they are traded in, the size,
    sector, and so on.
    """

    SIZES = (('L', 'Large'),
             ('M', 'Medium'),
             ('S', 'Small'))

    EXCHANGES = (('CSE', 'Copenhagen Stock Exchange'),
                 ('STO', 'Stockholm Stock Exchange'),
                 ('HEL', 'Helsinki Stock Exchange'),
                 ('ISE', 'Iceland Stock Exchange'))

    # the name of the company
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    currency = models.CharField(max_length=4)
    exchange = models.CharField(max_length=10, choices=EXCHANGES)
    size = models.CharField(max_length=1, choices=SIZES)
    sector = models.ForeignKey(Sector)
    isin = models.CharField(max_length=30)
    # guess is the guess provided by freyr
    reuters_symbol_guess = models.CharField(max_length=20)
    # ok is the corrected guess, can be set using admin interface
    reuters_symbol_ok = models.CharField(max_length=20, null=True, blank=True)

    def get_reuters_symbol(self):
        if self.reuters_symbol_ok is not None:
            return self.reuters_symbol_ok
        else:
            return self.reuters_symbol_guess

    reuters_symbol = property(get_reuters_symbol)

    def __str__(self):
        return "%s" % (self.symbol)

class StockProperty(models.Model):
    """
    Stock property holds the definition of a stock property (ie.
    how to retrieve it, and the name of the property, eg. P/E Ratio)
    """

    name = models.CharField(max_length=100)
    url = models.URLField()
    xml_path = models.CharField(max_length=250)
    convert_expression = models.CharField(max_length=250)

    def __str__(self):
        return self.name.encode('iso-8859-1')

class StockPropertyValue(models.Model):
    """
    Stock property value holds the current value for a stock property given
    a company (symbol)
    """

    symbol = models.ForeignKey(Company)
    value = models.DecimalField(max_digits=19, decimal_places=5)
    stock_property = models.ForeignKey(StockProperty)

    def __str__(self):
        return "%.2f" % self.value

class StockPropertyValueHistory(models.Model):
    """
    Stock property value history holds the historical values for a given
    stock property value.  It is related as  a 1:M to a stockproperty value.
    """

    current_value = models.ForeignKey(StockPropertyValue)

    historical_value = models.DecimalField(max_digits=19, decimal_places=5)
    historical_date = models.DateField()
