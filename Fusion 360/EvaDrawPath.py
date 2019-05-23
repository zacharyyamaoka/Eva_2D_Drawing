#Author-Zachary Yamaoka
#Description-

import adsk.core, adsk.fusion, adsk.cam, traceback
import os.path


file_directory = '/Users/zachyamaoka/Desktop'
file_name = "tool_path.txt"

app = adsk.core.Application.get()
ui = app.userInterface

design = app.activeProduct

# Get the root component of the active design.
rootComp = design.rootComponent

# Create a new sketch on the xy plane.
sketches = rootComp.sketches;
currSketch = sketches.item(0)



def save(file_directory, filename, info):      
    with open(os.path.join(file_directory,filename), "w") as file1:
        file1.write(info)
        file1.close() 
        
def round_array(array):
    
    return (round(array[0],6),round(array[1],6),round(array[2],6))

visted = []
unique_id = 0

#  Curves
curves = currSketch.sketchCurves
splines = curves.sketchFittedSplines
lines = curves.sketchLines

graph = dict()

#Loop through Curves
num_curves = splines.count
for i in range(num_curves):
    curr_spline = splines.item(i)
    spline_points = curr_spline.fitPoints
    num_s_points = spline_points.count
    assert(num_s_points==3)
    end1 = spline_points.item(0).geometry.asArray()
    end1 = round_array(end1)
    middle = spline_points.item(1).geometry.asArray()
    end2 =spline_points.item(2).geometry.asArray()
    end2 = round_array(end2)
    
    graph[end1] = [[middle],"linear", unique_id]
    unique_id += 1
    
    graph[middle] = [[end2,end1],"spline",unique_id]
    unique_id += 1

    graph[end2] = [[middle],"linear", unique_id]
    unique_id += 1

#Loop through straight lines
num_lines = lines.count

for i in range(num_lines):
    curr_line = lines.item(i)
    geo = curr_line.geometry
    end = round_array(geo.endPoint.asArray())
    start = round_array(geo.startPoint.asArray())
    
    if end in graph: # append neighbor
        graph[end][0].append(start)
    else:
        graph[end] = [[start],"linear", unique_id]
        unique_id += 1
        
    if start in graph: # append neighbor
        graph[start][0].append(end)
    else:
        graph[start] = [[end],"linear", unique_id]
        unique_id += 1


print(graph) #fully graph, all with 2 nodes, 2 with 1 nodes

# Create structure
points = ""

start_point = (0.0,0.0,0.0)
queue = [start_point]
start_id = graph[start_point][2]
while len(queue) > 0 : #while not empty
    curr_point = queue.pop()
    #check if visted
    curr_point_info = graph[curr_point]
    curr_id = curr_point_info[2]
    print("\n")
    print(curr_point)
    print(curr_id)
    if curr_id in visted:
        print("rejected")
        print("\n")
        #if curr_id == start_id: # special case, for circular paths, prevent backtrack on next step but allow to travel on last step
            #visted.remove(start_id)
        continue
    else:
        visted.append(curr_id)
        
    #Append Current Point to list
    for cord in curr_point:
        points += str(cord) + ","
    points += curr_point_info[1] + ","
    neighbour = curr_point_info[0]
    queue += neighbour
    
# Note currently cannot tell difference between left or right
save(file_directory, file_name, points) 