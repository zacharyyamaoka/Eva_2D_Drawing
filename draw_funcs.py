
from automata.Eva import Eva
import time
import json
import logging
import math

def load(path):
    with open(path, "r") as file1:
        lines = file1.readlines()
        lines = lines[0].split(',')
        if lines[-1] == "":
            del lines[-1]
    n = len(lines)
    points = []
    motion_type = []
    for i in range(n):
        if (i + 1) % 4 == 0:
            motion_type.append(lines[i])
        else:
            points.append(float(lines[i]))

    return points,motion_type

def switch_axis(point):
    #trasnform to Cheroeagraph Reference Frame
    # in: x,y,z
    #out: x,z,y - chorea graph moves on xz plane
    return [point[1],-point[0],point[2]]

def fusion_to_eva_units(val):
    #cm to m
    return round(val/100,3)

def parse_fusion_points(points):
    parsed_points = []
    n = len(points)
    for i in range(n//3):
        p = []
        for j in range(3):
            ind = (i*3)+j

            p.append(fusion_to_eva_units(points[ind]))
        p = switch_axis(p)
        parsed_points.append(p)
    return parsed_points


def quaternion_to_euler(w, x, y, z):

        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        X = math.atan2(t0, t1)

        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        Y = math.asin(t2)

        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        Z = math.atan2(t3, t4)

        return Z, Y, X

def euler_to_quaternion(yaw, pitch, roll):

        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)

        return [qw, qx, qy, qz]

def points_to_waypoints(points,start_end_eff,start_joints,EVA):

    offset_x = start_end_eff["position"]["x"] - points[0][0]
    offset_y = start_end_eff["position"]["y"] - points[0][1]
    offset_z = start_end_eff["position"]["z"] - points[0][2]

    num = len(points)
    for i in range(num):
        points[i][0] += offset_x
        points[i][1] += offset_y
        points[i][2] += offset_z

    for i in range(num-1):

        x =points[i][0] - points[i+1][0]
        y = points[i][1] - points[i+1][1]
        z = points[i][2] - points[i+1][2]

    waypoints = []
    guess = start_joints

    max_step = 0.01

    for i in range(num):

        if i != 0:
            orientation = start_end_eff["orientation"]

            diff_x = (points[i][0]-points[i-1][0])
            diff_y = (points[i][1]-points[i-1][1])
            diff_z = (points[i][2]-points[i-1][2])
            L2_distance = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)

            t_x = math.ceil(abs(diff_x)/max_step)
            t_y = math.ceil(abs(diff_y)/max_step)
            t_z = math.ceil(abs(diff_z)/max_step)

            max_divide = max(t_x,t_y)
            max_divide = max(max_divide,t_z)

            step_x = diff_x/max_divide
            step_y = diff_y/max_divide
            step_z = diff_z/max_divide

            starting_point = {"x": points[i-1][0], "y": points[i-1][1], "z": points[i-1][2]}
            for step in range(int(max_divide)):

                    starting_point["x"] += step_x
                    starting_point["y"] += step_y
                    starting_point["z"] += step_z
                    result = EVA.calc_inverse_kinematics(guess, starting_point, orientation)
                    joint_angles = result['ik']['joints']
                    guess = joint_angles

        else: #calculate directly
            position = {"x": points[i][0], "y": points[i][1], "z": points[i][2]}
            orientation = start_end_eff["orientation"]
            result = EVA.calc_inverse_kinematics(guess, position, orientation)
            joint_angles = result['ik']['joints']
            guess = joint_angles
        waypoints.append(joint_angles)

    return waypoints


def waypoints_to_toolpath(waypoints, motion_type, speed = 0.15):

    num = len(waypoints)
    toolpath = {
        "metadata":{
            "default_velocity":speed,
            "next_label_id":num+2,
            "analog_modes":{ "i0":"voltage", "i1":"voltage", "o0":"voltage", "o1":"voltage" }
        }
    }

    waypoints_dict = []
    timeline_dict = []

    for n in range(num):
        waypoints_dict.append({ "label_id":n+1 , "joints":waypoints[n]})
        if n == 0:
            timeline_dict.append( { "type":"home", "waypoint_id":n})
        else:
            # val = "false"
            pass_val = False
            motion_val = "linear"

            if motion_type[n] == "spline":
                pass_val = True
            if motion_type[n-1] == "spline":
                motion_val = "spline"

            timeline_dict.append( { "type":"trajectory","pass_through":pass_val, "trajectory": motion_val, "waypoint_id":n})

    toolpath["waypoints"] = waypoints_dict
    toolpath["timeline"] = timeline_dict

    return toolpath
