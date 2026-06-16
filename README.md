# Blender MediaPipe Motion Capture

完全本地运行的 Blender 动作捕捉插件，无需任何外部 API 调用。

## ✨ 功能特点

- 🎬 **视频驱动**：上传视频，角色自动跟随动作
- 🏠 **完全本地**：使用 MediaPipe，无需联网，无需 API Key
- 🦴 **骨骼匹配**：自动识别 Mixamo / 标准骨骼命名
- 🔧 **旋转驱动**：v4.0 使用旋转角度驱动骨骼（更自然）
- 📦 **易安装**：仅需 `pip install mediapipe`

## 📦 安装步骤

### 1. 安装 MediaPipe

```bash
pip install mediapipe opencv-python numpy
```

### 2. 安装 Blender 插件

1. 下载 `mediapipe_motion_capture.py`
2. 打开 Blender → **编辑 → 偏好设置 → 插件**
3. 点 **Install...** → 选择 `mediapipe_motion_capture.py`
4. 勾选启用 **MediaPipe Motion Capture (Local)**

### 3. 配置路径

在右侧面板 **Motion Capture** 标签中：
- **Python Path**：指向你的 Python（如 `D:\GVHMR\gvhmr_env\Scripts\python.exe`）
- **Video File**：选择你的视频文件
- **Scale Factor**：建议 `5.0 ~ 10.0`

## 🚀 使用方法

1. 在 Blender 中导入一个带骨骼的角色（Mixamo 模型最佳）
2. 选中角色骨骼
3. 在面板中选择视频文件
4. 点击 **Extract Pose**
5. 等待处理完成，动画自动应用到角色！
6. 按 **空格键** 播放动画 🎉

## 📋 文件说明

| 文件 | 说明 |
|------|------|
| `mediapipe_motion_capture.py` | Blender 插件主文件（推荐使用） |
| `simple_mediapipe_tool.py` | 命令行版本，更灵活 |
| `mediapipe_pose_extractor.py` | MediaPipe 姿态提取器 |
| `README_MediaPipe.md` | 详细文档 |
| `QUICKSTART.md` | 快速入门指南 |

## 💡 常见问题

**Q：角色没有动？**
- 检查骨骼命名是否为标准名称（Hips, LeftArm 等）或 Mixamo 格式（mixamorig:Hips）
- 尝试调大 **Scale Factor** 到 5.0 或 10.0

**Q：MediaPipe 安装失败？**
- 确保 Python 版本 ≤ 3.12（MediaPipe 暂不支持 3.13）
- 使用提供的 GVHMR 虚拟环境：`D:\新建文件夹\GVHMR\gvhmr_env\Scripts\python.exe`

**Q：动作不匹配？**
- v4.0 使用旋转驱动，如果仍有问题请提交 Issue

## 🔗 参考项目

- [GVHMR](https://github.com/zju3dv/GVHMR) - 3D 人体姿态恢复
- [HaMeR](https://github.com/geopavlakos/hamer) - 手部姿态估计
- [MediaPipe](https://developers.google.com/mediapipe) - Google 开源姿态检测

## 📄 许可

MIT License

---

⭐ 如果这个项目对你有帮助，欢迎 Star！
