import bpy
import os
from . import fn_nodes
from . import fn_soft
from . import fn_bake
import numpy as np
import collections
import time

class bake_cycles_textures_nodes(bpy.types.Operator):
    bl_idname = "bakemyscan.bake_textures_nodes"
    bl_label  = "Textures to textures via nodes"
    bl_options = {"REGISTER", "UNDO"}

    resolution: bpy.props.IntProperty( name="resolution",     description="image resolution", default=1024, min=128, max=8192)
    cageRatio: bpy.props.FloatProperty(name="cageRatio",     description="baking cage size as a ratio", default=0.02, min=0.00001, max=5)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        box = self.layout.box()
        box.prop(self, "resolution", text="Image resolution")
        box.prop(self, "cageRatio",  text="Relative cage size")

    @classmethod
    def poll(self, context):
        #Render engine must be cycles
        if bpy.context.scene.render.engine!="CYCLES":
            return 0
        #Object mode
        if context.mode!="OBJECT":
            return 0
        #If more than two objects are selected
        if len(context.selected_objects)<2:
            return 0
        #If no object is active
        if context.active_object is None:
            return 0
        #If something other than a MESH is selected
        for o in context.selected_objects:
            if o.type != "MESH":
                return 0
        #The source object must have correct materials
        sources = [o for o in context.selected_objects if o!=context.active_object]
        target = context.active_object

        #Each material must be not None and have nodes
        for source in sources:
            if source.active_material is None:
                return 0
            if source.active_material.use_nodes == False:
                return 0
        #The target object must have a UV layout
        # if len(target.data.uv_layers) == 0:
        #     return 0
        return 1


    def execute(self, context):
        #Find which object is the source and which is the target
        target  = context.active_object
        sources = [o for o in context.selected_objects if o!=target]

        # Add new BDSF material
        mat_name = 'LowPolyMat'
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        if target.data.materials:
            target.data.materials[0] = mat
        else:
            target.data.materials.append(mat)

        # UV Unwrap
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = target
        target.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action = 'SELECT')
        bpy.ops.mesh.uv_texture_add()
        bpy.context.object.data.uv_layers["UVMap"].active_render = True
        bpy.ops.uv.smart_project(angle_limit=66.0, island_margin=0.1)
        print("Smart Projection complete.")
        bpy.ops.object.mode_set(mode='OBJECT')

        # # New image
        imageName = 'img'
        image = bpy.data.images.new(imageName, self.resolution, self.resolution)

        # # Setup Image Texture Node
        image_tex_node = mat.node_tree.nodes.new(type="ShaderNodeTexImage")
        image_tex_node.image = image

        bpy.ops.object.select_all(action='DESELECT')
        sources[0].select_set(True)
        target.select_set(True)
        bpy.context.view_layer.objects.active = target

        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.bake.use_selected_to_active = True
        bpy.context.scene.cycles.bake_type = 'DIFFUSE'
        bpy.context.scene.render.bake.cage_extrusion = self.cageRatio
        bpy.context.scene.render.bake.use_pass_indirect = False
        bpy.context.scene.render.bake.use_pass_direct = False

        print("Baking...")
        t0 = time.time()
        bpy.ops.object.bake(type='DIFFUSE')

        print("Baking finished in %f seconds." % (time.time() - t0))

        principledNode = mat.node_tree.nodes["Principled BSDF"]
        links.new(principledNode.inputs["Base Color"], image_tex_node.outputs["Color"])

        # self.report({'INFO'}, "Baking successful")
        return{'FINISHED'}

def register() :
    bpy.utils.register_class(bake_cycles_textures_nodes)

def unregister() :
    bpy.utils.unregister_class(bake_cycles_textures_nodes)