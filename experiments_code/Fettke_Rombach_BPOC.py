from simulator import Simulator, EventType
from statistics import mean
from math import inf
from collections import OrderedDict
import time
import numpy as np


class MyPlanner:
    
    
    def __init__(self):
        self.task_info = None          # task            -> how many resources in pool (saved as var to reduce runtime)
        self.resource_info = None      # resource        -> how many tasks the resource is applicable to
        self.time_info = dict()        # task x resource -> execution times in past n events of that combination
        self.task_dict = OrderedDict() # task            -> list of resources that can (currently) be assigned

    
    def plan(self, available_resources, unassigned_tasks, resource_pool):    
        
        ## Helper functions ##
        
        def get_infos():
            """
            Initializes task_info-dict and resource_info-dict.
            """ 
            assert (self.resource_info is None and self.task_info is None) # only run once
            
            self.task_info = dict()

            for task_type, resource_list in resource_pool.items():
                self.task_info[task_type] = len(resource_list)
                
                
            self.resource_info = dict()
            
            occurring_resources = set([x for xs in list(resource_pool.values()) for x in xs])
            
            for resource in occurring_resources:
                self.resource_info[resource] = sum(resource in task_resource_list for task_resource_list in list(resource_pool.values()))
            
            return
        
        
        def init_time_info(task_type):
            """
            Initializes time_info-dict for a specific task_type.
            """ 
            if task_type not in self.time_info:
                self.time_info[task_type] = dict()

                pool = resource_pool[task_type]

                for resource in pool:
                    self.time_info[task_type][resource] = [inf] # as init; to prevent error when calculating mean

            return
        
        
        def update_data(resource, task):
            """
            Updates relevant data regarding assignment to be performed.
            """
            available_resources.remove(resource)
            unassigned_tasks.remove(task)
            assignments.append((task, resource))
                                        
            return
            
            
        def update_task_dict():
            """
            For each task, get currently available and applicable resources.
            Also prioritizes resource-lists (by resource_compare) and tasks (by task_compare).
            """            
            task_dict = dict()
                       
            local_unassigned_tasks = unassigned_tasks.copy()
            
            while len(local_unassigned_tasks) > 0:
                task = local_unassigned_tasks[0]
                
                init_time_info(task.task_type) # mabye init to prevent Key-Error
                
                pool = resource_pool[task.task_type]
                available_in_pool = [resource for resource in available_resources if resource in pool]
                
                if available_in_pool == []:
                    unassigned_tasks.remove(task) # not assignable anyway
                else:
                    # sort resource-list for prioritization of resources
                    resource_compare = lambda r: (mean(self.time_info[task.task_type][r]), - self.resource_info[r])
                    available_in_pool = sorted(available_in_pool, key=resource_compare)
                                            
                    task_dict[task] = available_in_pool
                
                del local_unassigned_tasks[0]

                
            # sort task-dict for prioritization of tasks
            # item = (task, resource-list)
            task_compare = lambda item: (len(item[1]), self.task_info[item[0].task_type], item[0].case_id)
            task_dict = OrderedDict(sorted(task_dict.items(), key=task_compare))
            
            self.task_dict = task_dict
                        
            assert len(unassigned_tasks) == len(self.task_dict), len(unassigned_tasks) + "!=" + len(self.task_dict)
            
            return
        
        
        ######################

        # begin plan()
        
        assignments = []
        
        if self.resource_info is None or self.task_info is None:
            get_infos() # init once
        
        
        # BASE CASE
        if len(available_resources) == 1:
            resource = list(available_resources)[0] # the only available resource
            unassigned_tasks = [task for task in unassigned_tasks if resource in resource_pool[task.task_type]] # filter
            
            if unassigned_tasks == []:
                return [] # no assignment possible
                    
            for task in unassigned_tasks:
                init_time_info(task.task_type) # mabye init to prevent Key-Error
            
            base_compare = lambda task: (self.task_info[task.task_type], task.case_id)
            sorted_unassigned_tasks = sorted(unassigned_tasks, key=base_compare)
            
            task = sorted_unassigned_tasks[0] # first task -> prioritized one
            
            update_data(resource, task) # do assignment and update
                            
            assert len(assignments) == 1
            
            return assignments 
        
        
        update_task_dict()

                 
        # main loop            
        while len(unassigned_tasks) > 0:   
            assert len(unassigned_tasks) == len(self.task_dict), len(unassigned_tasks) + "!=" + len(self.task_dict)
            task, resource_list = next(iter(self.task_dict.items()))
                                    
            if resource_list == []: # should not happen (tasks with empty list get deleted in update), but just in case 
                unassigned_tasks.remove(task)
                continue
                
            resource = resource_list[0]
        
            update_data(resource, task) # do assignment and update
            
            if len(available_resources) == 0: # no more assignments possible 
                return assignments

            update_task_dict() # update
                    

        return assignments



    def report(self, event):        
        if not (event.lifecycle_state == EventType.START_TASK or event.lifecycle_state == EventType.COMPLETE_TASK):
            return # these types not useful here
        
        # no need to differentiate between cases since resource is blocked until activity completed
        # -> the following complete-event with that task-resource-combination is necessarily part of same case as start-event
        task_type = event.task.task_type
        resource = event.resource
        
        if event.lifecycle_state == EventType.START_TASK:
            if inf in self.time_info[task_type][resource]:
                self.time_info[task_type][resource].remove(inf) # from init -> not needed anymore
            
            if len(self.time_info[task_type][resource]) == 20: # limit for window-size reached
                del self.time_info[task_type][resource][0] # delete first (i.e. oldest) entry
                
            self.time_info[task_type][resource].append(event.timestamp) # add new entry to list
                        
        else: # complete_task
            # change most recent entry to time-difference between start (currently last element in list) and complete
            self.time_info[task_type][resource][-1] = event.timestamp - self.time_info[task_type][resource][-1]
            
        #print(event) # print all information for each performed event

##############

# code for running the approach with the simulator-file
# prints out the results for the experiments

totalCycleTime = 0
amount = 5 # change amount of runs for experiments
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
    print(x+1, result)

print ("Avg. cycle time per case=", totalCycleTime / amount)
print ("Variance=", np.var(run_list))
print ("Std. deviation=", np.std(run_list))
print('Avg. runtime: {:5.3f}s'.format(runtime / amount))
