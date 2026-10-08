"""Regression for scripted use: load an empty file and import in the same script, with nothing active or selected."""
import sys, os; sys.path.insert(0, sys.argv[1])
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
import supcom_importer as imp; imp.register()
bpy.ops.wm.read_homefile(use_empty=True)
bpy.context.view_layer.objects.active = None
r = bpy.ops.import_scene.scm(filepath=sys.argv[2])
arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]; me = [o for o in bpy.data.objects if o.type == 'MESH'][0]
print("RESULT", r, "parent ok", me.parent == arm, "modifier", [(m.type, m.object.name) for m in me.modifiers], "bones", len(arm.data.bones))
