SupCom_Import_Export_Blender
============================

Python scripts to import and export Supreme Commander units (.scm) and animations (.sca) in Blender.

Blender 5.x (version 0.6.0)
------

Both add-ons work on Blender 5.x (tested on 5.2 LTS). Install each .py with Edit > Preferences > Add-ons >
(menu at the top right) Install from Disk, then enable it. What changed from 0.5.x:

- Importer: enabling it failed on Blender 5 ("No module named 'bgl'"); the unused import is gone. File reading uses
  explicit little-endian formats (bone records were misread off Windows). Imported meshes keep the file's own vertex
  normals, so they shade like in game. Error popups work again. Works when driven from Python scripts.
- Exporter: animation export works again (Blender 5.0 removed `Action.fcurves`; keyed bones are now read through
  slotted actions). Normals and tangents come from Blender itself (corner normals + MikkTSpace), so the game shows
  exactly what the viewport shows: smooth/flat shading, sharp edges and custom normals are all respected, and normal
  maps line up. Clear error past the format's 65535-vertex limit; warning if the armature has unapplied transforms.

Checked by round-tripping models from the game files (import -> export -> compare with the original): on models
authored by GPG, exported normals match the originals at 1.000 (mean dot product) on 8 of 9 models, against
0.86-1.00 for 0.5.9, and tangents at 0.97-1.00 on 8 of 9 (0.5.9: as low as 0.50). Bones and animations re-export
within 3e-5. The scripts in `tests/` repeat these checks headless with the `bpy` module from PyPI
(`pip install bpy==5.2.2`, then `python tests/roundtrip.py <folder with the add-ons> <output folder> <model.scm> [anim.sca]`;
the add-ons need to be importable as `supcom_importer` / `supcom_exporter`, e.g. copies with underscores).

Setting up the plugins :
------

Download the importer and exporter files from the github repo. They are counted as separate plugins.

On Blender 5.x use Install from Disk as described above. Otherwise these scripts are installed just like other blender plugins:
You can then place them into your plugins directory: `BlenderInstallDir/BlenderVersion/scripts/addons`
Then you can enable them in the user preferences, in the plugins section. There will be two plugins, import and export, under the Import/Export category.

Importing :
------
- You can import .scm models from Supreme commander, find the corresponding model in the game files (units.scd)

- To import animations (.sca), you have to have already loaded a model on Blender, either the corresponding mesh (.scm), or a custom mesh of your own, with the bones corresponding in names with the animation bones (each bone named in the animation must have a corresponding one with the same name in the mesh).

- Animation import is functional, but due to supcom file format reasons, the file is filled with keyframes for every frame, making it nearly impossible to edit.

Exporting :
------

- The exporter deals with one armature at a time. You can hide any armatures you dont want to be taken into account.

- All vertices must be in a "Vertex Group", and each vertex group must have the name of a bone. If some vertices are not moving, just assign them to the group with the base bone as bonename. The exporter will put you into edit mode and select all non-assigned vertices if your mesh contains them.

- When exporting, the script will assume the unit name (and so the .scm filename) from the name of your armature. So you'll have only to select the output folder, filenames will be deduced.

- It is recommended to triangulate the mesh. Quads and ngons are now supported, but in general triangulating gives more control over the mesh.

- Shading is taken from Blender as you see it: smooth/flat faces, sharp edges and custom normals all carry over. A vertex is only split where its corners differ in UV, normal or tangent.

known bugs :
- Models exported by this will work fine in the game, but importing them into 3dsMax with the 3ds importer is erratic and buggy due to how blender orders its vertices. I have a partial fix in another repository for the 3ds exporter here:

Exporting Animations :
------

- When exporting, the script will assume the filename for the animation from the action name in Blender (can be seen in the NLA editor). So you'll have only to select the output folder, filenames will be deduced.

- When exporting animations, you need to have the armature with that animation selected.

- An animation must be associated with an action (see the NLA editor).

- Multiple animations are now supported: the exporter will export each animation in your model separately.

Old blender versions :
------
If you are using blender 2.79 there is a version of the plugin on the 2.79 branch, though it has fewer features so using it isn't recommended.

Credits to dan & Brent for the original version and all the engineering work. Thanks to Oygron for porting it to 2.71.
