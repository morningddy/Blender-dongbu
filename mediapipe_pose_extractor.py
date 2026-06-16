#!/usr/bin/env python3
"""
MediaPipe姿态提取器
从视频中提取人体3D关键点并保存为JSON格式

输出格式：
{
    "fps": 30,
    "num_frames": 150,
    "landmarks": [
        {
            "frame": 0,
            "pose_landmarks": [
                {"x": 0.5, "y": 0.3, "z": 0.0, "visibility": 0.9},
                ... # 33个关键点
            ]
        },
        ...
    ]
}

MediaPipe姿态关键点索引（33个）：
0: nose, 1: left_eye_inner, 2: left_eye, 3: left_eye_outer,
4: right_eye_inner, 5: right_eye, 6: right_eye_outer,
7: left_ear, 8: right_ear, 9: mouth_left, 10: mouth_right,
11: left_shoulder, 12: right_shoulder, 13: left_elbow, 14: right_elbow,
15: left_wrist, 16: right_wrist, 17: left_pinky, 18: right_pinky,
19: left_index, 20: right_index, 21: left_thumb, 22: right_thumb,
23: left_hip, 24: right_hip, 25: left_knee, 26: right_knee,
27: left_ankle, 28: right_ankle, 29: left_heel, 30: right_heel,
31: left_foot_index, 32: right_foot_index
"""

import argparse
import json
import os
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path


class MediaPipePoseExtractor:
    """MediaPipe姿态提取器"""
    
    # MediaPipe关键点名称
    LANDMARK_NAMES = [
        'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
        'right_eye_inner', 'right_eye', 'right_eye_outer',
        'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
        'left_index', 'right_index', 'left_thumb', 'right_thumb',
        'left_hip', 'right_hip', 'left_knee', 'right_knee',
        'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]
    
    # 关键点索引到Blender骨骼的映射
    LANDMARK_TO_BONE = {
        11: 'LeftShoulder',  # left_shoulder
        12: 'RightShoulder',  # right_shoulder
        13: 'LeftArm',  # left_elbow
        14: 'RightArm',  # right_elbow
        15: 'LeftForeArm',  # left_wrist
        16: 'RightForeArm',  # right_wrist
        23: 'LeftUpLeg',  # left_hip
        24: 'RightUpLeg',  # right_hip
        25: 'LeftLeg',  # left_knee
        26: 'RightLeg',  # right_knee
        27: 'LeftFoot',  # left_ankle
        28: 'RightFoot',  # right_ankle
    }
    
    def __init__(self, model_complexity=2, enable_segmentation=False):
        """
        初始化MediaPipe姿态检测器
        
        Args:
            model_complexity: 模型复杂度 (0, 1, 2)
            enable_segmentation: 是否启用分割
        """
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            enable_segmentation=enable_segmentation,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        print(f"MediaPipe姿态检测器已初始化 (复杂度: {model_complexity})")
    
    def extract_from_video(self, video_path: str, output_path: str = None):
        """
        从视频中提取姿态数据
        
        Args:
            video_path: 输入视频路径
            output_path: 输出JSON文件路径（可选）
            
        Returns:
            提取的姿态数据字典
        """
        print(f"处理视频: {video_path}")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        # 获取视频信息
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"视频信息: {fps} FPS, {total_frames} 帧")
        
        # 提取数据 - 使用与 simple_mediapipe_tool.py 兼容的格式
        landmarks_data = {
            'fps': fps,
            'total_frames': total_frames,
            'video_path': video_path,
            'frames': []   # 统一使用 frames 字段
        }
        
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 转换为RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 处理帧
            results = self.pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # 提取关键点
                frame_landmarks = []
                
                for idx, landmark in enumerate(results.pose_landmarks.landmark):
                    frame_landmarks.append({
                        'idx': idx,
                        'x': round(float(landmark.x), 6),
                        'y': round(float(landmark.y), 6),
                        'z': round(float(landmark.z), 6),
                        'visibility': round(float(landmark.visibility), 4)
                    })
                
                landmarks_data['frames'].append({
                    'frame': frame_idx,
                    'landmarks': frame_landmarks
                })
            
            # 进度显示
            if frame_idx % 30 == 0:
                print(f"处理进度: {frame_idx}/{total_frames} ({frame_idx/total_frames*100:.1f}%)")
            
            frame_idx += 1
        
        cap.release()
        
        print(f"提取完成: {len(landmarks_data['landmarks'])} 帧有关键点")
        
        # 保存为JSON
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(landmarks_data, f, indent=2)
            
            print(f"Done: {len(landmarks_data['frames'])} frames saved to {output_path}")
        
        return landmarks_data
    
    def convert_to_blender_format(self, landmarks_data: dict, output_script: str, armature_name: str = None):
        """
        将MediaPipe关键点转换为Blender动画脚本
        
        Args:
            landmarks_data: 姿态数据
            output_script: 输出的Blender脚本路径
            armature_name: 骨骼对象名称
        """
        print(f"生成Blender脚本: {output_script}")
        
        num_frames = landmarks_data.get('total_frames', len(landmarks_data.get('frames', [])))
        fps = landmarks_data['fps']
        
        # 生成Blender Python脚本
        script_content = f'''# Blender动画应用脚本（MediaPipe版本）
# 自动生成

import bpy

# 动画设置
num_frames = {num_frames}
fps = {fps}

print(f"开始应用MediaPipe姿态动画: {{num_frames}} 帧")

# 获取骨骼对象
armature = None
if "{armature_name or ''}":
    armature = bpy.data.objects.get("{armature_name or ''}")

if not armature:
    # 尝试找到场景中的第一个ARMATURE对象
    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
            break

if not armature:
    print("错误: 未找到骨骼对象")
else:
    print(f"找到骨骼对象: {{armature.name}}")
    
    # 设置帧范围
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = num_frames - 1
    bpy.context.scene.render.fps = fps
    
    # 切换到POSE模式
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # 清除现有动画
    if armature.animation_data:
        armature.animation_data_clear()
    
    # 创建新的动画数据
    if not armature.animation_data:
        armature.animation_data_create()
    
    # MediaPipe姿态数据
    pose_data = {json.dumps(landmarks_data.get('frames', [])[:10], indent=4)}  # 示例前10帧

    # 应用动画（简化版本：仅设置根骨骼位置）
    # 注意：完整的IK/FK重定向需要更复杂的数学

    for frame_data in pose_data:
        frame_idx = frame_data['frame']
        bpy.context.scene.frame_set(frame_idx)

        # 提取关键点 - 兼容新旧格式
        landmarks_dict = {lm.get('idx', lm.get('index')): lm for lm in frame_data.get('landmarks', frame_data.get('pose_landmarks', []))}
        
        # 示例：使用hip关键点设置根骨骼位置
        if 23 in landmarks_dict and 24 in landmarks_dict:  # left_hip, right_hip
            left_hip = landmarks_dict[23]
            right_hip = landmarks_dict[24]
            
            # 计算臀部中心
            hip_center_x = (left_hip['x'] + right_hip['x']) / 2
            hip_center_y = (left_hip['y'] + right_hip['y']) / 2
            hip_center_z = (left_hip['z'] + right_hip['z']) / 2
            
            # 转换为Blender坐标（MediaPipe Y向下，Blender Y向上）
            if 'Hips' in armature.pose.bones:
                hip_bone = armature.pose.bones['Hips']
                hip_bone.location.x = (hip_center_x - 0.5) * 2  # 归一化到[-1, 1]
                hip_bone.location.z = (hip_center_y - 0.5) * 2  # 注意Y到Z的转换
                hip_bone.location.y = hip_center_z * 2
                
                hip_bone.keyframe_insert(data_path="location", frame=frame_idx)
        
        # 注意：完整的骨骼旋转需要使用IK解算器或更复杂的重定向算法
        print(f"已处理帧 {{frame_idx}}")
    
    # 切换回OBJECT模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    print("MediaPipe动画应用完成！")
    print("注意: 这是简化版本，仅应用了根骨骼位置。")
    print("建议: 使用Blender的IK解算器或专业重定向插件获得更好效果。")
'''

        # 保存脚本
        with open(output_script, 'w') as f:
            f.write(script_content)
        
        print(f"脚本已保存: {output_script}")
        print(f"在Blender中运行: bpy.ops.script.python_file_run(filepath='{output_script}')")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='使用MediaPipe从视频提取姿态')
    parser.add_argument('--input', type=str, required=True, help='输入视频路径')
    parser.add_argument('--output', type=str, default=None, help='输出JSON文件路径')
    parser.add_argument('--output_json', type=str, default=None, help='输出JSON文件路径(兼容)')
    parser.add_argument('--output_script', type=str, default=None, help='输出的Blender脚本路径')
    parser.add_argument('--armature_name', type=str, default=None, help='Blender中的骨骼对象名称')
    parser.add_argument('--model_complexity', type=int, default=2, choices=[0, 1, 2], help='模型复杂度')

    args = parser.parse_args()

    # 兼容两种输出参数名
    output_path = args.output_json or args.output
    if not output_path:
        # 自动生成输出路径
        video_name = os.path.splitext(os.path.basename(args.input))[0]
        output_path = f"{video_name}_pose.json"

    # 创建提取器
    extractor = MediaPipePoseExtractor(model_complexity=args.model_complexity)

    # 提取姿态
    landmarks_data = extractor.extract_from_video(args.input, output_path)

    # 如果需要，生成Blender脚本
    if args.output_script:
        extractor.convert_to_blender_format(landmarks_data, args.output_script, args.armature_name)

    print("Done!")


if __name__ == '__main__':
    main()
