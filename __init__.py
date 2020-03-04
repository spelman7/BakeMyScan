bl_info = {
    'name':     'BakeMyScan',
    'category': 'Object',
    'version': (1, 1, 0),
    'blender': (2, 80, 0),
    "description": "Multipurpose add-on to texture, remesh and bake objects",
    "author": "Loïc NORGEOT",
    "warning": "Materials and baking operators are only available in Cycles",
    "tracker_url": "https://github.com/norgeotloic/BakeMyScan/issues",
    "wiki_url": "http://bakemyscan.org"
}

import sys
import os
import importlib

#icons
import bpy.utils.previews

#All python files in the src/ directory
modulesFiles = [f for f in os.listdir(os.path.join(os.path.dirname(__file__),"src")) if f.endswith(".py")]
modulesNames = ["src." + f.replace(".py", "") for f in modulesFiles]
#print(modulesNames)

modulesFullNames = {}
for currentModuleName in modulesNames:
    modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        #print(currentModuleFullName)
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)

def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()
    #icons
    bpy.types.Scene.custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    bpy.types.Scene.custom_icons.load("meshlab", os.path.join(icons_dir, "meshlab.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("instant", os.path.join(icons_dir, "instant.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("mmg", os.path.join(icons_dir, "mmg.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("bakemyscan", os.path.join(icons_dir, "bakemyscan.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("github", os.path.join(icons_dir, "github.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("travis", os.path.join(icons_dir, "travis.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("sketchfab", os.path.join(icons_dir, "sketchfab.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("tweeter", os.path.join(icons_dir, "tweeter.png"), 'IMAGE')
    bpy.types.Scene.custom_icons.load("youtube", os.path.join(icons_dir, "youtube.png"), 'IMAGE')

def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()
    #icons
    bpy.utils.previews.remove(bpy.types.Scene.custom_icons)
    try:
        del bpy.types.Scene.custom_icons
    except:
        pass

if __name__ == "__main__":
    register()
