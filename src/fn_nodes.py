# coding: utf8
import imghdr
import os
import bpy

# Manual node tree implementation

def node_tree_mix_normals():
    #Get the group if it already exists
    if bpy.data.node_groups.get("mix_normals"):
        _node_tree = bpy.data.node_groups.get("mix_normals")
        return _node_tree
    #Create the group and its input/output sockets
    _node_tree = bpy.data.node_groups.new(type="ShaderNodeTree", name="mix_normals")
    _node_tree.inputs.new('NodeSocketColor','Geometry')
    _node_tree.inputs.new('NodeSocketColor','Surface')
    _node_tree.outputs.new('NodeSocketVector','Normal')
    #Aliases for the functions
    AN = _node_tree.nodes.new
    LN = _node_tree.links.new
    #Inputs and outputs
    _input     = AN(type="NodeGroupInput")
    _output    = AN(type="NodeGroupOutput")
    #Nodes
    _separate  = AN(type="ShaderNodeSeparateRGB")
    _combine   = AN(type="ShaderNodeCombineRGB")
    _overlay   = AN(type="ShaderNodeMixRGB")
    _normalMap = AN(type="ShaderNodeNormalMap")
    #Parameters
    _overlay.blend_type                  = "OVERLAY"
    _overlay.inputs["Fac"].default_value = 1.0
    _combine.inputs["B"].default_value   = 0.0
    #Links
    LN(_input.outputs["Geometry"],   _overlay.inputs["Color1"])
    LN(_input.outputs["Surface"],    _separate.inputs["Image"])
    LN(_separate.outputs["R"],       _combine.inputs["R"])
    LN(_separate.outputs["G"],       _combine.inputs["G"])
    LN(_combine.outputs["Image"],    _overlay.inputs["Color2"])
    LN(_overlay.outputs["Color"],    _normalMap.inputs["Color"])
    LN(_normalMap.outputs["Normal"], _output.inputs["Normal"])
    #Position
    _input.location     = [0,-100]
    _separate.location  = [200, -200]
    _combine.location   = [400, -200]
    _overlay.location   = [600, 0]
    _normalMap.location = [800,0]
    _output.location    = [1000,0]
    #Return
    return _node_tree

def node_tree_normal_to_color():
    #Get the group if it already exists
    if bpy.data.node_groups.get("normal_to_color"):
        _node_tree = bpy.data.node_groups.get("normal_to_color")
        return _node_tree
    #Create the group and its input/output sockets
    _node_tree = bpy.data.node_groups.new(type="ShaderNodeTree", name="normal_to_color")
    _node_tree.inputs.new('NodeSocketVector','Normal')
    _node_tree.outputs.new('NodeSocketColor','Color')
    #Aliases for the functions
    AN = _node_tree.nodes.new
    LN = _node_tree.links.new
    #Inputs and outputs
    _input     = AN(type="NodeGroupInput")
    _output    = AN(type="NodeGroupOutput")
    #Nodes
    _tangent   = AN(type="ShaderNodeTangent")
    _normal    = AN(type="ShaderNodeNewGeometry")
    _bitangent = AN(type="ShaderNodeVectorMath")
    _dot1      = AN(type="ShaderNodeVectorMath")
    _dot2      = AN(type="ShaderNodeVectorMath")
    _dot3      = AN(type="ShaderNodeVectorMath")
    _combine   = AN(type="ShaderNodeCombineXYZ")
    _curve     = AN(type="ShaderNodeVectorCurve")
    _gamma     = AN(type="ShaderNodeGamma")
    #Parameters
    _dot1.operation      = "DOT_PRODUCT"
    _dot2.operation      = "DOT_PRODUCT"
    _dot3.operation      = "DOT_PRODUCT"
    _bitangent.operation = "CROSS_PRODUCT"
    _gamma.inputs[1].default_value = 2.2
    for _c in _curve.mapping.curves:
        _c.points[0].location[1] = 0.0
    #Links
    LN(_input.outputs["Normal"],     _dot1.inputs[0])
    LN(_input.outputs["Normal"],     _dot2.inputs[0])
    LN(_input.outputs["Normal"],     _dot3.inputs[0])
    LN(_tangent.outputs["Tangent"],  _bitangent.inputs[1])
    LN(_normal.outputs["Normal"],    _bitangent.inputs[0])
    LN(_bitangent.outputs["Vector"], _dot2.inputs[1])
    LN(_tangent.outputs["Tangent"],  _dot1.inputs[1])
    LN(_normal.outputs["Normal"],    _dot3.inputs[1])
    LN(_dot1.outputs["Value"],       _combine.inputs[0])
    LN(_dot2.outputs["Value"],       _combine.inputs[1])
    LN(_dot3.outputs["Value"],       _combine.inputs[2])
    LN(_combine.outputs["Vector"],   _curve.inputs["Vector"])
    LN(_curve.outputs["Vector"],     _gamma.inputs["Color"])
    LN(_gamma.outputs["Color"],      _output.inputs["Color"])
    #Position
    _input.location = [0,400]
    _normal.location = [0,200]
    _input.location = [0,0]
    _tangent.location = [0,-200]
    _bitangent.location = [200,0]
    _dot1.location = [400,200]
    _dot2.location = [400,0]
    _dot3.location = [400,-200]
    _combine.location = [600,0]
    _curve.location = [800,0]
    _gamma.location = [1100,0]
    _output.location = [1300,0]
    #Return
    return _node_tree

def parameter_to_node(tree, parameter):
    """Converts an input str, int, float, list or tuple to a color or Image node"""
    _node = None
    #If it is a scalar value or a list or tuple
    if type(parameter) is float or type(parameter) is int or type(parameter) is list or type(parameter) is tuple:
        _col = [1,1,1,1]
        #If it is a tuple of ints or floats of len 3
        if type(parameter) is list or type(parameter) is tuple:
            if len(parameter)==3:
                if type(parameter[0]) is int or type(parameter[0]) is float:
                    _col = list(parameter) + [1]
        #If it is a float or an int
        else:
            _col = [parameter, parameter, parameter, 1]
        _node = tree.nodes.new(type="ShaderNodeRGB")
        _node.outputs["Color"].default_value = _col
    #If it is a blender image
    elif type(parameter) is bpy.types.Image:
        _node = tree.nodes.new(type="ShaderNodeTexImage")
        _node.image = parameter
    #If it is a path
    elif type(parameter) is str and os.path.exists(parameter):
        _node = tree.nodes.new(type="ShaderNodeTexImage")
        _node.image = bpy.data.images.load(parameter)
    #Else
    else:
        pass
    print(parameter, _node)
    return _node

def node_tree_pbr(settings, name):
    #Get the group if it already exists
    if bpy.data.node_groups.get(name):
        _node_tree = bpy.data.node_groups.get(name)
        return _node_tree
    #Create the group and its input/output sockets
    _node_tree = bpy.data.node_groups.new(type="ShaderNodeTree", name=name)
    _node_tree.inputs.new('NodeSocketFloat','UV scale')
    _node_tree.inputs.new('NodeSocketFloat','Height')
    _node_tree.outputs.new('NodeSocketShader','BSDF')
    #Aliases for the functions
    AN = _node_tree.nodes.new
    LN = _node_tree.links.new
    #Inputs and outputs
    _input     = AN(type="NodeGroupInput")
    _output    = AN(type="NodeGroupOutput")
    #Nodes
    _principled  = AN(type="ShaderNodeBsdfPrincipled")
    _albedo      = parameter_to_node(_node_tree, settings["albedo"])     if "albedo"     in settings else None
    _ao          = parameter_to_node(_node_tree, settings["ao"])         if "ao"         in settings else None
    _metallic    = parameter_to_node(_node_tree, settings["metallic"])   if "metallic"   in settings else None
    _roughness   = parameter_to_node(_node_tree, settings["roughness"])  if "roughness"  in settings else None
    _glossiness  = parameter_to_node(_node_tree, settings["glossiness"]) if "glossiness" in settings else None
    _normal      = parameter_to_node(_node_tree, settings["normal"])     if "normal"     in settings else None
    _height      = parameter_to_node(_node_tree, settings["height"])     if "height"     in settings else None
    _opacity     = parameter_to_node(_node_tree, settings["opacity"])    if "opacity"    in settings else None
    _emission    = parameter_to_node(_node_tree, settings["emission"])   if "emission"   in settings else None
    #If the dictionnary is empty, create images for each of them
    if not settings:
        _albedo     = AN(type="ShaderNodeTexImage")
        _ao         = AN(type="ShaderNodeTexImage")
        _metallic   = AN(type="ShaderNodeTexImage")
        _roughness  = AN(type="ShaderNodeTexImage")
        _glossiness = AN(type="ShaderNodeTexImage")
        _normal     = AN(type="ShaderNodeTexImage")
        _height     = AN(type="ShaderNodeTexImage")
        _opacity    = AN(type="ShaderNodeTexImage")
        _emission   = AN(type="ShaderNodeTexImage")
    _vertexcolors      = AN(type="ShaderNodeAttribute") if "vertexcolors" in settings else None
    _bump              = AN(type="ShaderNodeBump") if (_normal is not None or _height is not None) else None
    _nmap              = AN(type="ShaderNodeNormalMap") if (_normal is not None) else None
    _ao_mix            = AN(type="ShaderNodeMixRGB") if (_ao is not None) else None
    _opacity_mix       = AN(type="ShaderNodeMixShader") if (_opacity  is not None) else None
    _opacity_shader    = AN(type="ShaderNodeBsdfTransparent") if (_opacity  is not None) else None
    _emission_mix      = AN(type="ShaderNodeMixShader") if (_emission is not None) else None
    _emission_shader   = AN(type="ShaderNodeEmission") if (_emission  is not None) else None
    _glossiness_invert = AN(type="ShaderNodeInvert") if (_glossiness is not None) else None
    _reroute  = AN(type="NodeReroute")
    _uv       = AN(type="ShaderNodeUVMap")
    _mapping  = AN(type="ShaderNodeMapping")
    _separate = AN(type="ShaderNodeSeparateXYZ")
    _scalex   = AN(type="ShaderNodeMath")
    _scaley   = AN(type="ShaderNodeMath")
    _scalez   = AN(type="ShaderNodeMath")
    _combine  = AN(type="ShaderNodeCombineXYZ")
    #Parameters
    _scalex.operation = _scaley.operation = _scalez.operation = 'MULTIPLY'
    _scalex.inputs[1].default_value = _scaley.inputs[1].default_value = _scalez.inputs[1].default_value = 1
    if _ao_mix is not None:
        _ao_mix.blend_type = "MULTIPLY"
    if _vertexcolors is not None:
        _vertexcolors.attribute_name = "Col"
    #Links
    LN(_principled.outputs["BSDF"], _output.inputs["BSDF"])
    LN(_input.outputs["UV scale"], _reroute.inputs[0])
    LN(_uv.outputs["UV"], _mapping.inputs["Vector"])
    LN(_mapping.outputs["Vector"], _separate.inputs["Vector"])
    LN(_separate.outputs["X"], _scalex.inputs[0])
    LN(_separate.outputs["Y"], _scaley.inputs[0])
    LN(_separate.outputs["Z"], _scalez.inputs[0])
    LN(_reroute.outputs[0], _scalex.inputs[1])
    LN(_reroute.outputs[0], _scaley.inputs[1])
    LN(_reroute.outputs[0], _scalez.inputs[1])
    LN(_scalex.outputs["Value"], _combine.inputs["X"])
    LN(_scaley.outputs["Value"], _combine.inputs["Y"])
    LN(_scalez.outputs["Value"], _combine.inputs["Z"])
    for node in _node_tree.nodes:
        if node.type == "TEX_IMAGE":
            LN(_combine.outputs["Vector"], node.inputs["Vector"])
    if _albedo is not None:
        LN(_albedo.outputs["Color"], _principled.inputs["Base Color"])
    if _ao is not None:
        LN(_albedo.outputs["Color"], _ao_mix.inputs[1])
        LN(_ao.outputs["Color"], _ao_mix.inputs[2])
        LN(_ao_mix.outputs["Color"], _principled.inputs["Base Color"])
    if _vertexcolors is not None:
        LN(_vertexcolors.outputs["Color"], _principled.inputs["Base Color"])
    if _metallic is not None:
        LN(_metallic.outputs["Color"], _principled.inputs["Metallic"])
    if _roughness is not None:
        LN(_roughness.outputs["Color"], _principled.inputs["Roughness"])
    if _glossiness is not None:
        LN(_glossiness.outputs["Color"], _glossiness_invert.inputs["Color"])
        LN(_glossiness_invert.outputs["Color"], _principled.inputs["Roughness"])
    if _bump is not None:
        LN(_bump.outputs["Normal"], _principled.inputs["Normal"])
        if _height is not None:
            LN(_input.outputs["Height"], _bump.inputs["Distance"])
            LN(_height.outputs["Color"], _bump.inputs["Height"])
        if _nmap is not None:
            LN(_normal.outputs["Color"], _nmap.inputs["Color"])
            LN(_nmap.outputs["Normal"], _bump.inputs["Normal"])
    #Post shader emission and opacity mix
    if _emission is not None:
        LN(_emission.outputs["Color"], _emission_shader.inputs["Color"])
        LN(_emission.outputs["Color"], _emission_mix.inputs[0])
        LN(_emission_shader.outputs["Emission"], _emission_mix.inputs[2])
        LN(_principled.outputs["BSDF"], _emission_mix.inputs[1])
        LN(_emission_mix.outputs["Shader"], _output.inputs["BSDF"])
    if _opacity is not None:
        LN(_opacity.outputs["Color"], _opacity_shader.inputs["Color"])
        LN(_opacity.outputs["Color"], _opacity_mix.inputs[0])
        LN(_opacity_shader.outputs["BSDF"], _opacity_mix.inputs[1])
        LN(_opacity_mix.outputs["Shader"], _output.inputs["BSDF"])
        if _emission is not None:
            LN(_emission_mix.outputs["Shader"], _opacity_mix.inputs[2])
        else:
            LN(_principled.outputs["BSDF"], _opacity_mix.inputs[2])
    #Position everything
    _output.location     = [200,0]
    _principled.location = [0,0]
    #Input mapping and vector
    _uv.location       = [-2000, 0]
    _mapping.location  = [-1800, 0]
    _input.location    = [-1600, 300]
    _reroute.location  = [-1400, 200]
    _separate.location = [-1400, 0]
    _scalex.location   = [-1200, 100]
    _scaley.location   = [-1200, 0]
    _scalez.location   = [-1200,-100]
    _combine.location  = [-1000, 0]
    #Input nodes for the principled node
    if _albedo is not None:
        _albedo.location = [-200,0]
    if _ao is not None:
        _albedo.location = [-400,100]
        _ao.location = [-400,-100]
        _ao_mix.location = [-200, 0]
    if _vertexcolors is not None:
        _vertexcolors.location = [-400,0]
    if _metallic is not None:
        _metallic.location = [-200, -200]
    if _roughness is not None:
        _roughness.location = [-200, -400]
    if _glossiness is not None:
        _glossiness.location = [-400, -400]
        _glossiness_invert.location = [-200, -400]
    if _bump is not None:
        _bump.location = [-200, -600]
    if _nmap is not None:
        _nmap.location = [-400, -700]
    if _height is not None:
        _height.location = [-400, -500]
    if _normal is not None:
        _normal.location = [-600, -700]
        if _normal.type == "TEX_IMAGE":
            _normal.color_space = "NONE"
    #Post-shader emission and opacity mix
    if _emission is not None:
        _emission.location = [-200, 200]
        _emission_shader.location = [0, 200]
        _emission_mix.location = [200, 100]
    if _opacity is not None:
        off = [400,200] if _emission is not None else [0,0]
        _opacity.location = [-200 + off[0], 200 + off[1]]
        _opacity_shader.location = [0 + off[0], 200 + off[1]]
        _opacity_mix.location = [200 + off[0], 100 + off[1]]
    if (_emission is not None and _opacity is None) or (_emission is None and _opacity is not None):
        _output.location = [400,200]
    if _emission is not None and _opacity is not None:
        _output.location = [800,400]
    #Return
    return _node_tree


# Functions to transform a principled shader to emission

def get_neighbor_nodes(node):
    """Returns a list of the node's immediate neighbors"""
    _neighs = []
    for _input in node.inputs:
        if len(_input.links)>0:
            for _link in _input.links:
                _neighs.append(_link.from_node)
    for _output in node.outputs:
        if len(_output.links)>0:
            for _link in _output.links:
                _neighs.append(_link.to_node)
    return _neighs

def get_linked_nodes(node):
    """Returns a list of all the node's connected nodes"""
    _linkedNodes = [node]
    _neighs = [node]
    while len(_neighs):
        _newNeighs = []
        for _node in _neighs:
            for _neigh in get_neighbor_nodes(_node):
                if _neigh not in _linkedNodes:
                    _newNeighs.append(_neigh)
                    _linkedNodes.append(_neigh)
        _neighs = _newNeighs
    return _linkedNodes

def make_normals_non_color(node_tree):
    for n in node_tree.nodes:
        if n.type == "NORMAL_MAP":
            if n.inputs["Color"].links[0].from_node.type == "TEX_IMAGE":
                n.inputs["Color"].links[0].from_node.color_space="NONE"
        if n.type=="GROUP":
            make_normals_non_color(n.node_tree)

def principledNodeToEmission(node_tree, node, nodeInput):
    """Replaces the Principled by an Emission node, keeping only one input"""
    #Disconnect every principled input not of interest
    for _input in node.inputs:
        if _input != nodeInput:
            for _link in _input.links:
                node_tree.links.remove(_link)
    #Remove all links not connected to the principled shader
    _linked = get_linked_nodes(node) + [node]
    for _node in node_tree.nodes:
        if _node not in _linked:
            node_tree.nodes.remove(_node)
    #Create an Emission shader to replace the Principled
    _emission = node_tree.nodes.new(type="ShaderNodeEmission")
    _emission.location = node.location
    if len(nodeInput.links):
        _from_output = nodeInput.links[0].from_socket
        node_tree.links.new(_from_output, _emission.inputs["Color"])
    if len(node.outputs["BSDF"].links):
        _to_input    = node.outputs["BSDF"].links[0].to_socket
        node_tree.links.new(_emission.outputs["Emission"], _to_input)

def createBakingNodeGroup(material, bakeType):
    """Effectively add the converted group to the material"""
    #Do the conversion
    _newTree  = material.node_tree.copy()
    _trees = [_newTree]
    while len(_trees):
        _newTrees = []
        for _tree in _trees:
            for _node in _tree.nodes:
                if _node.type == "BSDF_PRINCIPLED":
                    fillPrincipledInputs(_tree, _node, bakeType)
                    principledNodeToEmission(_tree, _node, _node.inputs[bakeType])
                    _tree.nodes.remove(_node)
                    continue
                if _node.type == "TEX_IMAGE":
                    _node.color_space="COLOR"
                    if _node.image is None:
                        _tree.nodes.remove(_node)
                        continue
                if _node.type == "GROUP":
                    _newTrees.append(_node.node_tree)
        _trees = _newTrees

    make_normals_non_color(_newTree)

    """Insert the converted tree into the material"""
    #Create a node group and assign the tree to it
    _group = material.node_tree.nodes.new("ShaderNodeGroup")
    _group.node_tree   = _newTree
    #Add an output node for the group
    _group.outputs.new("NodeSocketShader", 'material')
    _newOut = _group.node_tree.nodes.new("NodeGroupOutput")
    #Replace the old output node with the new one (location and links)
    _oldOut    = [_n for _n in _group.node_tree.nodes if _n.type == 'OUTPUT_MATERIAL' and _n.is_active_output][0]
    _newOut.location = _oldOut.location
    _group.node_tree.links.new(_oldOut.inputs[0].links[0].from_node.outputs[0], _newOut.inputs[0])
    #Remove the old node
    _group.node_tree.nodes.remove(_oldOut)

    return _group

group = bpy.context.active_object.material_slots[0].material.node_tree.nodes.new("ShaderNodeGroup")
group.node_tree = node_tree_mix_normals()

group = bpy.context.active_object.material_slots[0].material.node_tree.nodes.new("ShaderNodeGroup")
group.node_tree = node_tree_normal_to_color()

group = bpy.context.active_object.material_slots[0].material.node_tree.nodes.new("ShaderNodeGroup")
#Add an empty PBR structure
group.node_tree = node_tree_pbr(settings={}, name="MyMaterial")