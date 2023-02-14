from bpy.types import Context, UILayout

from CAD_Sketcher.declarations import Operators, Panels
from ..sketches_menu import VIEW3D_MT_sketches
from . import VIEW3D_PT_sketcher_base


def sketch_selector(
    context: Context,
    layout: UILayout,
    is_header: bool = False,
    show_selector: bool = True,
):
    row = layout.row(align=True)
    index = context.scene.sketcher.active_sketch_i
    name = "Sketches"

    scale_y = 1 if is_header else 1.8

    if index != -1:
        sketch = context.scene.sketcher.active_sketch
        name = sketch.name

        row.operator(
            Operators.SetActiveSketch,
            text="Leave: " + name,
            icon="BACK",
            depress=True,
        ).index = -1

        row.active = True
        row.scale_y = scale_y

    else:

        row.scale_y = scale_y
        # TODO: Don't show text when is_header
        row.operator(Operators.AddSketch, icon="ADD").wait_for_input = True

        if show_selector:
            row.menu(VIEW3D_MT_sketches.bl_idname, text=name)

    row.operator(Operators.Update, icon="FILE_REFRESH", text="")


class VIEW3D_PT_sketcher(VIEW3D_PT_sketcher_base):
    """Menu for selecting the sketch you want to enter into"""

    bl_label = "Sketcher"
    bl_idname = Panels.Sketcher

    def draw(self, context: Context):
        layout = self.layout

        sketch_selector(context, layout, show_selector=False)
        sketch = context.scene.sketcher.active_sketch
        layout.use_property_split = True
        layout.use_property_decorate = False

        if sketch:
            # Sketch is selected, show info about the sketch itself
            row = layout.row()
            row.alignment = "CENTER"
            row.scale_y = 1.2

            if sketch.solver_state != "OKAY":
                state = sketch.get_solver_state()
                row.operator(
                    Operators.ShowSolverState,
                    text=state.name,
                    icon=state.icon,
                    emboss=False,
                ).index = sketch.slvs_index
            else:
                dof = sketch.dof
                dof_ok = dof <= 0
                dof_msg = (
                    "Fully defined sketch"
                    if dof_ok
                    else "Degrees of freedom: " + str(dof)
                )
                dof_icon = "CHECKMARK" if dof_ok else "ERROR"
                row.label(text=dof_msg, icon=dof_icon)

            layout.separator()

            row = layout.row()
            row.prop(sketch, "name")
            layout.prop(sketch, "convert_type")

            if sketch.convert_type == "MESH":
                layout.prop(sketch, "curve_resolution")
            if sketch.convert_type != "NONE":
                layout.prop(sketch, "fill_shape")

            layout.operator(
                Operators.DeleteEntity,
                text="Delete Sketch",
                icon="X",
            ).index = sketch.slvs_index

        else:
            # No active Sketch , show list of available sketches
            layout.template_list(
                "VIEW3D_UL_sketches",
                "",
                context.scene.sketcher.entities,
                "sketches",
                context.scene.sketcher,
                "ui_active_sketch",
            )
