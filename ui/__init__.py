import bpy
from bpy.types import Context

from CAD_Sketcher.declarations import Operators
from .panels.add_constraint import VIEW3D_PT_sketcher_add_constraints
from .panels.constraints_list import VIEW3D_PT_sketcher_constraints
from .panels.debug import VIEW3D_PT_sketcher_debug
from .panels.entities_list import VIEW3D_PT_sketcher_entities
from .panels.sketch_select import VIEW3D_PT_sketcher
from .sketches_list import VIEW3D_UL_sketches
from .sketches_menu import VIEW3D_MT_sketches


def draw_object_context_menu(self, context: Context):
    layout = self.layout
    ob = context.active_object
    row = layout.row()

    props = row.operator(Operators.SetActiveSketch, text="Edit Sketch")

    if ob and ob.sketch_index != -1:
        row.enabled = True
        props.index = ob.sketch_index
    else:
        row.enabled = False
    layout.separator()


def draw_add_sketch_in_add_menu(self, context: Context):
    self.layout.separator()
    self.layout.operator_context = "INVOKE_DEFAULT"
    self.layout.operator("view3d.slvs_add_sketch", text="Sketch")


classes = [
    VIEW3D_UL_sketches,
    VIEW3D_MT_sketches,
    VIEW3D_PT_sketcher,
    VIEW3D_PT_sketcher_add_constraints,
    VIEW3D_PT_sketcher_entities,
    VIEW3D_PT_sketcher_constraints,
    VIEW3D_PT_sketcher_debug,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.prepend(draw_object_context_menu)
    bpy.types.VIEW3D_MT_add.append(draw_add_sketch_in_add_menu)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.remove(draw_object_context_menu)
    bpy.types.VIEW3D_MT_add.remove(draw_add_sketch_in_add_menu)
