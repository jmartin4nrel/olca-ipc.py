# findCO2.py
# looks for all CO2 flows in database
import uuid
import olca
import example

def main():
    
    # Create a connection to the IPC server
    client = olca.Client(8081)

    co2 = client.find(olca.Flow, 'Carbon dioxide, to soil or biomass stock', list_all=True, category_path=['Elementary flows','Emission to soil'])
    
if __name__ == '__main__':
    main()
