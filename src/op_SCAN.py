# coding: utf8
import bpy
import os
import imghdr
from . import fn_soft
from . import fn_bake
from . import fn_nodes

import shutil


class colmap_auto(bpy.types.Operator):
    bl_idname = "bakemyscan.colmap_auto"
    bl_label  = "Use colmap"
    bl_options = {"REGISTER"}


    mesher: bpy.props.EnumProperty(items= ( ('delaunay', 'delaunay', 'delaunay'), ("poisson", "poisson", "poisson")) , description="Mesher", default="delaunay")
    quality: bpy.props.EnumProperty(items= ( ('low', 'low', 'low'), ("medium", "medium", "medium"), ("high", "high", "high")) , description="Quality", default="medium")
    sparse: bpy.props.BoolProperty(description="Sparse", default=True)
    dense: bpy.props.BoolProperty(description="Dense", default=True)
    single: bpy.props.BoolProperty(description="Single Camera", default=True)
    gpu: bpy.props.BoolProperty(description="GPU", default=True)

    def check(self, context):
        return True
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        self.layout.prop(self, "gpu",     text="GPU")
        self.layout.prop(self, "mesher",  text="Mesher")
        self.layout.prop(self, "quality", text="Quality")
        self.layout.prop(self, "sparse",  text="Sparse")
        self.layout.prop(self, "single",  text="Single Camera")
        if self.gpu:
            self.layout.prop(self, "dense",   text="Dense")
        else:
            self.layout.label("Dense reconstruction needs a CUDA GPU")
        col = self.layout.column(align=True)

    @classmethod
    def poll(self, context):
        #Need to be in Cycles render mode
        D = bpy.types.Scene.imagesdirectory
        if D=="":
            return 0
        if not os.path.exists(D):
            return 0
        if len([imghdr.what(os.path.join(D,x)) for x in os.listdir(D) if not os.path.isdir(os.path.join(D,x))]) == 0:
            return 0
        if bpy.types.Scene.executables["colmap"] == "":
            return 0
        return 1

    def execute(self, context):
        self.results = fn_soft.colmap_auto(
            colmap        = bpy.types.Scene.executables["colmap"],
            workspace     = os.path.join(bpy.types.Scene.imagesdirectory, "BakeMyScanRecon"),
            images        = bpy.types.Scene.imagesdirectory,
            mesher        = self.mesher,
            quality       = self.quality,
            sparse        = 1 if self.sparse else 0,
            dense         = 1 if self.dense else 0,
            single_camera = 1 if self.single else 0,
            gpu           = self.gpu
        )
        return{'FINISHED'}



class colmap_openmvs(bpy.types.Operator):
    bl_idname = "bakemyscan.colmap_openmvs"
    bl_label  = "Colmap + OpenMVS"
    bl_options = {"REGISTER"}


    single: bpy.props.BoolProperty(description="Single Camera", default=True)
    gpu: bpy.props.BoolProperty(description="GPU", default=True)
    reconstruct_distance: bpy.props.FloatProperty(description="Pixel distance", default=2.5, min=1., max=20.)
    texture_resolution: bpy.props.IntProperty(description="Scale factor for texturing", default=2, min=0, max=5)
    densify_resolution: bpy.props.IntProperty(description="Scale factor for densifying", default=2, min=0, max=5)
    min_size: bpy.props.IntProperty(description="Minimal texture size", default=640, min=128, max=4096)

    def check(self, context):
        return True
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        box = self.layout.box()
        box.label("Colmap")
        box.prop(self, "single",  text="Single Camera")
        box.prop(self, "gpu",  text="Use GPU")
        box = self.layout.box()
        box.label("OpenMVS")
        box.prop(self, "min_size",             text="Minimal image size")
        box.prop(self, "densify_resolution",   text="Image scale - Densify")
        box.prop(self, "texture_resolution",   text="Image scale - Texture")
        box.prop(self, "reconstruct_distance", text="Min. verts distance (px)")
        col = self.layout.column(align=True)

    @classmethod
    def poll(self, context):
        #Need to be in Cycles render mode
        D = bpy.types.Scene.imagesdirectory
        if D=="":
            return 0
        if not os.path.exists(D):
            return 0
        if len([imghdr.what(os.path.join(D,x)) for x in os.listdir(D) if not os.path.isdir(os.path.join(D,x))]) == 0:
            return 0
        if bpy.types.Scene.executables["colmap"] == "":
            return 0
        if bpy.types.Scene.executables["densifypointcloud"] == "":
            return 0
        if bpy.types.Scene.executables["interfacevisualsfm"] == "":
            return 0
        if bpy.types.Scene.executables["reconstructmesh"] == "":
            return 0
        if bpy.types.Scene.executables["texturemesh"] == "":
            return 0
        if bpy.types.Scene.executables["meshlabserver"] == "":
            return 0
        return 1

    def execute(self, context):

        W = bpy.types.Scene.imagesdirectory

        oldFiles = os.listdir(W)

        #Create a recon directory
        path = os.path.join(W, "BakeMyScanRecon")
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        os.mkdir(path)

        #Run Colmap + OpenMVS
        fn_soft.colmap_openmvs(
            workspace     = W,
            images        = bpy.types.Scene.imagesdirectory,
            colmap=bpy.types.Scene.executables["colmap"],
            interfacevisualsfm = bpy.types.Scene.executables["interfacevisualsfm"],
            densifypointcloud = bpy.types.Scene.executables["densifypointcloud"],
            reconstructmesh = bpy.types.Scene.executables["reconstructmesh"],
            texturemesh = bpy.types.Scene.executables["texturemesh"],
            meshlabserver = bpy.types.Scene.executables["meshlabserver"],
            gpu           = 1 if self.gpu else 0,
            single_camera = 1 if self.single else 0,
            reconstruct_distance=self.reconstruct_distance,
            texture_resolution=self.texture_resolution,
            densify_resolution=self.densify_resolution,
            min_size=self.min_size,
        )

        #Move the results
        for f in os.listdir(W):
            if f not in oldFiles:
                if "BakeMyScanRecon" not in f:
                    os.rename(os.path.join(W, f), os.path.join(path, f))

        #Reimport the files
        bpy.context.scene.render.engine="CYCLES"
        bpy.ops.bakemyscan.import_scan(filepath = os.path.join(path, "result.obj"))
        bpy.ops.bakemyscan.clean_object()
        bpy.ops.bakemyscan.create_empty_material()
        bpy.ops.bakemyscan.assign_texture(slot="albedo", filepath=os.path.join(path, "result.png"))
        return{'FINISHED'}

def bakeAO(mat, nam, res):
    #To blender internal
    restore = mat.use_nodes
    engine  = bpy.context.scene.render.engine
    bpy.context.scene.render.engine="BLENDER_RENDER"
    mat.use_nodes = False
    bpy.context.scene.render.use_bake_to_vertex_color = False


    if bpy.data.images.get(nam):
        bpy.data.images.remove(bpy.data.images.get(nam))
    image = bpy.data.images.new(nam, res, res)

    tex = bpy.data.textures.new( nam, type = 'IMAGE')
    tex.image = image

    for c in range(3):
        if mat.texture_slots[c] is not None:
            mat.texture_slots.clear(c)
    mtex = mat.texture_slots.add()
    mtex.texture = tex
    mtex.texture_coords = 'UV'

    bpy.context.scene.render.use_bake_selected_to_active = False

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.data.screens['UV Editing'].areas[1].spaces[0].image = image
    mat.use_textures[0] = False
    bpy.context.scene.render.bake_type = "AO"
    bpy.ops.object.bake_image()
    bpy.ops.object.editmode_toggle()

    #Do some clean up
    bpy.data.textures.remove(tex)

    #Back to original
    mat.use_nodes = restore
    bpy.context.scene.render.engine=engine
    return image

class delight(bpy.types.Operator):
    bl_idname = "bakemyscan.delight"
    bl_label  = "Quick delighting"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(self, context):
        if len(context.selected_objects)!=1:
            return 0
        if context.active_object.active_material is None:
            return 0
        if not context.active_object.active_material.use_nodes:
            return 0
        return 1

    def execute(self, context):
        mat = context.active_object.active_material
        principleds = fn_bake.get_all_nodes_in_material(mat, node_type="BSDF_PRINCIPLED")
        if len(principleds)==0:
            self.report({"ERROR"}, "The material has no principled shaders")
            return {"CANCELLED"}
        if len(principleds)>1:
            self.report({"ERROR"}, "The material has multiple principled shaders")
            return {"CANCELLED"}

        #Get the interesting variables
        node = principleds[0]
        tree = node["tree"]
        node = node["node"]

        #Get the albedo node
        albedo = tree.nodes.get("albedo")
        if albedo is None:
            self.report({"ERROR"}, "The material does not have an albedo map assigned")
            return {"CANCELLED"}

        #Where is the albedo going?
        sockets = [l.to_socket for l in albedo.outputs["Color"].links]

        #Create the node group
        ao = None
        #Try to find an image in the ao slot
        if tree.nodes.get("ao").image is not None:
            ao = tree.nodes.get("ao").image
        #If it does not already exists, bake it.
        else:
            name = context.active_object.name + "_delighting_ao"
            if bpy.data.images.get(name) is not None:
                ao = bpy.data.images.get(name)
            else:
                ao = bakeAO(mat, name, 2048)
        #Create and link the delighting group node
        _group = tree.nodes.new(type="ShaderNodeGroup")
        _group.node_tree = fn_nodes.node_tree_delight()
        _group.label = _group.name  = "delight"
        _group.inputs["Invert"].default_value = 0.3
        _group.inputs["AO"].default_value     = 0.15

        #Assign the ao texture
        _group.node_tree.nodes["ao"].image = ao

        #Link the group
        tree.links.new(albedo.outputs["Color"], _group.inputs["Color"])
        for socket in sockets:
            tree.links.new(_group.outputs["Color"], socket)

        #Position it
        _group.location = [albedo.location[0] + 100, albedo.location[1]]
        _group.hide=True

        return{'FINISHED'}

def register() :
    bpy.utils.register_class(colmap_auto)
    bpy.utils.register_class(colmap_openmvs)
    bpy.utils.register_class(delight)
def unregister() :
    bpy.utils.unregister_class(colmap_auto)
    bpy.utils.unregister_class(colmap_openmvs)
    bpy.utils.unregister_class(delight)
