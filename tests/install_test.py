import sys, bpy, addon_utils, tempfile, os
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in sys.argv[1:]:
    bpy.ops.preferences.addon_install(filepath=f, overwrite=True)
    mod = os.path.splitext(os.path.basename(f))[0]
    r = bpy.ops.preferences.addon_enable(module=mod)
    print("ENABLE", mod, r, addon_utils.check(mod))
print("OPS", hasattr(bpy.ops.import_scene, "scm"), hasattr(bpy.ops.export_mesh, "scm"), hasattr(bpy.ops.import_anim, "sca"), hasattr(bpy.ops.export_anim, "sca"))
for m in addon_utils.modules():
    if 'supcom' in m.__name__: print("BLINFO", m.__name__, m.bl_info["name"], m.bl_info["version"])
