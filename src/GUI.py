import bpy
import os
from   bpy_extras.io_utils import ImportHelper

import addon_utils
from . import fn_nodes

class BakeMyScanPanel(bpy.types.Panel):
    """A base class for panels to inherit"""
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "BakeMyScan"
    bl_options     = {"DEFAULT_CLOSED"}
    bl_context     = "objectmode"

class BakeMyScanProperties(bpy.types.PropertyGroup):

    #Callbacks
    def toggle_delight(self, context):
        if self.delight:
            bpy.ops.bakemyscan.delight()
        else:
            nodes = context.active_object.active_material.node_tree.nodes.get("PBR").node_tree.nodes
            nodes.remove(nodes.get("delight"))
        return None
    def update_delight_invert(self, context):
        nodes = context.active_object.active_material.node_tree.nodes.get("PBR").node_tree.nodes
        nodes["delight"].inputs["Invert"].default_value = self.delight_invert_factor
        return None
    def update_delight_ao(self, context):
        nodes = context.active_object.active_material.node_tree.nodes.get("PBR").node_tree.nodes
        nodes["delight"].inputs["AO"].default_value = self.delight_ao_factor
        return None
    def update_ao(self, context):
        nodes = context.active_object.active_material.node_tree.nodes.get("PBR").node_tree.nodes
        nodes["ao_mix"].inputs["Fac"].default_value = self.ao_factor
        return None
    def update_UV_scale(self, context):
        nodes = context.active_object.active_material.node_tree.nodes
        group = [g for g in nodes if g.type=="GROUP"][0]
        group.inputs["UV scale"].default_value = self.uv_scale
        return None
    def update_height(self, context):
        nodes = context.active_object.active_material.node_tree.nodes
        group = [g for g in nodes if g.type=="GROUP"][0]
        group.inputs["Height"].default_value = self.height
        return None
    def setworldintensity(self, context):
        bpy.data.worlds['World'].node_tree.nodes["Background"].inputs[1].default_value = self.intensity
        return None
    def toggle_hdri(self, context):
        context.scene.world.cycles_visibility.camera = self.visibility
        bpy.data.worlds['World'].node_tree.nodes["Background"].inputs[1].default_value = self.intensity
        return None
    def rotate_hdri(self, context):
        bpy.data.worlds['World'].node_tree.nodes["BMS_world"].rotation[2] = 3.14159 * self.rotation
        bpy.data.worlds['World'].node_tree.nodes["Background"].inputs[1].default_value = self.intensity
        return None
    def create_PBR_library(self, context):
        print(self.texturepath)
        bpy.ops.bakemyscan.create_library(filepath=self.texturepath)
        return None
    def update_scan_images(self, context):
        bpy.types.Scene.imagesdirectory = self.imagesdirectory
        return None

    #Delighting properties
    delight: bpy.props.BoolProperty(description="Delighting", default=False, update=toggle_delight)
    delight_invert_factor: bpy.props.FloatProperty(description="Inversion factor for delighting", default=0.3, min=0.,max=1., update=update_delight_invert)
    delight_ao_factor: bpy.props.FloatProperty(description="Ambient Occlusion factor for delighting", default=0.15, min=0.,max=1., update=update_delight_ao)
    #General material properties
    ao_factor: bpy.props.FloatProperty(description="Ambient Occlusion factor", default=0.5, min=0.,max=1., update=update_ao)
    uv_scale: bpy.props.FloatProperty(description="UV scale", default=1, min=0.,max=1000., update=update_UV_scale)
    height: bpy.props.FloatProperty(description="Height", default=0.005, min=-1.,max=1., update=update_height)
    #HDRI properties
    intensity: bpy.props.FloatProperty(description="HDRI intensity", default=1, min=0., max=10000., update=setworldintensity)
    visibility: bpy.props.BoolProperty(description="HDRI visibility", default=False, update=toggle_hdri)
    rotation: bpy.props.FloatProperty(description="HDRI rotation", default=0., min=-1., max=1., update=rotate_hdri)
    #Scanning images
    imagesdirectory: bpy.props.StringProperty(description="Filepath used for importing the file",subtype='DIR_PATH', update=update_scan_images)
    #PBR library
    texturepath: bpy.props.StringProperty(description="Filepath used for importing the file",subtype='DIR_PATH',update=create_PBR_library)

class SCAN_PT_Panel(BakeMyScanPanel):
    """A panel for the scanning methods"""
    bl_label       = "Structure from Motion"
    def draw(self, context):
        box = self.layout
        box.label(text="Images directory")
        box.prop(context.scene.bakemyscan_properties, "imagesdirectory", text="")
        box.label(text="Structure from motion")
        #box.operator("bakemyscan.colmap_auto", icon="CAMERA_DATA", text="Colmap auto")
        box.operator("bakemyscan.colmap_openmvs", icon="CAMERA_DATA", text="Colmap OpenMVS Meshlab")

class PIPELINE_PT_Panel(BakeMyScanPanel):
    bl_label = "Model optimization"
    def draw(self, context):
        self.layout.operator("bakemyscan.clean_object", icon="PARTICLEMODE", text="Pre-process")

        self.layout.label(text="Retopology")
        self.layout.operator("bakemyscan.full_pipeline", icon="MOD_DECIM", text="Remesh")
        self.layout.operator("bakemyscan.unwrap",            icon="GROUP_UVS",  text="Unwrap")

        self.layout.label(text="Post-process")

        self.layout.operator("bakemyscan.symetrize",         icon="MOD_MIRROR", text='Symmetry')
        self.layout.operator("bakemyscan.relax",             icon="MOD_SMOKE",  text='Relax!')
        self.layout.operator("bakemyscan.manifold",          icon="MOD_FLUIDSIM",  text='Manifold')
        self.layout.operator("bakemyscan.remove_all_but_selected", icon="X", text="Clean non selected data")

        self.layout.label(text="Texture baking")
        self.layout.operator("bakemyscan.bake_textures",         icon="TEXTURE", text="Bake textures")
        self.layout.operator("bakemyscan.bake_textures_nodes",         icon="TEXTURE", text="Bake textures w Nodes")
        self.layout.operator("bakemyscan.bake_to_vertex_colors", icon="COLOR",   text="Albedo to Vertex color")

class MATERIAL_PT_Panel(BakeMyScanPanel):
    bl_label       = "Material / Textures"

    @classmethod
    def poll(self, context):
        #Render engine must be cycles
        if bpy.context.scene.render.engine!="CYCLES":
            return 0
        return 1

    def check(self, context):
        return True

    def draw(self, context):

        def create_image_UI(layout, name, node):
            row = layout.row()
            lab = row.row()
            lab.scale_x = 1.0
            lab.label(text=name)
            sub=row.row()
            sub.scale_x=4.0
            sub.template_ID(data=node,property="image",open="image.open")

        #Do we display the textures and delighting options?
        display = False
        nodes   = None
        ob = context.active_object
        if ob is not None and len(context.selected_objects)>0:
            if len(ob.material_slots)>0:
                mat = ob.active_material
                if mat is not None:
                    if mat.use_nodes:
                        groups = [g for g in mat.node_tree.nodes if g.type=="GROUP"]
                        if len(groups)==1:
                            if mat.node_tree.nodes.get("PBR") is not None:
                                nodes = mat.node_tree.nodes.get("PBR").node_tree.nodes
                                display = True

        #Display a warning
        if ob is None:
            self.layout.label(text="No active object")

        #Display the material selector widget
        if ob is not None and len(context.selected_objects)>0:
            self.layout.template_ID(
                data=ob,
                property="active_material",
                new="bakemyscan.create_empty_material",
                open="bakemyscan.material_from_library"
            )

        if display:
            #Display the texture slots
            box = self.layout.box()
            create_image_UI(box, "Albedo", nodes["albedo"])
            create_image_UI(box, "AO", nodes["ao"])
            if nodes["ao"].image is not None:
                row = box.row()
                lab = row.row()
                lab.scale_x = 1.0
                lab.label(text="")
                sub=row.row()
                sub.scale_x=4.0
                sub.prop(context.scene.bakemyscan_properties, "ao_factor", text="Factor")
            create_image_UI(box, "Normal", nodes["normal"])
            create_image_UI(box, "Height", nodes["height"])
            create_image_UI(box, "Metallic", nodes["metallic"])
            create_image_UI(box, "Roughness", nodes["roughness"])

            #Delighting box
            if nodes.get("albedo") is not None:
                if nodes["albedo"].image is not None:
                    box = self.layout.box()
                    box.prop(context.scene.bakemyscan_properties, "delight", text="Delight")
                    if nodes.get("delight"):
                        box.prop(context.scene.bakemyscan_properties, "delight_invert_factor", text="Invert factor")
                        box.prop(context.scene.bakemyscan_properties, "delight_ao_factor", text="AO factor")

            #Correct the links in the material
            try:
                if bpy.context.space_data.viewport_shade != 'RENDERED':
                    fn_nodes.link_material(ob.active_material.node_tree.nodes.get("PBR").node_tree)
            except:
                fn_nodes.link_material(ob.active_material.node_tree.nodes.get("PBR").node_tree)

        else:
            #If there is a material which comes from the library
            if ob is not None:
                if len(ob.material_slots)>0:
                    mat = ob.active_material
                    if mat is not None:
                        if mat.use_nodes:
                            groups = [g for g in mat.node_tree.nodes if g.type=="GROUP"]
                            if len(groups)==1:
                                g = groups[0]
                                if "Height" in g.inputs and "UV scale" in g.inputs:
                                    self.layout.prop(context.scene.bakemyscan_properties, "uv_scale", text="UV scale")
                                    self.layout.prop(context.scene.bakemyscan_properties, "height",   text="Height")

class REMESHFROMSCULPT_PT_Panel(bpy.types.Panel):
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "Tools"
    bl_label       = "BakeMyScan"
    bl_context     = "sculpt_mode"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context):
        self.layout.operator("bakemyscan.full_pipeline", icon="MOD_DECIM", text="Retopology")

class HDRIS_PT_Panel(BakeMyScanPanel):
    """Creates a Panel in the Object properties window"""
    bl_label       = "HDRIs"

    @classmethod
    def poll(self, context):
        #Render engine must be cycles
        if bpy.context.scene.render.engine!="CYCLES":
            return 0
        #There must be a world called "World"
        if bpy.data.worlds.get("World") is None:
            return 0
        return 1

    def draw(self, context):
        layout = self.layout
        #HDRI
        wm = context.window_manager
        row = layout.row()
        row.prop(wm, "my_previews_dir")
        if wm.my_previews_dir != "":
            row = layout.row()
            row.template_icon_view(wm, "my_previews")
            layout.prop(context.scene.bakemyscan_properties, "visibility", text="Show background")
            layout.prop(context.scene.bakemyscan_properties, "intensity", text="Intensity")
            layout.prop(context.scene.bakemyscan_properties, "rotation", text="Rotation")

class ABOUT_PT_Panel(BakeMyScanPanel):
    bl_label       = "Updates / Help"

    def draw(self, context):

        self.layout.operator("wm.url_open", text="bakemyscan.org", icon_value=bpy.types.Scene.custom_icons["bakemyscan"].icon_id).url = "http://bakemyscan.org"

        #Update
        _text     = "Check for updates"
        _operator = "bakemyscan.check_updates"
        if bpy.types.Scene.currentVersion is not None and bpy.types.Scene.newVersion is not None:
            if bpy.types.Scene.currentVersion == bpy.types.Scene.newVersion and not bpy.types.Scene.restartRequired:
                _text     = "Nothing new. Check again?"
                _operator = "bakemyscan.check_updates"
            elif bpy.types.Scene.restartRequired:
                _text     = "Restart blender to update"
                _operator = "wm.quit_blender"
            else:
                _text     = "Update to %s" % bpy.types.Scene.newVersion
                _operator = "bakemyscan.update"
        else:
            pass
        row = self.layout.row(align=True)
        row.operator(_operator, text=_text, icon="FILE_REFRESH")
        for mod in addon_utils.modules():
            if mod.bl_info.get("name") == "BakeMyScan":
                try:
                    if bpy.types.Scene.currentVersion != bpy.types.Scene.newVersion:
                        row.operator("wm.url_open", text="Changelog", icon="INFO").url = "https://github.com/norgeotloic/BakeMyScan/releases/latest"
                    else:
                        name = ".".join([str(x) for x in mod.bl_info.get("version")])
                        icon = bpy.types.Scene.custom_icons["bakemyscan"].icon_id
                        row.operator("wm.url_open", icon="INFO", text='Current: %s' % name, icon_value=icon).url = "https://github.com/norgeotloic/BakeMyScan/releases/tag/"+name
                except:
                    name = ".".join([str(x) for x in mod.bl_info.get("version")])
                    icon = bpy.types.Scene.custom_icons["bakemyscan"].icon_id
                    row.operator("wm.url_open", icon="INFO", text='Current: %s' % name, icon_value=icon).url = "https://github.com/norgeotloic/BakeMyScan/releases/tag/"+name

        self.layout.label(text="Resources")
        self.layout.operator("wm.url_open", text="Tutorials", icon="QUESTION").url = "http://bakemyscan.org/tutorials"
        self.layout.operator("wm.url_open", text="BlenderArtists", icon="BLENDER").url = "https://blenderartists.org/t/bakemyscan-open-source-toolbox-for-asset-optimization"
        self.layout.operator("wm.url_open", text="Sketchfab", icon_value=bpy.types.Scene.custom_icons["sketchfab"].icon_id).url = "https://sketchfab.com/norgeotloic"
        self.layout.operator("wm.url_open", text="Twitter",   icon_value=bpy.types.Scene.custom_icons["tweeter"].icon_id).url = "https://twitter.com/norgeotloic"
        self.layout.operator("wm.url_open", text="Youtube",   icon_value=bpy.types.Scene.custom_icons["youtube"].icon_id).url = "https://youtube.com/norgeotloic"

        self.layout.label(text="Development")
        self.layout.operator("wm.url_open", text="Github",         icon_value=bpy.types.Scene.custom_icons["github"].icon_id).url = "http://github.com/norgeotloic/BakeMyScan"
        self.layout.operator("wm.url_open", text="Build status",   icon_value=bpy.types.Scene.custom_icons["travis"].icon_id).url = "https://travis-ci.org/norgeotloic/BakeMyScan"
        self.layout.operator("wm.url_open", text="Roadmap",   icon="SORTTIME").url = "http://github.com/norgeotloic/BakeMyScan/milestones"
        self.layout.operator("wm.url_open", text='"Blog"',    icon="WORDWRAP_ON").url = "http://bakemyscan.org/blog"

        self.layout.label(text="External software")
        self.layout.operator("wm.url_open", text="MMGtools", icon_value=bpy.types.Scene.custom_icons["mmg"].icon_id).url = "https://www.mmgtools.org/"
        self.layout.operator("wm.url_open", text="Instant Meshes", icon_value=bpy.types.Scene.custom_icons["instant"].icon_id).url = "https://github.com/wjakob/instant-meshes"
        self.layout.operator("wm.url_open", text="Quadriflow", icon="MOD_DECIM").url = "https://github.com/hjwdzh/QuadriFlow"
        self.layout.operator("wm.url_open", text="Meshlab", icon_value=bpy.types.Scene.custom_icons["meshlab"].icon_id).url = "http://www.meshlab.net/"
        self.layout.operator("wm.url_open", text="Colmap", icon="CAMERA_DATA").url = "https://colmap.github.io/"
        self.layout.operator("wm.url_open", text="OpenMVS", icon="CAMERA_DATA").url = "http://cdcseacave.github.io/openMVS/"

#Main menu fonctions
def import_mesh_func(self, context):
    self.layout.operator("bakemyscan.import_mesh", text="MESH (.mesh)")
def export_mesh_func(self, context):
    self.layout.operator("bakemyscan.export_mesh", text="MESH (.mesh)")
def import_bms_func(self, context):
    self.layout.operator("bakemyscan.import_scan", text="BMS (.obj, .fbx, .ply)")
def export_bms_func(self, context):
    self.layout.operator("bakemyscan.export", text="BMS: model (.obj, .fbx) and textures (.jpg, .png)")
def export_ortho_func(self, context):
    self.layout.operator("bakemyscan.export_orthoview", text="Orthographic view", icon="CAMERA_DATA")

#Node editor menu
def add_empty_pbr(self, context):
    self.layout.operator("bakemyscan.create_empty_node", text="Empty PBR node", icon="ZOOMIN")
def add_pbr_from_library(self, context):
    self.layout.operator("bakemyscan.node_from_library", text="PBR node from library", icon="MATERIAL")

def register():
    #Variables
    bpy.utils.register_class(BakeMyScanProperties)
    bpy.types.Scene.bakemyscan_properties = bpy.props.PointerProperty(type=BakeMyScanProperties)
    bpy.types.Scene.imagesdirectory = ""
    #Panels
    bpy.utils.register_class(SCAN_PT_Panel)
    bpy.utils.register_class(MATERIAL_PT_Panel)
    bpy.utils.register_class(REMESHFROMSCULPT_PT_Panel)
    bpy.utils.register_class(PIPELINE_PT_Panel)
    bpy.utils.register_class(HDRIS_PT_Panel)
    bpy.utils.register_class(ABOUT_PT_Panel)
    #Menu options
    bpy.types.TOPBAR_MT_file_import.append(import_mesh_func)
    bpy.types.TOPBAR_MT_file_export.append(export_mesh_func)
    bpy.types.TOPBAR_MT_file_import.append(import_bms_func)
    bpy.types.TOPBAR_MT_file_export.append(export_bms_func)
    bpy.types.TOPBAR_MT_render.append(export_ortho_func)
    #Node options
    bpy.types.NODE_MT_add.append(add_empty_pbr)
    bpy.types.NODE_MT_add.append(add_pbr_from_library)

def unregister():
    #Variables
    bpy.utils.unregister_class(BakeMyScanProperties)
    del bpy.types.Scene.bakemyscan_properties
    del bpy.types.Scene.imagesdirectory
    #Panels
    bpy.utils.unregister_class(SCAN_PT_Panel)
    bpy.utils.unregister_class(MATERIAL_PT_Panel)
    bpy.utils.unregister_class(REMESHFROMSCULPT_PT_Panel)
    bpy.utils.unregister_class(PIPELINE_PT_Panel)
    bpy.utils.unregister_class(HDRIS_PT_Panel)
    bpy.utils.unregister_class(ABOUT_PT_Panel)
    #Menu options
    bpy.types.TOPBAR_MT_file_import.remove(import_mesh_func)
    bpy.types.TOPBAR_MT_file_export.remove(export_mesh_func)
    bpy.types.TOPBAR_MT_file_import.remove(import_bms_func)
    bpy.types.TOPBAR_MT_file_export.remove(export_bms_func)
    bpy.types.TOPBAR_MT_render.remove(export_ortho_func)
    #Node options
    bpy.types.NODE_MT_add.remove(add_empty_pbr)
    bpy.types.NODE_MT_add.remove(add_pbr_from_library)
