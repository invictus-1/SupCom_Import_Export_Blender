"""Round-trip test in headless Blender:  python roundtrip.py <addon dir> <out dir> <model.scm> [anim.sca]
Imports the game file with the add-on, exports it again, parses both with scmlib and compares."""
import sys, os, math, json, traceback
addon_dir, out_dir, scm_path = sys.argv[1], sys.argv[2], sys.argv[3]
sca_path = sys.argv[4] if len(sys.argv) > 4 else None
sys.path.insert(0, addon_dir); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Quaternion
import scmlib

bpy.ops.wm.read_factory_settings(use_empty=True)
import supcom_importer as imp, supcom_exporter as exp
imp.register(); exp.register()
os.makedirs(out_dir, exist_ok=True)
R = {"model": os.path.basename(scm_path)}


def arm():
    return [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]


try:
    bpy.ops.import_scene.scm(filepath=scm_path)
    a = arm(); me = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    src = scmlib.read_scm(scm_path)
    R["imported"] = dict(verts=len(me.data.vertices), tris=len(me.data.polygons), bones=len(a.data.bones),
                         src_verts=len(src["verts"]), src_tris=len(src["tris"]), src_bones=len(src["bones"]))
    # custom normals landed? compare Blender corner normals with the file's normals (axis-swapped)
    rot3 = imp.xy_to_xz_transform.to_3x3()
    cn = me.data.corner_normals
    dots = [cn[l.index].vector.dot((Vector(src["verts"][l.vertex_index]["nrm"]) @ rot3).normalized())
            for l in me.data.loops]
    R["import_normals_mean_dot"] = round(sum(dots) / len(dots), 4)

    bpy.ops.object.select_all(action='DESELECT'); a.select_set(True); bpy.context.view_layer.objects.active = a
    bpy.ops.export_mesh.scm(directory=out_dir + '/')
    out_scm = os.path.join(out_dir, a.name + '.scm')
    dst = scmlib.read_scm(out_scm)

    # bones by name
    sb = {b["name"]: b for b in src["bones"]}; db = {b["name"]: b for b in dst["bones"]}
    pname = lambda bl, b: bl[b["parent"]]["name"] if b["parent"] >= 0 else None
    worst = dict(pos=0, rot=0, rpi=0); parent_bad = []
    for n, b in sb.items():
        if n not in db: parent_bad.append(n + ':missing'); continue
        c = db[n]
        if pname(src["bones"], b) != pname(dst["bones"], c): parent_bad.append(n)
        worst["pos"] = max(worst["pos"], max(abs(x - y) for x, y in zip(b["pos"], c["pos"])))
        q1, q2 = Quaternion(b["rot"]).normalized(), Quaternion(c["rot"]).normalized()
        worst["rot"] = max(worst["rot"], 1 - abs(q1.dot(q2)))
        worst["rpi"] = max(worst["rpi"], max(abs(x - y) for x, y in zip(b["rpi"], c["rpi"])))
    R["bones"] = dict(src=len(sb), dst=len(db), weighted_src=src["weighted"], weighted_dst=dst["weighted"],
                      parent_mismatch=parent_bad[:5], worst={k: round(v, 6) for k, v in worst.items()})

    # vertices: match each source vertex to exported vertices at the same position + uv
    key = lambda v: (round(v["pos"][0], 3), round(v["pos"][1], 3), round(v["pos"][2], 3),
                     round(v["uv"][0], 3), round(v["uv"][1], 3))
    dmap = {}
    for v in dst["verts"]: dmap.setdefault(key(v), []).append(v)
    found = 0; nd = []; td = []; bd = []; bone_ok = 0
    dbn = [b["name"] for b in dst["bones"]]; sbn = [b["name"] for b in src["bones"]]
    for v in src["verts"]:
        cands = dmap.get(key(v))
        if not cands: continue
        found += 1
        best = max(cands, key=lambda c: (dbn[c["bone"]] == sbn[v["bone"]], Vector(c["nrm"]).dot(Vector(v["nrm"]))))
        nd.append(Vector(best["nrm"]).dot(Vector(v["nrm"])))
        if Vector(v["tan"]).length > 0.5 and Vector(best["tan"]).length > 0.5:
            td.append(Vector(best["tan"]).dot(Vector(v["tan"]))); bd.append(Vector(best["bin"]).dot(Vector(v["bin"])))
        bone_ok += dbn[best["bone"]] == sbn[v["bone"]]
    mean = lambda x: round(sum(x) / len(x), 4) if x else None
    frac = lambda x, t: round(sum(1 for y in x if y > t) / len(x), 4) if x else None
    R["verts"] = dict(src=len(src["verts"]), dst=len(dst["verts"]), matched=found, tris_src=len(src["tris"]),
                      tris_dst=len(dst["tris"]), bone_match=round(bone_ok / max(found, 1), 4),
                      normal_mean_dot=mean(nd), normal_frac_gt_0_99=frac(nd, 0.99),
                      tangent_mean_dot=mean(td), binormal_mean_dot=mean(bd), tangent_frac_gt_0_9=frac(td, 0.9))

    if sca_path:
        bpy.ops.import_anim.sca(filepath=sca_path)
        a = arm(); act = a.animation_data.action
        R["anim_import"] = dict(action=act.name, slots=len(act.slots), frame_end=bpy.context.scene.frame_end)
        tr = a.animation_data.nla_tracks.new(); tr.strips.new(act.name, 1, act)
        bpy.ops.object.select_all(action='DESELECT'); a.select_set(True); bpy.context.view_layer.objects.active = a
        bpy.ops.export_anim.sca(directory=out_dir + '/')
        out_sca = os.path.join(out_dir, act.name + '.sca')
        s, d = scmlib.read_sca(sca_path), scmlib.read_sca(out_sca)
        common = [n for n in s["names"] if n in d["names"]]
        wp = wr = 0
        for fs, fd in zip(s["frames"], d["frames"]):
            for n in common:
                bs, bdd = fs["bones"][s["names"].index(n)], fd["bones"][d["names"].index(n)]
                wp = max(wp, max(abs(x - y) for x, y in zip(bs[0:3], bdd[0:3])))
                wr = max(wr, 1 - abs(Quaternion(bs[3:7]).normalized().dot(Quaternion(bdd[3:7]).normalized())))
        R["anim"] = dict(src_frames=len(s["frames"]), dst_frames=len(d["frames"]), src_bones=len(s["names"]),
                         dst_bones=len(d["names"]), common=len(common), worst_pos=round(wp, 5), worst_rot=round(wr, 6))
except Exception:
    R["error"] = traceback.format_exc(limit=6)
print("RESULT " + json.dumps(R))
