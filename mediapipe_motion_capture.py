# Blender MediaPipe Motion Capture Addon v4.0
# Fully local, uses MediaPipe Tasks API (compatible with MP 0.10.x)
# v4.0: ROTATION-based bone driving (was: location-based, didn't work!)
# Auto-generates extractor script to temp dir to avoid Chinese path issues
# Author: WorkBuddy AI

bl_info = {
    "name": "MediaPipe Motion Capture (Local)",
    "author": "WorkBuddy AI",
    "version": (4, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Motion Capture",
    "description": "MediaPipe video motion capture, fully local (v4: ROTATION-based)",
    "category": "Animation",
}

import bpy
import os
import sys
import subprocess
import json
import tempfile
import math
from mathutils import Vector, Euler, Matrix
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup


# ============================================================
# Embedded extractor script template (written to temp dir to avoid Chinese paths)
# ============================================================
EXTRACTOR_SCRIPT_TEMPLATE = r'''
# -*- coding: utf-8 -*-
"""Auto-generated MediaPipe pose extractor v2 (Tasks API) - DO NOT EDIT"""
import argparse, json, os, sys, cv2, numpy as np

try:
    import mediapipe as mp
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
    from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
except ImportError as e:
    print("ERROR: mediapipe not installed or version incompatible:", e)
    sys.exit(1)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output_json", required=True)
    p.add_argument("--complexity", type=int, default=2)
    args = p.parse_args()

    model_file = os.path.join(os.path.expanduser("~"), ".mediapipe", "pose_landmarker_heavy.task")
    if not os.path.exists(model_file):
        print("Downloading pose_landmarker_heavy.task (~30MB)...")
        os.makedirs(os.path.dirname(model_file), exist_ok=True)
        try:
            import urllib.request
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
            urllib.request.urlretrieve(url, model_file)
            print("Model downloaded.")
        except Exception as e:
            print(f"ERROR: Cannot download model: {e}")
            sys.exit(1)

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_file),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    detector = PoseLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {args.input}")
        sys.exit(1)

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"INFO: Video {fps}fps {total}frames")

    frames_data = []
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = detector.detect(mp_image)

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            lms = []
            for lm in result.pose_landmarks[0]:
                lms.append({"idx": len(lms), "x":round(float(lm.x),6), "y":round(float(lm.y),6), "z":round(float(lm.z),6), "vis":round(float(lm.visibility if hasattr(lm, 'visibility') else lm.presence),4)})
            frames_data.append({"frame": idx, "landmarks": lms})

        if idx % 30 == 0:
            print(f"  ... {idx}/{total}")
        idx += 1

    cap.release()
    detector.close()

    outdir = os.path.dirname(args.output_json) or "."
    os.makedirs(outdir, exist_ok=True)
    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump({"fps": fps, "total_frames": idx, "frames": frames_data}, f, ensure_ascii=False)
    print(f"DONE: {len(frames_data)} frames -> {args.output_json}")

if __name__ == "__main__":
    main()
'''


class MotionCaptureSettings(PropertyGroup):
    video_path: StringProperty(
        name="Video File", subtype='FILE_PATH', default=""
    )
    output_path: StringProperty(
        name="Output Dir", subtype='DIR_PATH', default=""
    )
    python_path: StringProperty(
        name="Python Path", subtype='FILE_PATH',
        default=r"D:\新建文件夹\GVHMR\gvhmr_env\Scripts\python.exe"
    )
    model_complexity: IntProperty(
        name="Model Quality", default=2, min=0, max=2
    )
    auto_apply: BoolProperty(
        name="Auto Apply Animation", default=True
    )
    scale_factor: FloatProperty(
        name="Scale Factor", default=1.0, min=0.01, max=100.0
    )


class MOTION_OT_ExtractPose(Operator):
    bl_idname = "motion.extract_pose"
    bl_label = "Extract Pose"
    bl_description = "Extract human pose from video using MediaPipe"

    _timer = None
    _process = None
    _temp_script = None

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._process.poll() is not None:
                context.window_manager.event_timer_remove(self._timer)

                if self._process.returncode == 0:
                    try:
                        out = self._process.stdout.read()
                        if isinstance(out, bytes):
                            out = out.decode('utf-8', errors='replace')
                        self.report({'INFO'}, "Extraction complete!")
                    except Exception:
                        pass

                    settings = context.scene.motion_capture_settings
                    if settings.auto_apply:
                        bpy.ops.motion.apply_mediapipe_animation()
                else:
                    try:
                        err = self._process.stderr.read()
                        if isinstance(err, bytes):
                            err = err.decode('utf-8', errors='replace')
                        else:
                            err = str(err)
                    except Exception:
                        err = "(cannot read error)"
                    if self._temp_script and os.path.exists(self._temp_script):
                        try:
                            os.remove(self._temp_script)
                        except Exception:
                            pass
                    self.report({'ERROR'}, f"Failed: {err[:300]}")

                return {'FINISHED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        settings = context.scene.motion_capture_settings

        if not settings.video_path or not os.path.exists(settings.video_path):
            self.report({'ERROR'}, "Please select a valid video file")
            return {'CANCELLED'}

        python_exe = settings.python_path
        if not python_exe or not os.path.exists(python_exe):
            self.report({'ERROR'}, f"Python not found: {python_exe}")
            return {'CANCELLED'}

        if not settings.output_path:
            settings.output_path = os.path.join(os.path.dirname(__file__), "output")
        output_dir = settings.output_path
        os.makedirs(output_dir, exist_ok=True)

        video_name = os.path.splitext(os.path.basename(settings.video_path))[0]
        output_json = os.path.join(output_dir, f"{video_name}_pose.json")

        temp_dir = tempfile.gettempdir()
        temp_script = os.path.join(temp_dir, "_mp_extractor.py")
        try:
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(EXTRACTOR_SCRIPT_TEMPLATE)
        except Exception as e:
            self.report({'ERROR'}, f"Cannot write temp script: {e}")
            return {'CANCELLED'}
        self._temp_script = temp_script

        cmd = [
            python_exe,
            temp_script,
            "--input", settings.video_path,
            "--output_json", output_json,
            "--complexity", str(settings.model_complexity),
        ]

        self.report({'INFO'}, f"Processing: {os.path.basename(settings.video_path)} ...")

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            wm = context.window_manager
            self._timer = wm.event_timer_add(0.5, window=context.window)
            wm.modal_handler_add(self)

            return {'RUNNING_MODAL'}

        except Exception as e:
            self.report({'ERROR'}, f"Launch failed: {e}")
            return {'CANCELLED'}


class MOTION_OT_ApplyMediaPipeAnimation(Operator):
    bl_idname = "motion.apply_mediapipe_animation"
    bl_label = "Apply Animation"
    bl_description = "Apply extracted pose data to selected armature using ROTATIONS"

    def execute(self, context):
        armature = None
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break

        if not armature:
            self.report({'ERROR'}, "Please select an ARMATURE object first")
            return {'CANCELLED'}

        settings = context.scene.motion_capture_settings

        if not settings.video_path:
            self.report({'ERROR'}, "No video file set")
            return {'CANCELLED'}

        if not settings.output_path:
            settings.output_path = os.path.join(os.path.dirname(__file__), "output")

        video_name = os.path.splitext(os.path.basename(settings.video_path))[0]
        json_file = os.path.join(settings.output_path, f"{video_name}_pose.json")

        if not os.path.exists(json_file):
            self.report({'ERROR'}, f"Pose data not found:\n{json_file}\n\nClick Extract Pose first.")
            return {'CANCELLED'}

        try:
            self.apply_pose_to_armature(armature, json_file, settings.scale_factor)
            self.report({'INFO'}, f"Animation applied to '{armature.name}' !")
        except Exception as e:
            self.report({'ERROR'}, f"Apply failed: {e}")
            return {'CANCELLED'}

        return {'FINISHED'}

    # ================================================================
    # CORE: Rotation-based pose application
    # ================================================================
    def apply_pose_to_armature(self, armature, json_file, scale_factor):
        """Apply MediaPipe landmarks to armature using BONE ROTATIONS (not locations)."""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        frames_list = data.get('frames', [])
        fps = data.get('fps', 30)
        total_frames = data.get('total_frames', len(frames_list))

        if total_frames == 0:
            raise ValueError("No frames in pose data")

        scene = bpy.context.scene
        scene.frame_start = 0
        scene.frame_end = max(total_frames - 1, 1)
        scene.render.fps = fps

        # Switch to POSE mode
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')

        # Clear old animation
        if armature.animation_data:
            armature.animation_data_clear()
        armature.animation_data_create()

        # ============================================================
        # Build bone mapping (auto-detect Mixamo or standard naming)
        # ============================================================
        all_bone_names = list(armature.pose.bones.keys())
        print(f"[Mocap] Armature '{armature.name}' has {len(all_bone_names)} bones")
        print(f"[Mocap] All bones: {all_bone_names}")

        prefix = ""
        for bname in all_bone_names:
            if ':' in bname:
                prefix = bname.split(':')[0] + ':'
                break

        def find_bone(name):
            """Find a pose bone by trying common naming patterns."""
            for candidate in [name, name.capitalize(), name.lower(),
                             prefix + name, prefix + name.capitalize(), prefix + name.lower()]:
                if candidate in armature.pose.bones:
                    return armature.pose.bones[candidate]
            return None

        # Map: landmark index -> PoseBone object
        BONE_MAP = {}
        mappings = [
            (11, ['LeftShoulder']),   (12, ['RightShoulder']),
            (13, ['LeftArm', 'LeftForeArm']),   (14, ['RightArm', 'RightForeArm']),
            (15, ['LeftForeArm', 'LeftHand']), (16, ['RightForeArm', 'RightHand']),
            (23, ['Hips']),             (24, ['Hips']),
            (25, ['LeftLeg', 'LeftUpLeg']),(26, ['RightLeg', 'RightUpLeg']),
            (27, ['LeftFoot', 'LeftAnkle']),(28, ['RightFoot', 'RightAnkle']),
        ]
        for mp_idx, names in mappings:
            for n in names:
                b = find_bone(n)
                if b is not None and mp_idx not in BONE_MAP:
                    BONE_MAP[mp_idx] = b
                    break

        # Additional bones for spine/head
        hips_bone = find_bone('Hips')
        spine_bone = find_bone('Spine') or find_bone('Spine1') or find_bone('Spine2')
        neck_bone = find_bone('Neck')
        head_bone = find_bone('Head')

        print(f"[Mocap] Mapped {len(BONE_MAP)} landmarks to bones:")
        for mp_idx, bone in sorted(BONE_MAP.items()):
            print(f"  MP[{mp_idx}] -> '{bone.name}'")

        if len(BONE_MAP) < 3:
            raise ValueError(
                f"Too few bones matched ({len(BONE_MAP)}).\n"
                f"Available bones: {all_bone_names[:10]}...\n"
                f"Check your rig uses standard naming."
            )

        # ============================================================
        # Helper functions for angle calculation
        # ============================================================
        def get_pt(lm_dict, mp_idx):
            """Convert MP normalized coords -> Blender world-space Vector3."""
            if mp_idx not in lm_dict:
                return None
            lm = lm_dict[mp_idx]
            vis = lm.get('vis', lm.get('visibility', 1.0))
            if vis < 0.3:
                return None
            # MP: x=right(+)/left(-), y=down(+)/up(-), z=far(+)/near(-)
            # Blender: X=right(+)/left(-), Y=up(+)/down(-), Z=front(+)/back(-)
            x = (lm['x'] - 0.5) * scale_factor
            y = -(lm['y'] - 0.5) * scale_factor  # flip Y axis
            z = -lm['z'] * scale_factor
            return Vector((x, y, z))

        def calc_joint_angles(p_parent, p_joint, p_child):
            """
            Compute Euler angles at p_joint from chain parent->joint->child.
            Returns (rx, ry, rz) in radians.
            """
            if None in (p_parent, p_joint, p_child):
                return (0, 0, 0)

            v_in = (p_parent - p_joint).normalized()  # vector pointing INTO joint from parent
            v_out = (p_child - p_joint).normalized()  # vector pointing OUT of joint toward child

            if v_in.length < 0.0001 or v_out.length < 0.0001:
                return (0, 0, 0)

            # Bend angle between the two vectors
            cos_bend = max(-1.0, min(1.0, v_in.dot(v_out)))
            bend_angle = math.acos(cos_bend)  # 0 = straight, pi = fully bent

            # Bend direction axis (cross product)
            bend_axis = v_out.cross(v_in).normalized()

            # Project onto principal axes for simplified Euler decomposition
            rx = bend_axis.x * bend_angle * 0.7  # pitch
            ry = bend_axis.y * bend_angle * 0.7  # yaw
            rz = bend_axis.z * bend_angle        # roll

            return (rx, ry, rz)

        def set_rot(bone, euler_tuple, frame_idx):
            """Set bone rotation keyframe at given frame."""
            if bone is None:
                return
            try:
                rot_mode = bone.rotation_mode
                if rot_mode == 'QUATERNION':
                    q = Euler(euler_tuple, 'XYZ').to_quaternion()
                    bone.rotation_quaternion = q
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame_idx)
                elif rot_mode.startswith('AXIS'):
                    ax = Vector(euler_tuple)
                    if ax.length > 0.001:
                        ax.normalize()
                        angle = bend_angle if 'bend_angle' in dir() else ax.length
                    else:
                        ax, angle = Vector((0, 0, 1)), 0
                    from mathutils import Quaternion
                    bone.rotation_axis_angle = (angle, ax.x, ax.y, ax.z)
                    bone.keyframe_insert(data_path="rotation_axis_angle", frame=frame_idx)
                else:
                    bone.rotation_euler = Euler(euler_tuple, rot_mode)
                    bone.keyframe_insert(data_path="rotation_euler", frame=frame_idx)
            except Exception as ex:
                print(f"[Mocap] Rot error on '{bone.name}': {ex}")

        # ============================================================
        # Process each frame
        # ============================================================
        print(f"[Mocap] Processing {len(frames_list)} frames...")

        for fi, frame_data in enumerate(frames_list):
            frm = frame_data['frame']
            scene.frame_set(frm)

            lm_dict = {lm['idx']: lm for lm in frame_data['landmarks']}

            # Get all points as Vectors
            pt = {}
            for i in range(33):
                pt[i] = get_pt(lm_dict, i)

            # ---- HIPS position ----
            hip_c = pt[23] or pt[24]
            if hip_c and hips_bone:
                hips_bone.location = (hip_c.x * 0.05, hip_c.y * 0.05, hip_c.z * 0.05)
                hips_bone.keyframe_insert(data_path="location", frame=frm)

            # ---- SPINE / upper body tilt ----
            if spine_bone and pt[11] and pt[12] and (pt[23] or pt[24]):
                shldr_center = (pt[11] + pt[12]) * 0.5
                hip_center = ((pt[23] if pt[23] else pt[24]) + (pt[24] if pt[24] else pt[23])) * 0.5
                spine_vec = shldr_center - hip_center
                if spine_vec.length > 0.001:
                    s_rx = math.asin(max(-1, min(1, spine_vec.normalized().y)))
                    s_rz = math.atan2(spine_vec.x, spine_vec.z + 0.001) if abs(spine_vec.z) > 0.001 else 0
                    set_rot(spine_bone, (s_rx * 0.6, 0, s_rz * 0.6), frm)

            # ---- LEFT ARM CHAIN: Shoulder(11)->Elbow(13)->Wrist(15) ----
            # Shoulder rotation: where elbow goes relative to shoulder
            if BONE_MAP.get(11) and pt[11] and pt[13]:
                s_vec = pt[13] - pt[11]
                if s_vec.length > 0.001:
                    sv = s_vec.normalized()
                    sh_ry = math.atan2(sv.x, math.sqrt(sv.y**2 + sv.z**2 + 0.001))
                    sh_rx = math.asin(max(-1, min(1, -sv.y)))
                    sh_rz = math.atan2(sv.x, sv.z + 0.001)
                    set_rot(BONE_MAP[11], (sh_rx, sh_ry, sh_rz * 0.5), frm)

            # Elbow bend: angle at elbow between shoulder-elbow-wrist
            if BONE_MAP.get(13) and pt[11] and pt[13] and pt[15]:
                elb_rot = calc_joint_angles(pt[11], pt[13], pt[15])
                set_rot(BONE_MAP[13], elb_rot, frm)

            # Wrist/forearm: slight rotation
            if BONE_MAP.get(15) and pt[13] and pt[15]:
                wr_rot = calc_joint_angles(pt[13], pt[15],
                                           pt[15] + (pt[15] - pt[13]) * 0.15)
                set_rot(BONE_MAP[15], (wr_rot[0]*0.3, wr_rot[1]*0.3, wr_rot[2]*0.3), frm)

            # ---- RIGHT ARM CHAIN: Shoulder(12)->Elbow(14)->Wrist(16) ----
            if BONE_MAP.get(12) and pt[12] and pt[14]:
                s_vec = pt[14] - pt[12]
                if s_vec.length > 0.001:
                    sv = s_vec.normalized()
                    sh_ry = math.atan2(sv.x, math.sqrt(sv.y**2 + sv.z**2 + 0.001))
                    sh_rx = math.asin(max(-1, min(1, -sv.y)))
                    sh_rz = math.atan2(sv.x, sv.z + 0.001)
                    set_rot(BONE_MAP[12], (sh_rx, sh_ry, sh_rz * 0.5), frm)

            if BONE_MAP.get(14) and pt[12] and pt[14] and pt[16]:
                elb_rot = calc_joint_angles(pt[12], pt[14], pt[16])
                set_rot(BONE_MAP[14], elb_rot, frm)

            if BONE_MAP.get(16) and pt[14] and pt[16]:
                wr_rot = calc_joint_angles(pt[14], pt[16],
                                           pt[16] + (pt[16] - pt[14]) * 0.15)
                set_rot(BONE_MAP[16], (wr_rot[0]*0.3, wr_rot[1]*0.3, wr_rot[2]*0.3), frm)

            # ---- LEFT LEG CHAIN: Hip(23)->Knee(25)->Ankle(27) ----
            if BONE_MAP.get(25) and pt[23] and pt[25] and pt[27]:
                knee_rot = calc_joint_angles(pt[23], pt[25], pt[27])
                set_rot(BONE_MAP[25], knee_rot, frm)

            if BONE_MAP.get(27) and pt[25] and pt[27]:
                foot_pt = pt.get(29) or (pt[27] + Vector((0, -0.08*scale_factor, 0)))  # heel
                foot_rot = calc_joint_angles(pt[25], pt[27], foot_pt)
                set_rot(BONE_MAP[27], (foot_rot[0]*0.5, foot_rot[1]*0.5, foot_rot[2]*0.5), frm)

            # ---- RIGHT LEG CHAIN: Hip(24)->Knee(26)->Ankle(28) ----
            if BONE_MAP.get(26) and pt[24] and pt[26] and pt[28]:
                knee_rot = calc_joint_angles(pt[24], pt[26], pt[28])
                set_rot(BONE_MAP[26], knee_rot, frm)

            if BONE_MAP.get(28) and pt[26] and pt[28]:
                foot_pt = pt.get(30) or (pt[28] + Vector((0, -0.08*scale_factor, 0)))
                foot_rot = calc_joint_angles(pt[26], pt[28], foot_pt)
                set_rot(BONE_MAP[28], (foot_rot[0]*0.5, foot_rot[1]*0.5, foot_rot[2]*0.5), frm)

            # Progress every 50 frames
            if fi % 50 == 0:
                print(f"  ... frame {fi}/{len(frames_list)}")

        # Back to OBJECT mode
        bpy.ops.object.mode_set(mode='OBJECT')
        scene.frame_set(0)
        print(f"[Mocap] DONE! Applied {len(frames_list)} frames with ROTATION to '{armature.name}'")


class MOTION_OT_CheckDependencies(Operator):
    bl_idname = "motion.check_dependencies"
    bl_label = "Check Deps"

    def execute(self, context):
        python_exe = context.scene.motion_capture_settings.python_path or sys.executable
        try:
            result = subprocess.run(
                [python_exe, "-c", "import mediapipe; print(mediapipe.__version__)"],
                capture_output=True, timeout=15
            )
            ver = result.stdout.decode('utf-8', errors='replace').strip()
            if result.returncode == 0:
                self.report({'INFO'}, f"MediaPipe OK: {ver}")
            else:
                err = result.stderr.decode('utf-8', errors='replace').strip()[:200]
                self.report({'ERROR'}, f"MediaPipe Error: {err}")
        except FileNotFoundError:
            self.report({'ERROR'}, f"Python not found: {python_exe}")
        except Exception as e:
            self.report({'ERROR'}, f"Check failed: {e}")
        return {'FINISHED'}


class MOTION_PT_MainPanel(Panel):
    bl_label = "MediaPipe Motion Capture"
    bl_idname = "MOTION_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Motion Capture'

    def draw(self, context):
        layout = self.layout
        settings = context.scene.motion_capture_settings

        layout.label(text="Motion Capture v4.0", icon='CAMERA_DATA')

        # Settings box
        box = layout.box()
        box.label(text="Settings", icon='SETTINGS')
        box.prop(settings, "python_path")
        col = box.column(align=True)
        col.prop(settings, "model_complexity")
        col.prop(settings, "scale_factor")
        col.prop(settings, "auto_apply")

        # Video box
        box = layout.box()
        box.label(text="Video Processing", icon='FILE_MOVIE')
        box.prop(settings, "video_path")
        box.prop(settings, "output_path")
        row = box.row(align=True)
        row.operator("motion.extract_pose", icon='PLAY')
        row.operator("motion.check_dependencies", icon='CHECKMARK')

        # Apply box
        box = layout.box()
        box.label(text="Apply Animation", icon='ARMATURE_DATA')

        sel_arm = None
        if context.selected_objects:
            for o in context.selected_objects:
                if o.type == 'ARMATURE':
                    sel_arm = o
                    break

        if sel_arm:
            box.label(text=f"Target: {sel_arm.name}", icon='ARMATURE_DATA')
        else:
            row = box.row()
            row.label(text="(Select an ARMATURE)", icon='ERROR')
            row.enabled = False

        box.operator("motion.apply_mediapipe_animation", icon='KEY_HLT')


classes = (
    MotionCaptureSettings,
    MOTION_OT_ExtractPose,
    MOTION_OT_ApplyMediaPipeAnimation,
    MOTION_OT_CheckDependencies,
    MOTION_PT_MainPanel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.motion_capture_settings = PointerProperty(type=MotionCaptureSettings)
    print("MediaPipe Motion Capture v4.0 registered OK")


def unregister():
    if hasattr(bpy.types.Scene, 'motion_capture_settings'):
        del bpy.types.Scene.motion_capture_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
