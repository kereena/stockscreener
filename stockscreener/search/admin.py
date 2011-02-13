from models import StockProperty, StockPropertyValue, StockPropertyValueHistory, Company, Sector
from django.contrib import admin

"""
This module defines how each model should look in the admin interface.

Each model needs to have an admin.ModelAdmin class, and then this class has to be
registered together with the model class in the admin site.
"""

class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name','symbol','reuters_symbol_guess','reuters_symbol_ok','sector','size','exchange']

class SectorAdmin(admin.ModelAdmin):
    list_display = ['name']

class StockPropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'xml_path', 'convert_expression']
    
class StockPropertyValueAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'value', 'stock_property']

class StockPropertyValueHistoryAdmin(admin.ModelAdmin):
    list_display = ['current_value', 'historical_value', 'historical_date']

# register models and modeladmins with the admin site.
admin.site.register(StockProperty, StockPropertyAdmin)
admin.site.register(StockPropertyValue, StockPropertyValueAdmin)
admin.site.register(StockPropertyValueHistory, StockPropertyValueHistoryAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(Sector, SectorAdmin)
