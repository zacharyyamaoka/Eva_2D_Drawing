#!/usr/bin/env python3
from automata.Eva import Eva
import time
import json
import logging
from draw_funcs import *
import math

# Ensure Eva is Connected to Computer

host_ip = "http://172.16.16.2" # Ip you used to connect to choreograph
token = "cec3d52b-ad0c-4caf-8624-95f09381fce9" # API Tokens
start_joints_deg = [17.55,6.55,-129.82,4,-55.16,-108.37] # Read from Go-to on choreograph

#----------------------------------------------

file_path = "./path.txt"
eva = Eva(host_ip, token)

# Enter Starting Joint Angles. Read off of dashboard in choreograph

# Convert joint angles from deg to rad
start_joints_rad = []
for joint in start_joints_deg:
    start_joints_rad.append( round( joint * (math.pi/180),3) )

# Calculate starting end effector position
start_end_eff = eva.calc_forward_kinematics(start_joints_rad)
init_orient_quat = start_end_eff['orientation']

# Convert end effector orientation from quaterion to euler
init_orient_euler = quaternion_to_euler(init_orient_quat['w'],init_orient_quat['x'],init_orient_quat['y'],init_orient_quat['z'])

# Create orientation object that is perpendicular to the floor,
new_quat = euler_to_quaternion(init_orient_euler[0],init_orient_euler[1],3.14) #yaw, pitch, roll
start_end_eff['orientation'] = {'w': new_quat[0], 'x': new_quat[1], 'y': new_quat[2], 'z': new_quat[3]}
start_end_eff['position']['z'] -= 0.01

#find joint angles associate with end effector positon with same, x,y,z, but adjusted orientation.
updated_start_joints = eva.calc_inverse_kinematics(start_joints_rad, start_end_eff['position'], start_end_eff['orientation'])['ik']['joints']

#load drawn points from Fusion 360
points, motion_type = load(file_path)
print(points)
#Functions to turn points to toolpath
parsed_points = parse_fusion_points(points)
waypoints = points_to_waypoints(parsed_points,start_end_eff,updated_start_joints, eva)
toolpath = waypoints_to_toolpath(waypoints, motion_type)

for i in toolpath["waypoints"]:
    print(i)
for j in toolpath["timeline"]:
    print(j)
# Run tool path
with eva.lock():
    eva.control_wait_for_ready()
    eva.toolpaths_use(toolpath)
    eva.control_home()
    eva.control_run(loop=1)
