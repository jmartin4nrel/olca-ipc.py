# create1pentene.py
# Creates and imports 1-Pentene into openLCA datacase
from unicodedata import category
import uuid
import olca
from olca.schema import Ref


def main():
    
    # Create a connection to the IPC server
    client = olca.Client(8081)

    # Create flow
    name = '1-Pentene copy'
    flow = olca.Flow()
    flow.olca_type = 'Flow'
    flow.id = str(uuid.uuid4())
    flow.name = name

    # Categorize flow
    flow.flow_type = olca.FlowType.ELEMENTARY_FLOW
    factor = olca.FlowPropertyFactor()
    factor.conversion_factor = 1.0
    category_name = 'Grid Mix 4.2'
    category = client.find(olca.Category, category_name)
    if category is None:
        category = olca.Category()
        category.id = str(uuid.uuid4())
        category.name = category_name
        client.insert(category)
    flow.category = category
    
    # Search for the flow property and unit 
    mass_ref = client.find(olca.FlowProperty, 'Mass')
    mass = client.get(olca.FlowProperty, mass_ref.id)
    units_of_mass = client.get(olca.UnitGroup, mass.unit_group.id)
    kg = None
    for unit in units_of_mass.units:
        if unit.name == 'kg':
            kg = unit
    mass.unit_group = kg
    factor.flow_property = mass
    flow.flow_properties = [factor]
    client.insert(flow)

    # Set TRACI factors
    Test = client.find(olca.ImpactMethod, 'ILCD 2011, midpoint [v1.0.10, August 2016]')
    
    TRACI = client.find(olca.ImpactMethod, 'TRACI 2.1 (NETL)')
    impact_cats = ['Acidification Potential - TRACI 2.1 (NETL)',
                    'Eutrophication Potential - TRACI 2.1 (NETL)',
                    'Global Warming Potential [100 yr] - TRACI 2.1 (NETL)',
                    'Ozone Depletion Potential - TRACI 2.1 (NETL)',
                    'Particulate Matter Formation Potential - TRACI 2.1 (NETL)',
                    'Photochemical Smog Formation Potential- TRACI 2.1 (NETL)',
                    'Water Consumption (NETL)']
    impact_factors = [0,0,0,0,0,7.207435897,0]
    for idx, cat in enumerate(impact_cats):
        impact_ref = client.find(olca.ImpactCategory, cat)
        impact_cat = client.get(olca.ImpactCategory, uid=impact_ref.id)
        value = impact_factors[idx]
        if value != 0:
            impact_factor = olca.ImpactFactor(flow=flow,flow_property=mass,unit=kg,value=value)
            impact_cat.impact_factors.append(impact_factor)
            client.update(impact_cat)

    

if __name__ == '__main__':
    main()
