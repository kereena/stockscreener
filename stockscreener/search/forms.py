
import re
from decimal import Decimal
from django import forms
from models import StockProperty, Company, Sector
from search import MinMaxCriteria

"""
The forms module handles the forms in the django application.

We have only one form, the SearchForm, so it is relatively simple for now.
"""

def load_sectors():
    """
    Helper function to load a list of sectors.
    """
    # load sectors and convert to a list: ((1,'Sector1'), (2,'Sector2'))
    l = [ (s.id, s.name) for s in Sector.objects.all() ]
    # add empty sector to the beginning of list (starting in dropdown menu)
    l.insert(0, ('', 'Select sector ...'))
    return l

def load_exchanges():
    """
    Helper function to provide a lits of exchanges
    """
    # clone the EXCHANGES tuple in Company class
    l = list(Company.EXCHANGES);
    # add empty exchange.
    l.insert(0, ('', 'Select exchange ...'))
    return l

def load_criterias():
    """
    Helper function to provide a list of StockProperties to select in the form
    """
    l = [ (p.id, p.name) for p in StockProperty.objects.all() ]
    l.insert(0, ('', 'Select to add criteria ...'))
    return l

class SearchForm(forms.Form):
    """
    The search form represents the search form. It has a list of static fields
    which are using the Django framework to handle: sector, exchange, add_criteria, show_result

    It also has minmax_criteria which is dynamic, and we have the helper function
    find_minmax_criteria to handle those.
    """

    SHOW_RESULT = (
        ('criteria', 'Show only selected in result'),
        ('all', 'Show all in result'))

    sector = forms.ChoiceField(choices=load_sectors(), required=False, initial='')
    exchange = forms.ChoiceField(choices=load_exchanges(), required=False, initial='')

    add_criteria = forms.ChoiceField(choices=load_criterias(), required=False, initial='')
    add_criteria.widget.attrs['onchange'] = "addCriteria('id_criterias', this);"

    show_result = forms.ChoiceField(choices=SHOW_RESULT, required=True)

    minmax_criteria = None

    def find_minmax_criteria(self, data):
        """
        Find all minmax criterias from the search form.
        """
        found = {}
        data = dict(data)
        for k in data.keys():
            m = re.match(r'(?P<minmax>min|max)\[(?P<property_id>\d+)\]', k)
            if m is not None:
                minmax = m.group('minmax')
                property_id = int(m.group('property_id'))
                if not found.has_key(property_id):
                    found[property_id] = MinMaxCriteria(property_id)
                if minmax == 'min':
                    found[property_id].min_value = self.__to_value(data[k])
                elif minmax == 'max':
                    found[property_id].max_value = self.__to_value(data[k])
        self.minmax_criteria = found

    def __to_value(self, s):
        """
        Convert the value to a decimal number
        """
        if isinstance(s, list):
            s = s[0]
        if s is None:
            return None
        elif s.strip() == '':
            return None
        else:
            return Decimal(s)
    
    def to_criteria(self):
        """
        Creates a list of criteria from the minmax_criteria found in the form.
        """
        c = []
        if self.minmax_criteria is not None:
            c.extend(self.minmax_criteria.values())

        return c
