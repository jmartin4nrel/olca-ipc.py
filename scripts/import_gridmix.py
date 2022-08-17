# import_gridmix.py
# Imports NETL Grid Mix flows into openLCA datacase
from sqlite3 import DataError
from unicodedata import category
import uuid
import olca
from olca.schema import Ref
import pandas as pd
import math

def main():

    # Import TRACI factors & flow rates
    filepath = 'gridmix_traci_2_1.csv'
    traci_df = pd.read_csv(filepath, index_col=0)
    df_cols = traci_df.columns.values
    traci_idxs = ['TRACI 2.1' in i for i in df_cols]
    traci_cats = df_cols[traci_idxs]
    impact_cats = []

    # Create solar & wind process
    solar = olca.Process(name='Solar Electricity, NETL Grid Mix Explorer 4.2',
                        id=str(uuid.uuid4()), exchanges=[])
    wind = olca.Process(name='Wind Electricity, NETL Grid Mix Explorer 4.2',
                        id=str(uuid.uuid4()), exchanges=[])

    # Create a connection to the IPC server
    client = olca.Client(8081)

    # old_solar_ref = client.find(olca.Process, 'Solar Thermal Electricity')
    # old_solar = client.get(olca.Process, old_solar_ref.id)

    # Find TRACI impact categories in OpenLCA database
    for cat in traci_cats:
        impact_ref = client.find(olca.ImpactCategory, cat)
        impact_cats.append(client.get(olca.ImpactCategory, uid=impact_ref.id))

    # Loop through flows, storing unique category paths & flow props/units
    # Lists of lists for names, synchronous lists for object references
    cat_lol = []
    cat_list = []
    flow_lol = []
    flow_props = []
    flow_units = []
    for row_idx, row in traci_df.iterrows():
        
        # Create flow
        name = row.loc['Name']
        flow = olca.Flow()
        flow.olca_type = 'Flow'
        flow.id = str(uuid.uuid4())
        flow.name = name

        # Categorize flow
        flow.flow_type = olca.FlowType.ELEMENTARY_FLOW
        category_path = ['NETL flows']
        if row_idx == 0:
            category_name = 'Energy carriers and technologies'
            elec_ref = client.find(olca.Flow,name,category_path=category_path+[category_name])
            traci_df.loc[row_idx,'ID'] = elec_ref.id
            row.loc['ID'] = elec_ref.id
        else:
            category_name = 'Grid mix imports'
        # Build category path
        category_idxs = ['Category 1','Category 2','Category 3','Category 4']
        for category_idx in category_idxs:
            if type(row.loc[category_idx]) is str:
                category_path.append(category_name)
                category_name = row.loc[category_idx]
        # Search for category path if not in lists
        category_path_found = False
        if category_path + [category_name] not in cat_lol:
            categories = client.find(olca.Category, category_name, list_all=True)
            for category in categories:
                if category.category_path == category_path:
                    flow.category = category
                    category_path_found = True
                    cat_lol.append(category_path+[category_name])
                    cat_list.append(category)
        # Otherwise summon from lists
        else:
            idx = cat_lol.index(category_path+[category_name])
            if idx is not None:
                flow.category = cat_list[idx]
                category_path_found = True
        if not category_path_found:
            raise DataError('Could not find category path for {}'.format(name))

        # Search for the flow property and unit 
        factor = olca.FlowPropertyFactor()
        factor.conversion_factor = 1.0
        flow_prop_found = False
        if [row.loc['Flow property'],row.loc['Unit']] not in flow_lol:
            flow_prop_ref = client.find(olca.FlowProperty, row.loc['Flow property'])
            flow_prop = client.get(olca.FlowProperty, flow_prop_ref.id)
            unit_gp = client.get(olca.UnitGroup, flow_prop.unit_group.id)
            flow_unit = None
            for unit in unit_gp.units:
                if unit.name == row.loc['Unit']:
                    flow_unit = unit
                    flow_prop_found = True
            flow_prop.unit_group = flow_unit
            flow_lol.append([row.loc['Flow property'],row.loc['Unit']])
            flow_props.append(flow_prop)
            flow_units.append(flow_unit)
        else:
            flow_idx = flow_lol.index([row.loc['Flow property'],row.loc['Unit']])
            if flow_idx is not None:
                flow_prop = flow_props[flow_idx]
                flow_unit = flow_units[flow_idx]
                flow_prop_found = True
        if not flow_prop_found:
            raise DataError('Could not find flow property for {}'.format(name))
        factor.flow_property = flow_prop
        flow.flow_properties = [factor]

        # See if flow exists in data base, otherwise insert it
        existing_flow = None
        if type(row.loc['ID']) is str:
            id = row.loc['ID']
            existing_flow = client.get(olca.Flow,uid=id,name=name)
        if existing_flow is not None:
            flow = existing_flow
            print('Found flow {}'.format(row_idx))
        else:
            print('Did not find flow {}'.format(row_idx))
            traci_df.loc[row_idx,'ID'] = flow.id
            client.insert(flow)

            # Set TRACI factors
            for idx, cat in enumerate(traci_cats):
                impact_cat = impact_cats[idx]
                value = row.loc[cat]
                if not math.isnan(value):
                    impact_factor = olca.ImpactFactor(flow=flow,
                                                    flow_property=flow_prop,
                                                    unit=flow_unit,
                                                    value=value)
                    impact_cat.impact_factors.append(impact_factor)
                    client.update(impact_cat)

        # Create exchanges and insert them into solar/wind processes
        input = 'resource' in category_path or 'resource' == category_name
        solar_ex = olca.Exchange(flow=flow,
                                 flow_property=flow_prop,
                                 unit=flow_unit,
                                 input=input,
                                 amount=row.loc['Solar Use'])
        wind_ex = olca.Exchange(flow=flow,
                                 flow_property=flow_prop,
                                 unit=flow_unit,
                                 input=input,
                                 amount=row.loc['Wind Use'])
        solar_ex.quantitative_reference = row_idx == 0
        wind_ex.quantitative_reference = row_idx == 0
        solar.exchanges.append(solar_ex)
        wind.exchanges.append(wind_ex)

    # Insert processes
    category_path = ['NETL Process Library','Power Plants']
    category_name = 'Grid Mixes'
    categories = client.find(olca.Category, category_name, list_all=True)
    for category in categories:
        if category.category_path == category_path:
            solar.category = category
            wind.category = category
    client.insert(solar)
    client.insert(wind)        

    # Write IDs to .csv
    traci_df.to_csv(filepath)

if __name__ == '__main__':
    main()
