import bpy

con = bpy.data.objects.get("Controller")

def update_frame_text(scene):
    
    for name in ["q1","q2","q3","d1","d2"]:
        text_object = bpy.data.objects.get(name)
        if text_object and text_object.type == 'FONT':
            value = round(con[name],3)
            text_object.data.body = f"{name} = {value}"

bpy.app.handlers.frame_change_pre.append(update_frame_text)

