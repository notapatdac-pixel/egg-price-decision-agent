from .oil_indicator import OilPriceIndicatorTool
from .price_lookup import PriceLookupTool

def get_default_tools():
    return [PriceLookupTool(), OilPriceIndicatorTool()]
