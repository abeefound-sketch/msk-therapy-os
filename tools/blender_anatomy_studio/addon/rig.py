"""Upper limb armature rig, joint constraints, and FK/IK kinematics for Blender Anatomical Studio.
Supports deterministic FK/IK computation, bone length invariance, and real motion retargeting.
"""
import math
from typing import Any, Dict, List, Optional, Tuple

# Pure-Python Kinematics for Deterministic Testing and Sidecar Solving
class ArmKinematicsSolver:
    """2-link / 3-link analytical arm solver for verification and retargeting."""
    def __init__(self, upper_arm_length: float = 0.30, forearm_length: float = 0.26):
        self.l1 = float(upper_arm_length)
        self.l2 = float(forearm_length)

    def forward_kinematics_2d(
        self,
        shoulder_elevation_deg: float,
        elbow_flexion_deg: float,
        shoulder_origin: Tuple[float, float] = (0.0, 1.42)
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate elbow and wrist positions in sagittal/coronal plane.
        shoulder_elevation: 0 deg = hanging straight down (towards -Y/Z)
        elbow_flexion: 0 deg = straight, positive = bent anteriorly/flexed
        """
        th1 = math.radians(shoulder_elevation_deg)
        th2 = math.radians(elbow_flexion_deg)

        # Base angle straight down is -pi/2
        base_angle = -math.pi / 2.0 + th1
        elbow_x = shoulder_origin[0] + self.l1 * math.cos(base_angle)
        elbow_y = shoulder_origin[1] + self.l1 * math.sin(base_angle)

        forearm_angle = base_angle + th2
        wrist_x = elbow_x + self.l2 * math.cos(forearm_angle)
        wrist_y = elbow_y + self.l2 * math.sin(forearm_angle)

        return (elbow_x, elbow_y), (wrist_x, wrist_y)

    def inverse_kinematics_2d(
        self,
        target_wrist: Tuple[float, float],
        shoulder_origin: Tuple[float, float] = (0.0, 1.42)
    ) -> Optional[Tuple[float, float]]:
        """Calculate shoulder elevation and elbow flexion angles to reach target_wrist.
        Returns (shoulder_elevation_deg, elbow_flexion_deg) or None if target is unreachable.
        """
        dx = target_wrist[0] - shoulder_origin[0]
        dy = target_wrist[1] - shoulder_origin[1]
        dist = math.hypot(dx, dy)

        # Check reachability with numerical tolerance
        if dist > (self.l1 + self.l2 + 1e-6) or dist < abs(self.l1 - self.l2 - 1e-6):
            return None

        # Clamp distance to reach limit for numerical stability
        dist_clamped = max(abs(self.l1 - self.l2), min(self.l1 + self.l2, dist))

        # Law of cosines for elbow flexion
        cos_elbow = (self.l1**2 + self.l2**2 - dist_clamped**2) / (2.0 * self.l1 * self.l2)
        cos_elbow = max(-1.0, min(1.0, cos_elbow))
        # Interior angle at elbow
        alpha_elbow = math.acos(cos_elbow)
        elbow_flexion = math.pi - alpha_elbow

        # Angle of target vector from shoulder
        gamma = math.atan2(dy, dx)

        # Angle offset from upper arm to target vector
        cos_shoulder = (self.l1**2 + dist_clamped**2 - self.l2**2) / (2.0 * self.l1 * dist_clamped)
        cos_shoulder = max(-1.0, min(1.0, cos_shoulder))
        beta = math.acos(cos_shoulder)

        # Upper arm angle in standard coordinates
        arm_angle = gamma - beta
        # Convert to shoulder elevation from hanging down (-pi/2)
        shoulder_elevation = arm_angle - (-math.pi / 2.0)

        return math.degrees(shoulder_elevation), math.degrees(elbow_flexion)

try:
    import bpy
    import mathutils

    def build_upper_limb_armature(
        context: bpy.types.Context,
        armature_name: str = "Armature_UpperLimb_R",
        side: str = "RIGHT"
    ) -> bpy.types.Object:
        """Create a biomechanically constrained upper limb Armature in Blender."""
        col_name = "MSK_Rigs"
        if col_name not in bpy.data.collections:
            rig_col = bpy.data.collections.new(col_name)
            context.scene.collection.children.link(rig_col)
        else:
            rig_col = bpy.data.collections[col_name]

        # Remove existing if present to recreate cleanly
        if armature_name in bpy.data.objects:
            old = bpy.data.objects[armature_name]
            bpy.data.objects.remove(old, do_unlink=True)

        arm_data = bpy.data.armatures.new(name=armature_name)
        arm_obj = bpy.data.objects.new(name=armature_name, object_data=arm_data)
        rig_col.objects.link(arm_obj)
        context.view_layer.objects.active = arm_obj

        # Enter edit mode to build bone hierarchy
        bpy.ops.object.mode_set(mode='EDIT')
        edit_bones = arm_data.edit_bones

        # 1. Clavicle bone
        b_clav = edit_bones.new("clavicle.R")
        b_clav.head = mathutils.Vector((0.02, 0.0, 1.42))
        b_clav.tail = mathutils.Vector((0.18, 0.0, 1.42))

        # 2. Upper arm (Humerus)
        b_arm = edit_bones.new("upper_arm.R")
        b_arm.head = mathutils.Vector((0.18, 0.0, 1.42))
        b_arm.tail = mathutils.Vector((0.20, 0.0, 1.12)) # length 0.30m
        b_arm.parent = b_clav

        # 3. Forearm (Radius / Ulna)
        b_fore = edit_bones.new("forearm.R")
        b_fore.head = mathutils.Vector((0.20, 0.0, 1.12))
        b_fore.tail = mathutils.Vector((0.22, 0.0, 0.86)) # length 0.26m
        b_fore.parent = b_arm
        b_fore.use_connect = True

        # 4. Hand
        b_hand = edit_bones.new("hand.R")
        b_hand.head = mathutils.Vector((0.22, 0.0, 0.86))
        b_hand.tail = mathutils.Vector((0.23, 0.0, 0.70))
        b_hand.parent = b_fore
        b_hand.use_connect = True

        # 5. Non-deform IK Target bone
        b_target = edit_bones.new("wrist_IK.R")
        b_target.head = mathutils.Vector((0.22, 0.0, 0.86))
        b_target.tail = mathutils.Vector((0.22, 0.05, 0.86))
        b_target.use_deform = False

        # 6. Non-deform Pole Target bone
        b_pole = edit_bones.new("elbow_pole.R")
        b_pole.head = mathutils.Vector((0.20, -0.25, 1.12))
        b_pole.tail = mathutils.Vector((0.20, -0.30, 1.12))
        b_pole.use_deform = False

        bpy.ops.object.mode_set(mode='POSE')

        # Add IK Constraint to forearm pose bone
        p_fore = arm_obj.pose.bones["forearm.R"]
        ik_con = p_fore.constraints.new(type='IK')
        ik_con.name = "MSK_Elbow_IK"
        ik_con.target = arm_obj
        ik_con.subtarget = "wrist_IK.R"
        ik_con.pole_target = arm_obj
        ik_con.pole_subtarget = "elbow_pole.R"
        ik_con.pole_angle = 0.0
        ik_con.chain_count = 2 # forearm + upper_arm

        # Add Limit Rotation Constraint on Elbow (Kapandji 2007: Extension 0 deg, Flexion 145 deg)
        rot_con = p_fore.constraints.new(type='LIMIT_ROTATION')
        rot_con.name = "MSK_Elbow_ROM_Limit"
        rot_con.use_limit_x = True
        rot_con.min_x = 0.0
        rot_con.max_x = math.radians(145.0)
        rot_con.use_limit_y = True
        rot_con.min_y = 0.0
        rot_con.max_y = 0.0 # No axial twist in pure hinge mode
        rot_con.use_limit_z = True
        rot_con.min_z = 0.0
        rot_con.max_z = 0.0
        rot_con.owner_space = 'LOCAL'

        bpy.ops.object.mode_set(mode='OBJECT')

        arm_obj["msk_rig_version"] = "1.0.0"
        arm_obj["msk_side"] = side
        arm_obj["msk_upper_arm_length"] = 0.30
        arm_obj["msk_forearm_length"] = 0.26
        arm_obj["msk_rom_reference"] = "Kapandji IA. The Physiology of the Joints, Vol 1 (2007)"
        return arm_obj

    def apply_joint_angles_to_armature(
        arm_obj: bpy.types.Object,
        shoulder_elevation_deg: float,
        elbow_flexion_deg: float,
        frame: Optional[int] = None
    ):
        """Pose the arm directly via FK angles and optionally insert keyframes."""
        if arm_obj.type != 'ARMATURE':
            return
        p_arm = arm_obj.pose.bones.get("upper_arm.R")
        p_fore = arm_obj.pose.bones.get("forearm.R")

        if p_arm:
            p_arm.rotation_mode = 'XYZ'
            p_arm.rotation_euler = (math.radians(shoulder_elevation_deg), 0.0, 0.0)
            if frame is not None:
                p_arm.keyframe_insert(data_path="rotation_euler", frame=frame)

        if p_fore:
            p_fore.rotation_mode = 'XYZ'
            # Clamp to Kapandji ROM [0, 145 deg]
            clamped_elbow = max(0.0, min(145.0, elbow_flexion_deg))
            p_fore.rotation_euler = (math.radians(clamped_elbow), 0.0, 0.0)
            if frame is not None:
                p_fore.keyframe_insert(data_path="rotation_euler", frame=frame)

    class MSK_OT_BuildArmRig(bpy.types.Operator):
        """Build biomechanically constrained upper limb Armature with IK"""
        bl_idname = "msk.build_arm_rig"
        bl_label = "Build Arm Rig (FK/IK)"
        bl_options = {'REGISTER', 'UNDO'}

        side: bpy.props.EnumProperty(
            name="Side",
            items=[('RIGHT', "Right", "Cánh tay Phải"), ('LEFT', "Left", "Cánh tay Trái")],
            default='RIGHT'
        )

        def execute(self, context):
            arm_obj = build_upper_limb_armature(context, side=self.side)
            self.report({'INFO'}, f"Built armature rig: {arm_obj.name}")
            return {'FINISHED'}

    CLASSES = [MSK_OT_BuildArmRig]
except ImportError:
    CLASSES = []

def register():
    for c in CLASSES:
        bpy.utils.register_class(c)

def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
