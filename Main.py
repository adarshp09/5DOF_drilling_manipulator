import math
import numpy as np
import bpy
from bpy.app.handlers import persistent
import sys

q1 = float()
q2 = float()
d1 = 0.0

m = 0.10
a1 = 0.125
a2 = 0.14


PARAMS = {
    "q1": {"kind": "angle",    "min": 0,  "max":  180},
    "q2": {"kind": "angle",    "min": -160.0, "max": 160.0},
    "q3": {"kind": "angle",    "min": 0, "max": 360},
    "d1": {"kind": "distance", "min":   0.0,   "max":  0.1},
    "d2": {"kind": "distance", "min":   0.0,   "max":  0.1},
}


start = [0.1,0.3]

targets = []



for i in range(4):
    targets.append([0.1-(i*0.05),0.3])

for j in range(4):
    targets.append([0.05-(j*0.05),0.25])

for k in range(4):
    targets.append([0.1-(k*0.05),0.2])
    


def inverseZY(x, z, y, a1, a2, d1, m):
    # radial distance in y–z plane
    R2 = z*z + y*y
    R = math.sqrt(R2)

    # feasible range for the second link length
    L2_min = max(abs(R - a1), a2)
    L2_max = min(R + a1, a2 + m)

    if L2_min > L2_max:
        print("inverseZY: No possible solution")
        return None

    # choose the "shortest" extension
    L2 = L2_min

    # --- correct law of cosines for q2 ---
    cos_q2 = (R2 - a1*a1 - L2*L2) / (2 * a1 * L2)
    cos_q2 = max(-1.0, min(1.0, cos_q2))
    
    if y>0:
        q2 = math.acos(cos_q2)   # radians
    else:
        q2 = -math.acos(cos_q2)   # radians
    
    # --- compute q1 using standard 2-link geometry ---
    # angle from base to target
    phi = math.atan2(z, y)
    # angle inside the triangle

    psi = math.atan2(-1 * L2 * math.sin(q2), a1 + L2 * math.cos(q2))
    q1 = phi - psi

    d1_val = L2 - a2
    
    if x<0:
        q3_val = 180
    else:
        q3_val = 0
        

    return {
        "L2": L2,
        "q2": math.degrees(q2),
        "q1": math.degrees(q1),
        "d1": d1_val,
        "q3": q3_val
    }
    

def set_controller_prop(prop_name, value, controller_name="Controller"):
    con = bpy.data.objects.get(controller_name)
    if con is None:
        raise KeyError(f"No object named '{controller_name}'")
    meta = PARAMS.get(prop_name)
    if meta is None:
        raise KeyError(f"Unknown property '{prop_name}'")

    # clamp
    v = float(value)
    v = max(meta["min"], min(meta["max"], v))

    # convert/store (angles -> radians)
    if meta["kind"] == "angle":
        stored = math.radians(v)
    else:
        stored = v  # distance or plain float

    # write to property (may raise if driven/locked)
    try:
        con[prop_name] = stored
    except Exception as e:
        raise RuntimeError(f"Cannot write property '{prop_name}': {e}")

    # ensure _RNA_UI exists (assigning a dict to a key is fine)
    if "_RNA_UI" not in con:
        con["_RNA_UI"] = {}

    # prepare UI metadata (Blender expects radians for ANGLE subtype)
    if meta["kind"] == "angle":
        ui_meta = {
            "min": math.radians(meta["min"]),
            "max": math.radians(meta["max"]),
            "soft_min": math.radians(meta["min"]),
            "soft_max": math.radians(meta["max"]),
            "subtype": "ANGLE",
            "step": 1.0,
            "precision": 3,
        }
    else:  # distance
        ui_meta = {
            "min": float(meta["min"]),
            "max": float(meta["max"]),
            "soft_min": float(meta["min"]),
            "soft_max": float(meta["max"]),
            "subtype": "DISTANCE",
            "step": 1.0,
            "precision": 3,
        }

    # assign metadata (replace only this property's metadata)
    con["_RNA_UI"][prop_name] = ui_meta
    
def animate_solution(solution, start_frame=1, end_frame=20, controller_name="Controller"):
    print("animate_solution: start")

    if solution is None:           
        print("animate_solution: no solution, aborting")
        return

    con = bpy.data.objects.get(controller_name)
    if con is None:
        raise KeyError(f"No object named '{controller_name}'")

    scene = bpy.context.scene

    # kyframe at start_frame
    print(f"animate_solution: keyframing current pose at frame {start_frame}")
    scene.frame_set(start_frame)
    for name in ("q1", "q2","q3","d1"):
        if name in PARAMS:
            con.keyframe_insert(data_path=f'["{name}"]', frame=start_frame)
    set_controller_prop("d2", 0, controller_name)
    con.keyframe_insert(data_path=f'["d2"]', frame=start_frame)

    #keyframe at end_frame
    print(f"animate_solution: setting target pose at frame {end_frame-10}")
    scene.frame_set(end_frame-10)
    for name in ("q1", "q2", "d1","q3"):
        if name in solution:
            set_controller_prop(name, solution[name], controller_name)
            con.keyframe_insert(data_path=f'["{name}"]', frame=end_frame-10)

    set_controller_prop("d2", 0, controller_name)
    con.keyframe_insert(data_path=f'["d2"]', frame=end_frame-10)

    scene.frame_set(end_frame-5)
    set_controller_prop("d2", 0.1, controller_name)
    con.keyframe_insert(data_path=f'["d2"]', frame=end_frame-5)

    scene.frame_set(end_frame)
    set_controller_prop("d2", 0, controller_name)
    con.keyframe_insert(data_path=f'["d2"]', frame=end_frame)

    print("animate_solution: done")


frame_counter = 0



for target in targets:
    solution = inverseZY(1,target[1], target[0], a1, a2, d1, m)
    animate_solution(solution, frame_counter , frame_counter + 30)
    frame_counter += 35

for target in targets:
    solution = inverseZY(-1,target[1], target[0], a1, a2, d1, m)
    animate_solution(solution, frame_counter , frame_counter + 30)
    frame_counter += 35