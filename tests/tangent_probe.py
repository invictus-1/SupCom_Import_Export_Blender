import sys, os
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, scmlib
from mathutils import Vector, Matrix
bpy.ops.wm.read_factory_settings(use_empty=True)
import supcom_importer as imp; imp.register()
for p in sys.argv[2:]:
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    bpy.ops.import_scene.scm(filepath=p)
    me=[o for o in bpy.data.objects if o.type=='MESH'][0].data
    src=scmlib.read_scm(p)
    X=Matrix(([1,0,0],[0,0,-1],[0,1,0]))   # exporter's blender->supcom (row-vector convention)
    me.calc_tangents(uvmap='UVMap')
    nd=[];t1=[];b1=[];t2=[];b2=[]
    for l in me.loops:
        v=src["verts"][l.vertex_index]
        if Vector(v["tan"]).length<0.5: continue
        n=(l.normal@X); t=(l.tangent@X); b=(l.bitangent@X)
        nd.append(n.dot(Vector(v["nrm"])))
        t1.append(t.dot(Vector(v["tan"]))); b1.append(b.dot(Vector(v["bin"])))
        t2.append(t.dot(Vector(v["bin"]))); b2.append(b.dot(Vector(v["tan"])))
    m=lambda x: round(sum(x)/len(x),4)
    f=lambda x: round(sum(1 for y in x if y>0.95)/len(x),3)
    print(os.path.basename(p), 'normal',m(nd),'| tan.tan',m(t1),f(t1),'bit.bin',m(b1),f(b1),'| tan.bin',m(t2),'bit.tan',m(b2))
