# Blender Video Motion Retargeting Addon
# 基于GVHMR和HaMeR项目实现视频驱动角色动画
# 作者: WorkBuddy AI
# 版本: 1.0

bl_info = {
    "name": "Video Motion Retargeting",
    "author": "WorkBuddy AI",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Motion Retarget",
    "description": "从视频中提取动作并应用到绑定角色",
    "warning": "",
    "wiki_url": "",
    "category": "Animation",
}

import bpy
import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from bpy.props import StringProperty, PointerProperty, EnumProperty, BoolProperty, FloatProperty
from bpy.types import Panel, Operator, PropertyGroup

# ------------------------------------------------------------
# 全局配置
# ------------------------------------------------------------
class MotionRetargetSettings(PropertyGroup):
    """插件设置属性组"""
    
    # GVHMR路径
    gvhmr_path: StringProperty(
        name="GVHMR路径",
        description="GVHMR项目根目录",
        subtype='DIR_PATH',
        default=""
    )
    
    # 视频文件路径
    video_path: StringProperty(
        name="视频文件",
        description="输入视频文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    # 输出目录
    output_path: StringProperty(
        name="输出目录",
        description="动作数据输出目录",
        subtype='DIR_PATH',
        default=""
    )
    
    # Python解释器路径
    python_path: StringProperty(
        name="Python路径",
        description="GVHMR使用的Python解释器路径",
        subtype='FILE_PATH',
        default=""
    )
    
    # 静态相机模式
    static_camera: BoolProperty(
        name="静态相机",
        description="视频使用静态相机拍摄（跳过视觉里程计计算）",
        default=True
    )
    
    # 焦距设置（mm）
    focal_length: FloatProperty(
        name="焦距",
        description="相机焦距（mm），用于自定义相机内参",
        default=50.0,
        min=10.0,
        max=200.0
    )
    
    # 是否应用动画
    auto_apply: BoolProperty(
        name="自动应用动画",
        description="处理完成后自动将动画应用到选中角色",
        default=True
    )


# ------------------------------------------------------------
# 核心功能类
# ------------------------------------------------------------
class MOTION_OT_InstallDependencies(Operator):
    """安装GVHMR依赖"""
    
    bl_idname = "motion.install_dependencies"
    bl_label = "安装依赖"
    bl_description = "安装GVHMR所需的Python依赖包"
    
    def execute(self, context):
        settings = context.scene.motion_retarget_settings
        
        if not settings.gvhmr_path:
            self.report({'ERROR'}, "请先设置GVHMR路径")
            return {'CANCELLED'}
        
        # 检查requirements.txt
        req_file = os.path.join(settings.gvhmr_path, "requirements.txt")
        if not os.path.exists(req_file):
            self.report({'ERROR'}, f"未找到requirements.txt: {req_file}")
            return {'CANCELLED'}
        
        # 安装依赖
        try:
            python_exe = settings.python_path if settings.python_path else sys.executable
            
            self.report({'INFO'}, "开始安装依赖...")
            
            # 安装requirements.txt
            result = subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", req_file],
                cwd=settings.gvhmr_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.report({'INFO'}, "依赖安装成功")
            else:
                self.report({'ERROR'}, f"安装失败: {result.stderr}")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"安装过程出错: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class MOTION_OT_ProcessVideo(Operator):
    """处理视频提取动作数据"""
    
    bl_idname = "motion.process_video"
    bl_label = "处理视频"
    bl_description = "使用GVHMR从视频中提取动作数据"
    
    _timer = None
    _process = None
    _output_file = None
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            if self._process.poll() is not None:
                # 处理完成
                context.window_manager.event_timer_remove(self._timer)
                
                if self._process.returncode == 0:
                    self.report({'INFO'}, "视频处理完成")
                    
                    # 自动应用动画
                    settings = context.scene.motion_retarget_settings
                    if settings.auto_apply:
                        self.apply_animation(context)
                else:
                    self.report({'ERROR'}, "视频处理失败")
                
                return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def execute(self, context):
        settings = context.scene.motion_retarget_settings
        
        # 验证输入
        if not settings.gvhmr_path:
            self.report({'ERROR'}, "请先设置GVHMR路径")
            return {'CANCELLED'}
        
        if not settings.video_path:
            self.report({'ERROR'}, "请选择视频文件")
            return {'CANCELLED'}
        
        if not os.path.exists(settings.video_path):
            self.report({'ERROR'}, f"视频文件不存在: {settings.video_path}")
            return {'CANCELLED'}
        
        # 设置输出目录
        if not settings.output_path:
            settings.output_path = tempfile.mkdtemp()
        
        output_dir = settings.output_path
        os.makedirs(output_dir, exist_ok=True)
        
        # 构建GVHMR命令
        python_exe = settings.python_path if settings.python_path else sys.executable
        demo_script = os.path.join(settings.gvhmr_path, "tools", "demo", "demo.py")
        
        # 确保输出目录存在
        if not settings.output_path:
            settings.output_path = os.path.join(settings.gvhmr_path, "outputs", "demo")
        
        output_dir = settings.output_path
        os.makedirs(output_dir, exist_ok=True)
        
        # 获取视频文件名（不含扩展名）
        video_name = os.path.splitext(os.path.basename(settings.video_path))[0]
        
        cmd = [
            python_exe,
            demo_script,
            f"--video={settings.video_path}",
            f"--output_root={output_dir}"
        ]
        
        # 静态相机参数
        if settings.static_camera:
            cmd.append("-s")
        
        # 焦距参数（如果设置了）
        if settings.focal_length > 0 and settings.focal_length != 50.0:
            cmd.append(f"--f_mm={settings.focal_length}")
        
        self.report({'INFO'}, f"执行命令: {' '.join(cmd)}")
        
        # 启动处理进程
        try:
            self.report({'INFO'}, f"开始处理视频: {settings.video_path}")
            
            self._process = subprocess.Popen(
                cmd,
                cwd=settings.gvhmr_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 设置定时器监控进程
            wm = context.window_manager
            self._timer = wm.event_timer_add(0.5, window=context.window)
            wm.modal_handler_add(self)
            
            return {'RUNNING_MODAL'}
            
        except Exception as e:
            self.report({'ERROR'}, f"启动处理失败: {str(e)}")
            return {'CANCELLED'}
    
    def apply_animation(self, context):
        """将处理后的动作数据应用到选中角色"""
        settings = context.scene.motion_retarget_settings
        
        # 查找输出的动作数据文件
        output_dir = settings.output_path
        if not output_dir or not os.path.exists(output_dir):
            self.report({'WARNING'}, "未找到输出目录")
            return
        
        # GVHMR输出的结果文件名格式：<video_name>_hmr4d.pt
        video_name = os.path.splitext(os.path.basename(settings.video_path))[0]
        result_file = None
        
        # 在输出目录中查找.pt文件
        for file in os.listdir(output_dir):
            if file.endswith('.pt') and video_name in file:
                result_file = os.path.join(output_dir, file)
                break
        
        if not result_file:
            # 如果没找到匹配的文件，尝试找任何.pt文件
            for file in os.listdir(output_dir):
                if file.endswith('.pt'):
                    result_file = os.path.join(output_dir, file)
                    break
        
        if not result_file:
            self.report({'ERROR'}, f"未找到动作数据文件(.pt)在: {output_dir}")
            return
        
        self.report({'INFO'}, f"找到动作数据: {result_file}")
        
        # 调用数据转换脚本
        self.convert_and_apply(context, result_file)


class MOTION_OT_ApplyAnimation(Operator):
    """应用动作数据到角色"""
    
    bl_idname = "motion.apply_animation"
    bl_label = "应用动画"
    bl_description = "将动作数据应用到选中的绑定角色"
    
    def execute(self, context):
        # 检查是否选中了角色
        if len(context.selected_objects) == 0:
            self.report({'ERROR'}, "请先选择一个绑定角色")
            return {'CANCELLED'}
        
        # 获取选中的 armature 对象
        armature = None
        for obj in context.selected_objects:
            if obj.type == 'ARMATURE':
                armature = obj
                break
        
        if not armature:
            self.report({'ERROR'}, "选中的对象不是有效的骨骼绑定对象")
            return {'CANCELLED'}
        
        settings = context.scene.motion_retarget_settings
        
        # 读取动作数据
        output_dir = settings.output_path
        if not output_dir or not os.path.exists(output_dir):
            self.report({'ERROR'}, "请先处理视频生成动作数据")
            return {'CANCELLED'}
        
        # TODO: 实现实际的动作数据读取和应用逻辑
        # 这里需要解析GVHMR的输出格式，并映射到骨骼
        
        self.report({'INFO'}, f"开始将动作应用到角色: {armature.name}")
        
        # 示例：创建简单的旋转动画（占位符）
        self.create_demo_animation(armature)
        
        return {'FINISHED'}
    
    def create_demo_animation(self, armature):
        """创建演示动画（实际应该读取GVHMR输出）"""
        # 这里只是示例，实际需要解析GVHMR的输出数据
        
        # 获取骨骼
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        
        # 示例：对一些骨骼添加关键帧
        if 'Hips' in armature.pose.bones:
            hip_bone = armature.pose.bones['Hips']
            
            # 清除现有动画
            hip_bone.keyframe_insert(data_path="location", frame=1)
            
            # 添加一些示例关键帧
            for frame in range(1, 250, 10):
                hip_bone.location.y = 0.1 * (frame % 20) / 20.0
                hip_bone.keyframe_insert(data_path="location", frame=frame)
        
        bpy.ops.object.mode_set(mode='OBJECT')


class MOTION_OT_DownloadModels(Operator):
    """下载GVHMR预训练模型"""
    
    bl_idname = "motion.download_models"
    bl_label = "下载模型"
    bl_description = "下载GVHMR预训练模型"
    
    def execute(self, context):
        settings = context.scene.motion_retarget_settings
        
        if not settings.gvhmr_path:
            self.report({'ERROR'}, "请先设置GVHMR路径")
            return {'CANCELLED'}
        
        # 检查是否有下载脚本
        download_script = os.path.join(settings.gvhmr_path, "scripts", "download_checkpoints.sh")
        
        if os.path.exists(download_script):
            try:
                python_exe = settings.python_path if settings.python_path else sys.executable
                
                result = subprocess.run(
                    ["bash", download_script],
                    cwd=settings.gvhmr_path,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.report({'INFO'}, "模型下载成功")
                else:
                    self.report({'ERROR'}, f"下载失败: {result.stderr}")
                    return {'CANCELLED'}
                    
            except Exception as e:
                self.report({'ERROR'}, f"下载过程出错: {str(e)}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "未找到下载脚本，请手动下载模型")
        
        return {'FINISHED'}


# ------------------------------------------------------------
# UI面板
# ------------------------------------------------------------
class MOTION_PT_MainPanel(Panel):
    """主面板"""
    
    bl_label = "Video Motion Retargeting"
    bl_idname = "MOTION_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Motion Retarget'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.motion_retarget_settings
        
        # 标题
        layout.label(text="视频动作重定向", icon='ANIM')
        
        # 设置区域
        box = layout.box()
        box.label(text="设置", icon='SETTINGS')
        
        # GVHMR路径
        box.prop(settings, "gvhmr_path")
        
        # Python路径
        box.prop(settings, "python_path")
        
        # 按钮行
        row = box.row()
        row.operator("motion.install_dependencies", icon='PACKAGE')
        row.operator("motion.download_models", icon='IMPORT')
        
        # 视频处理区域
        box = layout.box()
        box.label(text="视频处理", icon='FILE_MOVIE')
        
        # 视频文件
        box.prop(settings, "video_path")
        
        # 输出目录
        box.prop(settings, "output_path")
        
        # 参数设置
        col = box.column(align=True)
        col.prop(settings, "static_camera")
        col.prop(settings, "focal_length")
        col.prop(settings, "auto_apply")
        
        # 处理按钮
        box.operator("motion.process_video", icon='PLAY')
        
        # 动画应用区域
        box = layout.box()
        box.label(text="动画应用", icon='ARMATURE_DATA')
        
        # 显示选中的对象
        if len(context.selected_objects) > 0:
            selected = context.selected_objects[0]
            box.label(text=f"选中: {selected.name}")
        else:
            box.label(text="未选中对象")
        
        box.operator("motion.apply_animation", icon='KEY_HLT')


# ------------------------------------------------------------
# 注册和注销
# ------------------------------------------------------------
classes = (
    MotionRetargetSettings,
    MOTION_OT_InstallDependencies,
    MOTION_OT_ProcessVideo,
    MOTION_OT_ApplyAnimation,
    MOTION_OT_DownloadModels,
    MOTION_PT_MainPanel,
)

def register():
    """注册插件"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册属性组
    bpy.types.Scene.motion_retarget_settings = PointerProperty(type=MotionRetargetSettings)
    
    print("Video Motion Retargeting插件已注册")


def unregister():
    """注销插件"""
    # 注销属性组
    if hasattr(bpy.types.Scene, 'motion_retarget_settings'):
        del bpy.types.Scene.motion_retarget_settings
    
    # 注销类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("Video Motion Retargeting插件已注销")


if __name__ == "__main__":
    register()
