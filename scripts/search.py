# findCO2.py
# looks for all CO2 flows in database
import uuid
import olca
import csv
import numpy as np

def main():
    
    # Import .csv files
    num_subfolders = 4
    category_lol = []
    name_lol = []
    value_lol = []
    filenames = ['solar_in.csv']
    for filename in filenames:
        category_paths = []
        names = []
        values = []
        with open(filename, newline='') as csvfile:
            r = csv.reader(csvfile, delimiter=',')
            for row in r:
                category_path = row[0:num_subfolders]
                while '' in category_path:
                    category_path.remove('')
                category_paths.append(category_path)
                name = row[num_subfolders+1]
                names.append(name)
                values.append(float(row[num_subfolders+2]))
        category_lol.append(category_paths)
        name_lol.append(names)
        value_lol.append(values)

    # Create a connection to the IPC server
    client = olca.Client(8081)

    # Find flow IDs
    id_lol = []
    for file_idx, filename in enumerate(filenames):
        filename = filename[:-4]+'_ids.csv'
        ids = []
        with open(filename, 'w', newline='') as csvfile:
            w = csv.writer(csvfile, delimiter=' ')
            for flow_idx, name in enumerate(name_lol[file_idx]):
                category_path = category_lol[file_idx][flow_idx]
                Ref = client.find(olca.Flow, name, False, category_path)
                if Ref is None:
                    w.writerow('Not found')
                elif type(Ref) == list:
                    match_ids = []
                    for OneRef in Ref:
                        match_ids.append(OneRef.id)
                    w.writerow(match_ids)
                    ids.append(match_ids)
                else:
                    w.writerow(Ref.id)
                    ids.append(Ref.id)
        id_lol.append(ids)
    asdf

if __name__ == '__main__':
    main()