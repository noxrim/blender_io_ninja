bl_info = {
    "name": "Ninja format",
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
    EnumProperty,
    IntProperty,
    CollectionProperty,
)
from bpy_extras.io_utils import (
    ImportHelper,
    ExportHelper,
    orientation_helper,
    path_reference_mode,
    axis_conversion,
)
import os


if "bpy" in locals():
    import importlib
    if "ninja_import" in locals():
        importlib.reload(ninja_import)
    if "ninja_export" in locals():
        importlib.reload(ninja_export)


# @orientation_helper(axis_forward='-Z', axis_up='Y')
class ImportNinja(bpy.types.Operator, ImportHelper):
    """Import binary Ninja data"""
    bl_idname = "import_scene.ninja"
    bl_label = "Import Ninja"
    bl_options = {'UNDO', 'PRESET'}

    filename_ext = ".nj"
    filter_glob: StringProperty(default="*", options={'HIDDEN'})

    _autodetected = False
    _last_filepath = ""

    format: EnumProperty(
        name="Format",
        description="Type of Ninja file to import",
        items=(('IFF_CONTAINER', "Ninja IFF Container", "Import a standard Ninja IFF container, containing multiple data buffers.\nCommonly found with file extensions .nj, .njm, .njc, .njs"),
               #('CHUNK_MODEL', "Ninja Chunk Model", "Import a single Chunk Model buffer, embedded or linked into a binary object"),
               #('BASIC_MODEL', "Ninja Basic Model", "Import a single Basic Model buffer, embedded or linked into a binary object"),
               ),
        default='IFF_CONTAINER',
    )

    file_offset: IntProperty(
        name="File Offset",
        description="File position of the base of the buffer",
        min=0,
        default=0,
        options={'HIDDEN'},
    )

    pointer_offset: IntProperty(
        name="Pointer Offset",
        description="Virtual memory address of the base of the buffer, for calculating pointer offsets",
        min=0,
        default=0,
        options={'HIDDEN'},
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "format")

    def check(self, context):
        if self.filepath != self._last_filepath:
            # filepath changed
            if os.path.isfile(self.filepath):
                pass # autodetect format

            _last_filepath = self.filepath

        return False

    def execute(self, context):        
        print("x")
        from . import ninja_import
        return ninja_import.load(self, context)

    def invoke(self, context, event):
        return self.invoke_popup(context)


def menu_func_import(self, context):
    self.layout.operator(ImportNinja.bl_idname, text="Ninja Binary (.nj)")

# def menu_func_export(self, context):
#    self.layout.operator(ExportNinja.bl_idname, text="Ninja Binary (.nj)")


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