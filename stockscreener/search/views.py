# Create your views here.

from DistrGraph import GraphHelper
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
import forms, search
from models import StockProperty, StockPropertyValue

#
# Build graph url, and send redirect to it.
#
def distrgraph(request, stock_property_id):
    """
    Builds a graph URL using the GraphHelper, and sends HTTP Redirect to this
    new URL.

    If there was an exception creating the URL, we send HTTP Redirect to the graph-error
    image (so browser will show that)
    """
    try:
        g = GraphHelper()
    
        data, y_min, y_max = g.create_data(50, None, stock_property_id)

        url = g.create_graph_url(data, y_min, y_max, 220, 75)

        return HttpResponseRedirect(url)

    except Exception, e:
        print e.message
        return HttpResponseRedirect('/site_media/graph-error.png')


def index(request):
    """
    Index is the page that is shown when user enters /search/ It is showing
    the main search page.

    Creates a new search form object, and renders the search form in response.
    """
    form = forms.SearchForm()
    
    return render_to_response('search/search.html', {'form': form})


def addcriteria(request, stock_property_id):
    """
    Add criteria is requested when user selects a criteria in the drop-down
    list in the search form.

    A criteria is found, and we find min/max values, and returns the criteria.html
    in response, which contains input fields for the user to enter details about
    this criteria.
    """

    # get the criteria
    criteria = StockProperty.objects.get(id=stock_property_id)

    # find the min/max for the criteria
    values = StockPropertyValue.objects.filter(stock_property=criteria).values_list('value',flat=True)
    min_value = min(values).normalize()
    max_value = max(values).normalize()

    return render_to_response('search/criteria.html', {'criteria': criteria, 'min_value': min_value, 'max_value': max_value})


def getresult(request):
    """
    Get result returns the result of a query, it is executed when user presses
    the Search Now button on the HTML page.

    It can work in two different ways:
    1) Form is valid => show results
    2) Form is not valid => show error message
    """

    form = forms.SearchForm(request.POST)
    form.find_minmax_criteria(request.POST)

    if form.is_valid():

        headers, results = search.query(form.to_criteria(), form.cleaned_data['sector'], form.cleaned_data['exchange'], form.cleaned_data['show_result'])

        # show result in response
        return render_to_response('search/result.html', {
            'headers': headers,
            'results': results
        })

    else:
        # show error message in response
        return render_to_response('search/result-error.html', {
            'message': 'Please enter details correctly.',
            'form': form
        })
