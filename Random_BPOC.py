from simulator import Simulator
import time
import numpy as np
import random

class MyPlanner:

    def plan(self, available_resources, unassigned_tasks, resource_pool):
        
        assignments = []
            
        for task in unassigned_tasks:
            for resource in available_resources: 
                resource = random.choice(tuple(available_resources))
                if resource in resource_pool[task.task_type]:
                    available_resources.remove(resource)
                    assignments.append((task, resource))
                    break  

        return assignments

    def report(self, event):
        #print(event) 
        return
        
   
totalCycleTime = 0
amount = 5
runtime = 0
run_list = []
for x in range(0, amount):
    start = time.time()
    my_planner = MyPlanner()
    simulator = Simulator(my_planner)
    result = simulator.run()
    cycletime = simulator.total_cycle_time / simulator.finalized_cases
    totalCycleTime = cycletime + totalCycleTime
    run_list.append(cycletime)
    end = time.time()
    runtime = runtime + (end-start)
    print(result)

print ("Avg. cycle time per case=", totalCycleTime / amount)
print ("Variance=", np.var(run_list))
print ("Std. deviation=", np.std(run_list))
print('Avg. runtime: {:5.3f}s'.format(runtime / amount))



