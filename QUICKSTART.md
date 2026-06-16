# MediaPipe Motion Capture - 快速使用指南

## 🎯 概述

这是一个**完全本地运行**的视频动作捕捉方案，使用Google MediaPipe，无需任何外部API调用。

---

## 📦 已包含的文件

1. **simple_mediapipe_tool.py** - 简化版命令行工具（推荐）
2. **mediapipe_pose_extractor.py** - 完整版姿态提取器
3. **mediapipe_motion_capture.py** - Blender插件版本
4. **README_MediaPipe.md** - 详细文档

---

## 🚀 快速开始（3步搞定）

### 步骤1：安装MediaPipe

在**系统Python**中安装MediaPipe（不是Blender内置Python）：

```bash
# Windows
pip install mediapipe opencv-python numpy

# 或者使用GVHMR虚拟环境
cd D:\新建文件夹\GVHMR
source gvhmr_env/Scripts/activate
pip install mediapipe
```

**验证安装：**
```bash
python -c "import mediapipe; print('MediaPipe已安装')"
```

---

### 步骤2：处理视频

使用 `simple_mediapipe_tool.py` 从视频中提取动作：

```bash
# 基本用法
python simple_mediapipe_tool.py --input path/to/video.mp4

# 完整参数
python simple_mediapipe_tool.py \
    --input path/to/video.mp4 \
    --output_json pose_data.json \
    --output_script blender_animation.py
```

**输出文件：**
- `pose_data.json` - 提取的姿态关键点数据
- `blender_animation.py` - 可直接在Blender中运行的脚本

---

### 步骤3：在Blender中应用动画

1. **打开Blender**
2. **切换到Scripting工作区**
3. **打开生成的脚本**（`blender_animation.py`）
4. **点击"Run Script"按钮**
5. **查看动画效果**

或者，如果你想指定骨骼对象名称：

```bash
python simple_mediapipe_tool.py \
    --input video.mp4 \
    --armature "Armature"  # 你的骨骼对象名称
```

然后在Blender中运行生成的脚本，它会自动找到名为"Armature"的骨骼对象。

---

## 📝 完整使用示例

### 示例1：处理示例视频

```bash
# 1. 准备一个视频文件（例如：dance.mp4）
# 2. 运行处理工具
python simple_mediapipe_tool.py --input dance.mp4

# 3. 输出：
#    - dance_pose.json (姿态数据)
#    - dance_blender_animation.py (Blender脚本)

# 4. 打开Blender，运行生成的脚本
```

### 示例2：批量处理多个视频

```bash
# 创建批处理脚本 process_all.py
import os
import subprocess

video_dir = "videos/"
for video in os.listdir(video_dir):
    if video.endswith(('.mp4', '.avi', '.mov')):
        cmd = [
            'python', 'simple_mediapipe_tool.py',
            '--input', os.path.join(video_dir, video)
        ]
        subprocess.run(cmd)
```

---

## 🦴 骨骼映射说明

MediaPipe检测到33个人体关键点，插件会尝试映射到常见的Blender骨骼命名：

| MediaPipe索引 | 关键点名称 | 常见Blender骨骼 |
|--------------|-------------|-------------------|
| 11, 12 | 左右肩膀 | LeftShoulder, RightShoulder |
| 13, 14 | 左右手肘 | LeftArm, RightArm |
| 15, 16 | 左右手腕 | LeftForeArm, RightForeArm |
| 23, 24 | 左右臀部 | LeftUpLeg, RightUpLeg |
| 25, 26 | 左右膝盖 | LeftLeg, RightLeg |
| 27, 28 | 左右脚踝 | LeftFoot, RightFoot |

### 自定义映射

如果你的角色使用不同的骨骼命名，需要修改 `simple_mediapipe_tool.py` 中的映射逻辑，或者在生成的Blender脚本中手动调整。

---

## ⚙️ 参数调整

### 模型复杂度

MediaPipe提供3种模型复杂度：

- **0** - 最快，准确度最低（实时预览用）
- **1** - 平衡速度和准确度
- **2** - 最准确，速度较慢（**推荐**）

修改方法：编辑 `simple_mediapipe_tool.py`，找到这行：

```python
pose = mp_pose.Pose(
    model_complexity=2,  # 改成 0, 1, 或 2
    ...
)
```

---

## 🐛 常见问题

### 问题1：MediaPipe安装失败

**错误信息：** `ModuleNotFoundError: No module named 'mediapipe'`

**解决方案：**
1. 确认使用正确的Python环境
2. 尝试：`pip install --upgrade pip` 然后重新安装
3. 如果使用虚拟环境，确保已激活

### 问题2：视频处理失败

**错误信息：** `无法打开视频` 或 `姿态检测失败`

**解决方案：**
1. 检查视频文件路径是否包含中文或特殊字符（建议改用英文路径）
2. 尝试将视频转换为MP4格式：
   ```bash
   ffmpeg -i input.avi -c:v libx264 output.mp4
   ```
3. 确保视频中有清晰、全身可见的人物

### 问题3：动画应用后角色扭曲

**症状：** 角色肢体出现异常旋转或位置

**解决方案：**
1. 确保角色处于**T-Pose**或**A-Pose**状态
2. 检查角色的骨骼命名是否与映射表匹配
3. 调整生成脚本中的缩放因子（修改 `(center_x - 0.5) * 2` 中的 `2` 为其他值）
4. 使用Blender的**Inverse Kinematics (IK)** 解算器进行精细调整

---

## 📚 进一步学习

### MediaPipe官方资源
- 姿势检测文档：https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- Python API参考：https://developers.google.com/mediapipe/api/solutions/python

### Blender动画资源
- Blender动画系统：https://docs.blender.org/manual/en/latest/animation/
- Python API - 动画：https://docs.blender.org/api/current/bpy.types.Action.html
- IK/FK切换教程：https://www.youtube.com/watch?v=BVqX2oFpZfU

### 动作捕捉技巧
- 角色绑定基础：https://www.blender.org/manual/animation/armatures/
- 动作清理技巧：https://www.youtube.com/watch?v=JpvPZ4TNbVA

---

## 🎉 完成！

现在你应该可以：

1. ✅ 安装并使用MediaPipe进行动作捕捉
2. ✅ 从视频中提取人体姿态数据
3. ✅ 将姿态数据应用到Blender角色
4. ✅ 调整参数以获得最佳效果

---

## 📄 文件清单

```
blender动作捕捉/
├── simple_mediapipe_tool.py       # 简化版工具（推荐）
├── mediapipe_pose_extractor.py   # 完整版提取器
├── mediapipe_motion_capture.py   # Blender插件
├── README_MediaPipe.md           # 详细文档
├── QUICKSTART.md                 # 本快速指南
└── test_mediapipe.py            # 测试脚本
```

---

## 💡 提示

- **第一次使用？** 从 `simple_mediapipe_tool.py` 开始，它最简单
- **需要更多控制？** 使用 `mediapipe_pose_extractor.py` 的完整功能
- **想要Blender集成？** 安装 `mediapipe_motion_capture.py` 插件
- **遇到问题？** 查看 `README_MediaPipe.md` 的详细故障排查部分

---

**祝你使用愉快！** 🎊

如果有任何问题或建议，欢迎反馈。
