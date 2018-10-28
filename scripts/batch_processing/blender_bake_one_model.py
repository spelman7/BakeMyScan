"""
Remesh one scan to a lowpoly version

Usage:
blender --background --python bakeOne.py -- -i INFILE -o OUTFILE [-t TARGETFACES] [-r RESOLUTION] [-a ALBEDO] [-n NORMAL]

For instance, to remesh scan.obj to 500 triangles and save the resulting mesh to scan01.fbx associated with 2048px images:
blender --background --python bakeOne.py -- -i scan.obj -o scan01.fbx -t 500 -r 2048 -a model_albedo.jpg -n model_normals.jpg
"""

import bpy
import sys
import os
import argparse
import imghdr

#Create an arguments parser
parser = argparse.ArgumentParser(description="Remesh a scan to a lowpoly model in blender")
parser.add_argument("-i", "--input",  dest="input",  type=str, metavar='FILE', required=True, help="Input model")
parser.add_argument("-o", "--output", dest="output", type=str, metavar='FILE', required=True, help="Output model")
parser.add_argument("-t", "--target", dest="target", type=int, default=1500,   help="Target number of faces")
parser.add_argument("-r", "--resolution", dest="resolution", type=int, default=1024, help="Baked textures resolution")
parser.add_argument("-a", "--albedo", dest="albedo", type=str, metavar='FILE', help="Albedo texture")
parser.add_argument("-n", "--normal", dest="normal", type=str, metavar='FILE', help="Normal texture")

#Parse the arguments
argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)

#Check their validity
if not os.path.exists(args.input):
    print("ERROR: " + args.input + " is not a valid file")
    sys.exit(1)
args.input = os.path.abspath(args.input)
if args.output.split(".")[-1]!="fbx":
    print("ERROR: " + args.output + " must be a .fbx file")
    sys.exit(1)
args.output = os.path.abspath(args.output)

#Remove the delete file objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

#Switch to Cycles
bpy.context.scene.render.engine = "CYCLES"

#Import the base scan model
bpy.ops.bakemyscan.import_scan(filepath = args.input)

#Preprocess it
bpy.ops.bakemyscan.clean_object()

#Add a material with the albedo and normal slots
bpy.ops.bakemyscan.create_empty_material()
if args.albedo is not None:
    bpy.ops.bakemyscan.assign_texture(slot="albedo", filepath=args.albedo)
if args.normal is not None:
    bpy.ops.bakemyscan.assign_texture(slot="normal", filepath=args.normal)

#Get the interesting stuff
hr = bpy.context.active_object

#Remesh the object
bpy.ops.bakemyscan.remesh_iterative(limit=args.target)

#Unwrap the lowpoly model
bpy.ops.bakemyscan.unwrap(method="smarter")

#Select the two models to bake
hr.select=True

#Bake
bpy.ops.bakemyscan.bake_textures(
    resolution    = args.resolution,
    bake_albedo   = (args.albedo!=""),
    bake_geometry = True,
    bake_surface  = (args.normal!="")
)

#Export
hr.select = False
bpy.ops.bakemyscan.export_fbx(filepath=args.output)
