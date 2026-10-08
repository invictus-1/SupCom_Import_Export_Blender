"""Exporter must refuse a mesh with more than 80 weighted bones (game shader limit) and accept 80."""
import sys, os; sys.path.insert(0, sys.argv[1])
import bpy, bmesh
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import supcom_exporter as exp; exp.register()
def build(n, name):
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    ad = bpy.data.armatures.new(name); ao = bpy.data.objects.new(name, ad); bpy.context.scene.collection.objects.link(ao)
    bpy.context.view_layer.objects.active = ao
    with bpy.context.temp_override(active_object=ao, object=ao, selected_objects=[ao]):
        bpy.ops.object.mode_set(mode='EDIT')
        root = ad.edit_bones.new(name); root.head = (0, 0, 0); root.tail = (0, 1, 0)
        for i in range(n - 1):
            b = ad.edit_bones.new("B%03d" % i); b.head = (i, 0, 0); b.tail = (i, 1, 0); b.parent = root
        bpy.ops.object.mode_set(mode='OBJECT')
    me = bpy.data.meshes.new("m"); bm = bmesh.new()
    for i in range(n):
        bmesh.ops.create_cube(bm, size=0.5, matrix=__import__('mathutils').Matrix.Translation((i, 0, 0)))
    bm.to_mesh(me); bm.free()
    me.uv_layers.new(name="UVMap")
    ob = bpy.data.objects.new("m", me); bpy.context.scene.collection.objects.link(ob); ob.parent = ao
    names = [name] + ["B%03d" % i for i in range(n - 1)]
    for i, nm in enumerate(names):
        g = ob.vertex_groups.new(name=nm); g.add(list(range(i * 8, i * 8 + 8)), 1.0, 'REPLACE')
    ao.select_set(True); bpy.context.view_layer.objects.active = ao
    with bpy.context.temp_override(active_object=ao, object=ao, selected_objects=[ao]):
        bpy.ops.export_mesh.scm(directory=out + '/')
    return os.path.exists(os.path.join(out, name + ".scm"))
print("RESULT 80 bones exported:", build(80, "T80"), "| 81 bones exported:", build(81, "T81"))
