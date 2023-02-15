from bpy.types import WorkSpaceTool

from ..declarations import GizmoGroups, Operators, WorkSpaceTools
from ..keymaps import disable_gizmos, tool_access, tool_select
from ..stateful_operator.tool import GenericStateTool
from ..stateful_operator.utilities.keymap import operator_access


class VIEW3D_T_slvs_add_workplane_face(GenericStateTool, WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"
    bl_idname = WorkSpaceTools.AddWorkplaneFace
    bl_label = "Add Workplane on mesh face"
    bl_operator = Operators.AddWorkPlaneFace
    bl_icon = "ops.mesh.primitive_grid_add_gizmo"
    bl_widget = GizmoGroups.Preselection
    bl_keymap = (
        *disable_gizmos,
        *tool_select,
        *tool_access,
        *operator_access(Operators.AddWorkPlaneFace),
    )
