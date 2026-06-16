# MediaPipe Motion Capture - 完全本地化Blender动作捕捉插件

## 🎯 概述

这是一个**完全本地运行**的Blender插件，使用Google MediaPipe进行视频动作捕捉，**无需任何外部API调用**。

### 核心优势

- ✅ **完全本地** - 所有处理在本地完成，无需联网
- ✅ **易于安装** - 仅需 `pip install mediapipe`
- ✅ **跨平台** - 支持Windows、Mac、Linux
- ✅ **实时性能** - MediaPipe优化良好，处理速度快
- ✅ **免费开源** - MediaPipe是完全开源的

---

## 📦 安装步骤

### 1. 安装MediaPipe

在Blender的Python环境中安装MediaPipe：

**方法A：使用Blender内置Python**
```bash
# 找到Blender的Python路径（示例）
# Windows: C:\Program Files\Blender Foundation\Blender 4.0\4.0\python\bin\python.exe
# Mac: /Applications/Blender.app/Contents/Resources/4.0/python/bin/python3.10
# Linux: /usr/lib/blender/4.0/python/bin/python3.10

# 安装MediaPipe
path/to/blender/python -m pip install mediapipe
```

**方法B：使用系统Python（推荐）**
```bash
# 在系统Python中安装
pip install mediapipe

# 然后在插件设置中指定该Python路径
```

### 2. 安装Blender插件

1. 打开Blender
2. 进入 `编辑(Edit)` → `偏好设置(Preferences)` → `插件(Add-ons)`
3. 点击 `安装(Install...)` 按钮
4. 选择 `mediapipe_motion_capture.py` 文件
5. 启用插件（勾选复选框）
6. 在右侧面板找到 `Motion Capture` 标签页

---

## 🚀 快速开始

### 示例1：基础使用

1. **检查依赖**
   - 在 `Motion Capture` 面板中点击 `检查依赖` 按钮
   - 如果显示错误，点击 `安装MediaPipe` 按钮

2. **配置路径**
   - 设置 `提取器脚本` 为 `mediapipe_pose_extractor.py` 的路径
   - 设置 `Python路径` 为系统Python路径（例如 `C:\Python39\python.exe`）

3. **选择视频**
   - 点击 `视频文件` 旁边的文件夹图标
   - 选择一个包含清晰人物的视频（建议MP4格式）

4. **提取姿态**
   - 点击 `提取姿态` 按钮
   - 等待处理完成（进度会在Blender系统控制台显示）

5. **应用动画**
   - 在Blender场景中选中你的角色（ARMATURE对象）
   - 点击 `应用MediaPipe动画` 按钮
   - 动画将自动应用到你的角色

---

## 📝 详细使用说明

### 参数说明

#### 模型复杂度
- **0** - 最快，准确度较低（适合实时预览）
- **1** - 平衡速度和准确度
- **2** - 最准确，速度较慢（**推荐**）

#### 帧采样率
- **1** - 处理每一帧（最准确，速度慢）
- **2** - 每隔1帧处理一次（加快速度）
- **N** - 每隔N-1帧处理一次

#### 缩放因子
- 调整动作幅度（默认值：1.0）
- 如果角色运动幅度太小，增大此值
- 如果角色运动幅度太大，减小此值

---

## 🎬 视频要求

为了获得最佳效果，你的视频应该：

1. **人物清晰** - 全身可见，无遮挡
2. **光线充足** - 避免过暗或过亮
3. **背景简单** - 避免复杂背景（纯色背景最佳）
4. **格式支持** - MP4、AVI、MOV等常见格式
5. **分辨率** - 建议720p或1080p
6. **帧率** - 建议30fps或60fps

### 示例视频

你可以使用任何包含人物的视频进行测试。如果没有，可以：
- 自己录制一段视频
- 从网上下载示例视频
- 使用Blender的默认动画渲染视频

---

## 🦴 骨骼映射

MediaPipe检测到33个人体关键点，插件会将其映射到常见的Blender骨骼命名：

| MediaPipe关键点 | Blender骨骼（常见命名） |
|----------------|--------------------------------|
| left_shoulder (11) | LeftShoulder |
| right_shoulder (12) | RightShoulder |
| left_elbow (13) | LeftArm |
| right_elbow (14) | RightArm |
| left_wrist (15) | LeftForeArm |
| right_wrist (16) | RightForeArm |
| left_hip (23) | LeftUpLeg |
| right_hip (24) | RightUpLeg |
| left_knee (25) | LeftLeg |
| right_knee (26) | RightLeg |
| left_ankle (27) | LeftFoot |
| right_ankle (28) | RightFoot |

### 自定义骨骼映射

如果你的角色使用不同的骨骼命名，需要修改 `mediapipe_pose_extractor.py` 中的 `LANDMARK_TO_BONE` 字典：

```python
LANDMARK_TO_BONE = {
    11: 'YourLeftShoulderBone',
    12: 'YourRightShoulderBone',
    # ... 其他映射
}
```

---

## ⚠️ 已知限制

### 1. 旋转精度

当前版本使用**简化算法**将MediaPipe关键点转换为骨骼旋转。这可能会导致：
- 某些关节旋转不自然
- 需要手动调整动画曲线

**解决方案**：使用Blender的IK解算器或专业重定向插件（如Auto-Rig Pro）。

### 2. 手指追踪

MediaPipe的姿势模型**不包含手指关键点**。如果你需要手指动画：
- 使用MediaPipe的Hands模型（需要修改代码）
- 手动制作手指动画
- 使用其他支持手指追踪的工具

### 3. 面部表情

本插件**不支持面部表情捕捉**。如果需要：
- 使用MediaPipe的Face Mesh模型
- 使用专业的面部捕捉工具（如FaceCap）

---

## 🔧 高级功能

### 命令行使用

你也可以直接在命令行中使用 `mediapipe_pose_extractor.py`：

```bash
python mediapipe_pose_extractor.py \
    --input path/to/video.mp4 \
    --output pose_data.json \
    --output_script apply_animation.py \
    --model_complexity 2
```

然后在Blender的Scripting工作区中运行生成的 `apply_animation.py` 脚本。

### 批量处理

如果需要处理多个视频，可以创建批处理脚本：

```bash
#!/bin/bash
for video in videos/*.mp4; do
    python mediapipe_pose_extractor.py \
        --input "$video" \
        --output "output/$(basename $video .mp4).json"
done
```

---

## 🐛 常见问题排查

### 问题1：MediaPipe安装失败

**症状**：点击 `安装MediaPipe` 后报错

**解决**：
1. 检查Python版本（MediaPipe支持Python 3.9-3.11）
2. 尝试手动安装：`pip install mediapipe`
3. 如果使用Blender内置Python，确保其已更新

### 问题2：视频处理失败

**症状**：点击 `提取姿态` 后无反应或报错

**解决**：
1. 检查视频文件路径是否包含中文或特殊字符（建议改用英文路径）
2. 检查视频格式是否受支持（尝试转换为MP4）
3. 查看Blender系统控制台获取详细错误信息

### 问题3：动画应用后角色扭曲

**症状**：角色肢体出现异常旋转或位置

**解决**：
1. 确保角色处于**T-Pose**或**A-Pose**状态
2. 检查角色的骨骼命名是否与映射表匹配
3. 调整 `缩放因子` 参数
4. 手动编辑生成的关键帧

### 问题4：处理速度太慢

**症状**：视频处理耗时过长

**解决**：
1. 降低 `模型复杂度` 到0或1
2. 增大 `帧采样率`（例如设置为2或3）
3. 降低视频分辨率（例如转换为720p）
4. 使用GPU加速（需要CUDA版本的MediaPipe）

---

## 📚 进一步学习

### MediaPipe官方文档
- 姿势检测：https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- Python API：https://developers.google.com/mediapipe/api/solutions/python

### Blender Python API
- 动画系统：https://docs.blender.org/api/current/bpy.types.Action.html
- 骨骼操作：https://docs.blender.org/api/current/bpy.types.PoseBone.html

### 动作捕捉技巧
- 角色绑定基础：https://www.blender.org/manual/animation/armatures/
- IK/FK切换：https://www.youtube.com/watch?v=BVqX2oFpZfU

---

## 🎉 完成！

现在你应该可以：
1. ✅ 安装并使用本插件
2. ✅ 从视频中提取人体姿态
3. ✅ 将姿态数据应用到Blender角色
4. ✅ 调整参数以获得最佳效果

如果你遇到任何问题或有改进建议，欢迎反馈！

---

## 📄 文件清单

本插件包含以下文件：

1. **mediapipe_motion_capture.py** - Blender插件主文件
2. **mediapipe_pose_extractor.py** - MediaPipe姿态提取脚本
3. **README_MediaPipe.md** - 本使用指南

---

**祝你使用愉快！** 🎊
