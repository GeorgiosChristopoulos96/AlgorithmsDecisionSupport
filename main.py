import sys
from ortools.linear_solver import pywraplp
import chardet

def create_data_model():
    """Read the data from the text file."""
    #introduce txt file for testing
    filepath_name = ""
    f = open(filepath_name, "r")
    rawdata = open(filepath_name, "rb").read()
    result = chardet.detect(rawdata)
    charenc = result['encoding']
    #validation if txt file is ascii
    if(charenc =='ascii'):
        no_images = int(f.readline())
    else:
        print("Please provide an ASCII file")
        sys.exit()
    images = []
    unavail_time_start = []
    unavail_duration = []
    #Seperation of images and unavailabilities
    for x in f:
        t = str(x).strip("\n")
        if t.find(",") != -1:
            s = t.split(",")
            unavail_time_start.append(float(s[0]))
            unavail_duration.append(float(s[1]))
        if t != '' and t.find(",") == -1:
            if(len(images) != no_images):
                images.append(float(t))
    no_unavail = len(unavail_duration)
    #sort unavailable intervals in case they are random
    unavail_time_start, unavail_duration = zip(*sorted(zip(unavail_time_start, unavail_duration)))
    """Create the data for the example."""
    data = {}
    data["unavailabilities"] = unavail_duration
    data['weights'] = images
    total_capacity = 0
    data['all_items'] = list(range(len(images)))
    data['bin_capacities'] = []
    for i in range(no_unavail):
        if (i == 0):
            data['bin_capacities'].append(unavail_time_start[i])
        elif (i == no_unavail):
            data['bin_capacities'].append(total_capacity - unavail_time_start[i] + unavail_duration[i])
        else:
            data['bin_capacities'].append(
                unavail_time_start[i] - (unavail_time_start[i - 1] + unavail_duration[i - 1]))
    data["bins"] = list(range(len(data["bin_capacities"])))
    return data

def main():
    data = create_data_model()
    data['num_items'] = len(data['weights'])
    data['all_items'] = range(data['num_items'])
    data['num_bins'] = len(data['bin_capacities'])
    data['all_bins'] = range(data['num_bins'])

    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if solver is None:
        print('SCIP solver unavailable.')
        return

    # Variables.
    # x[i, b] = 1 if item i is packed in bin b.
    x = {}
    for i in data['all_items']:
        for b in data['all_bins']:
            x[i, b] = solver.BoolVar(f'x_{i}_{b}')

    # Constraints.
    # Each item is assigned to at most one bin.
    for i in data['all_items']:
        solver.Add(sum(x[i, b] for b in data['all_bins']) <= 1)

    # The amount packed in each bin cannot exceed its capacity.
    for b in data['all_bins']:
        solver.Add(
            sum(x[i, b] * data['weights'][i]
                for i in data['all_items']) <= data['bin_capacities'][b])

    # Objective.
    # Maximize total value of packed items.
    objective = solver.Objective()
    for i in data['all_items']:
        for b in data['all_bins']:
            objective.SetCoefficient(x[i, b], data['weights'][i])
    objective.SetMaximization()

    status = solver.Solve()

    if status == pywraplp.Solver.OPTIMAL:
        total_cost = 0
        no_trans_items = 0
        weights_trans = data["weights"].copy()
        for b in data['all_bins']:
            print('Bin number', b)
            bin_weight = 0
            bin_value = 0
            for i in data['all_items']:
                if x[i, b].solution_value() > 0:
                    print(
                        f"Item {i} weight: {data['weights'][i]}"
                    )
                    weights_trans.remove(data["weights"][i])
                    bin_weight += data['weights'][i]
                    no_trans_items += 1
            if no_trans_items < len(data["weights"]):
                total_cost += data["unavailabilities"][b]
                total_cost += data["bin_capacities"][b]
                print('Bin capacity', data["bin_capacities"][b])
                #if all items are transmitted append the weights of the last interval and exit
            elif no_trans_items == len(data["weights"]):
                total_cost += bin_weight
                break
            else:
                #else add up the bin weight
                total_cost += bin_weight
            print(f'Packed bin weight: {bin_weight}')
        #if there are remaining items add them to the last bin
        for i in weights_trans:
            total_cost+= i
        print(f'Total cost: {total_cost}')
    else:
        print('The problem does not have an optimal solution.')
if __name__ == '__main__':
    main()