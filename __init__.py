bl_info = {
    "name": "SEGA Ninja format",
    "author": "noxrim",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "File > Import-Export",
    "description": "SEGA Ninja format import/export",
    "warning": "",
    "category": "Import-Export",
}

import bpy

from bpy.props import (
    StringProperty,
    FloatProperty,
)

from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
)

if "bpy" in locals():
    import importlib
    if "ninja_import" in locals():
        importlib.reload(ninja_import)
    if "ninja_export" in locals():
        importlib.reload(ninja_export)

@orientation_helper(axis_forward='Z', axis_up='Y')
class ImportNinja(bpy.types.Operator, ImportHelper):
    """Import binary Ninja data"""
    bl_idname = "import_scene.ninja"
    bl_label = "Import Ninja"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".nj"
    filter_glob: StringProperty(default="*", options={'HIDDEN'})

    def execute(self, context):        
        from . import ninja_import
        return ninja_import.load(self, context)

    def invoke(self, context, event):
        return self.invoke_popup(context)


def menu_func_import(self, context):
    self.layout.operator(ImportNinja.bl_idname, text="SEGA Ninja (.nj)")

# def menu_func_export(self, context):
#    self.layout.operator(ExportNinja.bl_idname, text="SEGA Ninja (.nj)")


classes = (
    ImportNinja,
    # ExportNinja,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    # bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()