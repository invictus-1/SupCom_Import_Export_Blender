import sys, os, json, math, traceback
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh, scmlib
from mathutils import Vector, Matrix
out = sys.argv[2]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
import supcom_importer as imp, supcom_exporter as exp
imp.register(); exp.register()
R = {}
try:
    # armature: root "TestShip" + child "Turret" (identity object transform, as the wiki/handoff recommend)
    ad = bpy.data.armatures.new("TestShip"); ao = bpy.data.objects.new("TestShip", ad)
    bpy.context.scene.collection.objects.link(ao); bpy.context.view_layer.objects.active = ao
    bpy.ops.object.mode_set(mode='EDIT')
    r = ad.edit_bones.new("TestShip"); r.head = (0, 0, 0); r.tail = (0, 1, 0)
    t = ad.edit_bones.new("Turret"); t.head = (0, 0.5, 1); t.tail = (0, 1.5, 1); t.parent = r
    bpy.ops.object.mode_set(mode='OBJECT')
    # hull: a box (quads) with one sharp edge, smooth shading; turret: a cylinder with ngon caps
    me = bpy.data.meshes.new("hull"); bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.3, radius2=0.3, depth=0.4,
                          matrix=Matrix.Translation((0, 0.5, 1.0)))
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new("hull", me); bpy.context.scene.collection.objects.link(ob)
    ob.location = (0.0, 0.0, 0.25)   # un-applied object transform on purpose
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(); bpy.ops.object.mode_set(mode='OBJECT')
    me.shade_smooth()
    me.edges[0].use_edge_sharp = True
    gr = ob.vertex_groups.new(name="TestShip"); gt = ob.vertex_groups.new(name="Turret")
    gr.add([v.index for v in me.vertices if v.co.z < 0.75], 1.0, 'REPLACE')
    gt.add([v.index for v in me.vertices if v.co.z >= 0.75], 1.0, 'REPLACE')
    ob.parent = ao; mod = ob.modifiers.new("Armature", 'ARMATURE'); mod.object = ao
    R["blender"] = dict(verts=len(me.vertices), faces=len(me.polygons), ngons=sum(p.loop_total > 4 for p in me.polygons),
                        tris=sum(p.loop_total - 2 for p in me.polygons))
    world = [ob.matrix_world @ v.co for v in me.vertices]

    bpy.ops.object.select_all(action='DESELECT'); ao.select_set(True); bpy.context.view_layer.objects.active = ao
    bpy.ops.export_mesh.scm(directory=out + '/')
    m = scmlib.read_scm(os.path.join(out, "TestShip.scm"))
    X = exp.xy_to_xz_transform.to_3x3()
    exp_world = {tuple(round(c, 4) for c in (Vector(v["pos"]) @ X.inverted())) for v in m["verts"]}
    want = {tuple(round(c, 4) for c in p) for p in world}
    R["scm"] = dict(verts=len(m["verts"]), tris=len(m["tris"]), bones=[b["name"] for b in m["bones"]],
                    parents=[b["parent"] for b in m["bones"]], weighted=m["weighted"],
                    world_positions_match=exp_world == want,
                    unit_normals=all(abs(Vector(v["nrm"]).length - 1) < 1e-3 for v in m["verts"]),
                    unit_tangents=sum(abs(Vector(v["tan"]).length - 1) < 1e-3 for v in m["verts"]) / len(m["verts"]))
    # animation: turret yaws 90 degrees over 24 frames
    ao.rotation_mode = 'QUATERNION'
    bpy.ops.object.mode_set(mode='POSE'); pb = ao.pose.bones["Turret"]; pb.rotation_mode = 'QUATERNION'
    sc = bpy.context.scene; sc.frame_start, sc.frame_end = 1, 24
    for f, ang in ((1, 0), (24, 90)):
        sc.frame_set(f); pb.rotation_quaternion = Matrix.Rotation(math.radians(ang), 4, 'Y').to_quaternion()
        pb.keyframe_insert("rotation_quaternion"); pb.keyframe_insert("location")
    bpy.ops.object.mode_set(mode='OBJECT')
    act = ao.animation_data.action; act.name = "TestShip_Aturn"
    tr = ao.animation_data.nla_tracks.new(); tr.strips.new(act.name, 1, act)
    bpy.ops.export_anim.sca(directory=out + '/')
    a = scmlib.read_sca(os.path.join(out, "TestShip_Aturn.sca"))
    tb = a["names"].index("Turret") if "Turret" in a["names"] else None
    R["sca"] = dict(frames=len(a["frames"]), bones=a["names"], links=a["links"],
                    turret_rot_first=[round(x, 3) for x in a["frames"][0]["bones"][tb][3:7]] if tb is not None else None,
                    turret_rot_last=[round(x, 3) for x in a["frames"][-1]["bones"][tb][3:7]] if tb is not None else None)
    # re-import both into a clean scene
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for a_ in list(bpy.data.actions): bpy.data.actions.remove(a_)
    bpy.ops.import_scene.scm(filepath=os.path.join(out, "TestShip.scm"))
    bpy.ops.import_anim.sca(filepath=os.path.join(out, "TestShip_Aturn.sca"))
    ao2 = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
    bpy.context.scene.frame_set(24)
    q = ao2.pose.bones["Turret"].matrix.to_quaternion()
    R["reimport"] = dict(objects=sorted(o.name for o in bpy.data.objects), turret_world_rot_f24=[round(x, 3) for x in q])
except Exception:
    R["error"] = traceback.format_exc(limit=6)
print("RESULT " + json.dumps(R))
