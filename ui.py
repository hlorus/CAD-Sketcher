import bpy
from bpy.types import Panel, Menu, UIList, Context, UILayout, PropertyGroup

from .utilities.preferences import get_prefs
from .declarations import Menus, Operators, Panels, ConstraintOperators
from .stateful_operator.constants import Operators as StatefulOperators
from .model.types import GenericConstraint, DimensionalConstraint


class VIEW3D_UL_sketches(UIList):
    """Creates UI list of available Sketches"""

    def draw_item(
        self,
        context: Context,
        layout: UILayout,
        data: PropertyGroup,
        item: PropertyGroup,
        icon: int,
        active_data: PropertyGroup,
        active_propname: str,
        index: int = 0,
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if item:
                active = index == getattr(active_data, active_propname)

                row = layout.row(align=True)
                row.alignment = "LEFT"
                row.prop(
                    item,
                    "visible",
                    icon_only=True,
                    icon=("HIDE_OFF" if item.visible else "HIDE_ON"),
                    emboss=False,
                )
                row.prop(item, "name", text="", emboss=False, icon_value=icon)

                row = layout.row()
                row.alignment = "RIGHT"

                if item.solver_state != "OKAY":
                    row.operator(
                        Operators.ShowSolverState,
                        text="",
                        emboss=False,
                        icon_value=layout.enum_item_icon(
                            item, "solver_state", item.solver_state
                        ),
                    ).index = item.slvs_index

                row.operator(
                    Operators.SetActiveSketch,
                    icon="OUTLINER_DATA_GP_LAYER",
                    text="",
                    emboss=False,
                ).index = item.slvs_index

                if active:
                    row.operator(
                        Operators.DeleteEntity,
                        text="",
                        icon="X",
                        emboss=False,
                    ).index = item.slvs_index
                else:
                    row.separator()
                    row.separator()

            else:
                layout.label(text="", translate=False, icon_value=icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


class VIEW3D_PT_sketcher_base(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sketcher"


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


class VIEW3D_PT_sketcher_debug(VIEW3D_PT_sketcher_base):
    """Debug Menu"""

    bl_label = "Debug Settings"
    bl_idname = Panels.SketcherDebugPanel

    def draw(self, context: Context):
        layout = self.layout

        prefs = get_prefs()
        layout.operator(Operators.WriteSelectionTexture)
        layout.operator(Operators.Solve)
        layout.operator(Operators.Solve, text="Solve All").all = True

        layout.operator(StatefulOperators.Test)
        layout.prop(context.scene.sketcher, "show_origin")
        layout.prop(prefs, "hide_inactive_constraints")
        layout.prop(prefs, "all_entities_selectable")
        layout.prop(prefs, "force_redraw")
        layout.prop(context.scene.sketcher, "selectable_constraints")
        layout.prop(prefs, "use_align_view")

    @classmethod
    def poll(cls, context: Context):
        prefs = get_prefs()
        return prefs.show_debug_settings


class VIEW3D_PT_sketcher_add_constraints(VIEW3D_PT_sketcher_base):
    """
    Add Constraint Menu: List of buttons with the constraint you want
    to create.
    """

    bl_label = "Add Constraints"
    bl_idname = Panels.SketcherAddContraint
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        layout = self.layout
        layout.label(text="Constraints:")
        col = layout.column(align=True)
        for op in ConstraintOperators:
            col.operator(op)


class VIEW3D_PT_sketcher_entities(VIEW3D_PT_sketcher_base):
    """
    Entities Menu: List of entities in the sketch.
    Interactive
    """

    bl_label = "Entities"
    bl_idname = Panels.SketcherEntities
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        layout = self.layout
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8

        sketch = context.scene.sketcher.active_sketch
        for e in context.scene.sketcher.entities.all:
            if not e.is_active(sketch):
                continue
            if e.is_sketch():
                continue

            row = col.row()
            row.alert = e.selected

            # Left part
            sub = row.row(align=True)
            sub.alignment = "LEFT"

            # Select operator
            props = sub.operator(
                Operators.Select,
                text="",
                emboss=False,
                icon=("RADIOBUT_ON" if e.selected else "RADIOBUT_OFF"),
            )
            props.mode = "TOGGLE"
            props.index = e.slvs_index
            props.highlight_hover = True

            # Visibility toggle
            sub.prop(
                e,
                "visible",
                icon_only=True,
                icon=("HIDE_OFF" if e.visible else "HIDE_ON"),
                emboss=False,
            )

            # Middle Part
            sub = row.row()
            sub.alignment = "LEFT"
            sub.prop(e, "name", text="")

            # Right part
            sub = row.row()
            sub.alignment = "RIGHT"

            # Context menu
            props = sub.operator(
                Operators.ContextMenu,
                text="",
                icon="OUTLINER_DATA_GP_LAYER",
                emboss=False,
            )
            props.highlight_hover = True
            props.highlight_active = True
            props.index = e.slvs_index

            # Delete operator
            props = sub.operator(
                Operators.DeleteEntity,
                text="",
                icon="X",
                emboss=False,
            )
            props.index = e.slvs_index
            props.highlight_hover = True

            # Props
            if e.props:
                row_props = col.row()
                row_props.alignment = "RIGHT"
                for entity_prop in e.props:
                    row_props.prop(e, entity_prop, text="")
                col.separator()


def draw_constraint_listitem(
    context: Context, layout: UILayout, constraint: GenericConstraint
):
    """
    Creates a single row inside the ``layout`` describing
    the ``constraint``.
    """
    index = context.scene.sketcher.constraints.get_index(constraint)
    row = layout.row()

    left_sub = row.row(align=True)

    # Left part
    left_sub.alignment = "LEFT"

    left_sub.prop(
        constraint,
        "visible",
        icon_only=True,
        icon=("HIDE_OFF" if constraint.visible else "HIDE_ON"),
        emboss=False,
    )

    # Failed hint
    left_sub.label(
        text="",
        icon=("ERROR" if constraint.failed else "CHECKMARK"),
    )
    # Label
    left_sub.prop(constraint, "name", text="")

    # Middle Part
    center_sub = row.row()
    center_sub.alignment = "LEFT"

    # Dimensional Constraint Values
    for constraint_prop in constraint.props:
        center_sub.prop(constraint, constraint_prop, text="")

    # # Disable interaction with element if it is "readonly"
    # center_sub.enabled = not (
    #     isinstance(constraint, DimensionalConstraint) and constraint.is_reference
    # )

    # Right part
    right_sub = row.row()
    right_sub.alignment = "RIGHT"

    # Context menu, shows constraint name
    props = right_sub.operator(
        Operators.ContextMenu, text="", icon="OUTLINER_DATA_GP_LAYER", emboss=False
    )
    props.type = constraint.type
    props.index = index
    props.highlight_hover = True
    props.highlight_active = True
    props.highlight_members = True

    # Delete operator
    props = right_sub.operator(
        Operators.DeleteConstraint,
        text="",
        icon="X",
        emboss=False,
    )
    props.type = constraint.type
    props.index = index
    props.highlight_hover = True
    props.highlight_members = True


class VIEW3D_PT_sketcher_constraints(VIEW3D_PT_sketcher_base):
    """
    Constraints Menu: List of entities in the sketch.
    Interactive
    """

    bl_label = "Constraints"
    bl_idname = Panels.SketcherContraints
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        layout = self.layout

        # Visibility Operators
        col = layout.column(align=True)
        col.operator_enum(Operators.SetAllConstraintsVisibility, "visibility")

        # Dimensional Constraints
        layout.label(text="Dimensional:")
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8

        sketch = context.scene.sketcher.active_sketch
        for c in context.scene.sketcher.constraints.dimensional:
            if not c.is_active(sketch):
                continue
            draw_constraint_listitem(context, col, c)

        # Geometric Constraints
        layout.label(text="Geometric:")
        box = layout.box()
        col = box.column(align=True)
        col.scale_y = 0.8

        sketch = context.scene.sketcher.active_sketch
        for c in context.scene.sketcher.constraints.geometric:
            if not c.is_active(sketch):
                continue
            draw_constraint_listitem(context, col, c)


class VIEW3D_MT_sketches(Menu):
    bl_label = "Sketches"
    bl_idname = Menus.Sketches

    def draw(self, context: Context):
        layout = self.layout
        sse = context.scene.sketcher.entities
        layout.operator(Operators.AddSketch).wait_for_input = True

        if len(sse.sketches):
            layout.separator()

        for i, sk in enumerate(sse.sketches):
            layout.operator(
                Operators.SetActiveSketch, text=sk.name
            ).index = sk.slvs_index


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
]

classes.extend(panel for panel in VIEW3D_PT_sketcher_base.__subclasses__())


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
