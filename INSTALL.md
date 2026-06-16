# 安装和配置指南

## 快速开始

### 自动化安装（Linux/Mac）

```bash
bash install.sh
```

### 手动安装（所有平台）

#### 1. 安装GVHMR

```bash
# 克隆仓库
git clone https://github.com/zju3dv/GVHMR.git
cd GVHMR

# 创建虚拟环境
python -m venv gvhmr_env
source gvhmr_env/bin/activate  # Linux/Mac
# 或
gvhmr_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 下载预训练模型
bash scripts/download_checkpoints.sh
```

详细安装说明：https://github.com/zju3dv/GVHMR/blob/main/docs/INSTALL.md

#### 2. 安装Blender插件

1. 打开Blender
2. 进入 `编辑(Edit)` -> `偏好设置(Preferences)` -> `插件(Add-ons)`
3. 点击 `安装(Install...)` 按钮
4. 选择 `video_motion_retarget.py` 文件
5. 启用插件（勾选复选框）

#### 3. 配置插件

在Blender右侧面板找到 `Motion Retarget` 标签页，填写：

- **GVHMR路径**：GVHMR项目目录（例如：`C:\GVHMR`）
- **Python路径**：GVHMR虚拟环境中的Python解释器（例如：`C:\GVHMR\gvhmr_env\Scripts\python.exe`）

## 使用示例

### 示例1：基本使用

1. **准备视频**：准备一个包含清晰人物的视频（建议MP4，1080p，30fps）
2. **打开插件**：在Blender中打开 `Motion Retarget` 面板
3. **选择视频**：点击 `浏览` 选择视频文件
4. **处理视频**：点击 `处理视频` 按钮
5. **等待完成**：处理时间取决于视频长度和硬件配置
6. **应用动画**：选择场景中的角色，点击 `应用动画`

### 示例2：命令行使用

如果你更喜欢命令行操作：

```bash
# 1. 使用GVHMR处理视频
cd GVHMR
python tools/demo/demo.py --video=/path/to/video.mp4 --output_root=/output/path -s

# 2. 转换为Blender脚本
python apply_gvhmr_to_blender.py \
    --input /output/path/video_hmr4d.pt \
    --output_script apply_anim.py \
    --armature_name Armature

# 3. 在Blender中运行脚本
# 打开Blender -> Scripting工作区 -> 打开 apply_anim.py -> 运行脚本
```

## 测试数据

为了快速测试，你可以使用GVHMR项目提供的示例视频：

```bash
# 示例视频位置（GVHMR项目中）
GVHMR/docs/example_video/tennis.mp4
```

## 常见问题排查

### 问题1：插件找不到GVHMR

**症状**：点击 `处理视频` 后报错 "请先设置GVHMR路径"

**解决**：
1. 确认GVHMR已正确安装
2. 在插件设置中填写正确的GVHMR路径
3. 确认路径不包含中文或特殊字符

### 问题2：Python依赖错误

**症状**：处理视频时报错 "ModuleNotFoundError: No module named 'torch'"

**解决**：
1. 确认已安装GVHMR的所有依赖
2. 在插件设置中填写正确的Python路径（指向包含依赖的虚拟环境）

### 问题3：视频处理失败

**症状**：处理进程启动后立即失败

**解决**：
1. 检查视频文件格式（建议使用MP4）
2. 检查视频文件路径是否包含中文（建议改用英文路径）
3. 查看Blender系统控制台获取详细错误信息（Window -> Toggle System Console）

### 问题4：动画应用后角色扭曲

**症状**：应用动画后，角色肢体出现异常扭曲

**解决**：
1. 确认角色的骨骼命名与SMPL标准一致（参见 `SMPL_TO_BLENDER` 字典）
2. 确保角色处于TPose状态
3. 调整角色缩放以匹配SMPL尺寸（约1.7米高）
4. 检查骨骼朝向是否正确

## 高级配置

### 自定义骨骼映射

如果你的角色使用不同的骨骼命名，需要修改映射字典：

编辑 `apply_gvhmr_to_blender.py`，修改 `SMPL_TO_BLENDER` 字典：

```python
SMPL_TO_BLENDER = {
    'Pelvis': 'YourHipsBoneName',
    'L_Hip': 'YourLeftUpLegName',
    # ... 其他映射
}
```

### 坐标系统转换

SMPL使用Y轴向上的坐标系，Blender使用Z轴向上。转换公式在 `apply_gvhmr_to_blender.py` 中：

```python
# SMPL到Blender坐标转换
blender_t = [smpl_x, -smpl_z, smpl_y]  # X, -Z, Y
```

如果你的角色使用不同的坐标系，需要调整这个公式。

### 帧率设置

默认帧率为30fps。如果你的视频使用不同的帧率，需要修改：

1. GVHMR处理时：`demo.py` 会自动将视频转换为30fps
2. Blender中：在输出设置中调整帧率

## 性能优化

### 降低处理分辨率

如果视频处理太慢，可以降低输入分辨率：

```bash
# 在运行GVHMR之前，先压缩视频
ffmpeg -i input.mp4 -vf scale=640:360 compressed.mp4
```

### 使用GPU加速

GVHMR支持GPU加速（需要CUDA）：

```bash
# 确保安装了CUDA版本的PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 下一步

- 阅读 `README.md` 了解完整功能
- 查看 `apply_gvhmr_to_blender.py` 源码了解数据转换细节
- 尝试处理自己的视频数据
- 根据需要调整骨骼映射和坐标转换

## 获取帮助

- GVHMR Issues: https://github.com/zju3dv/GVHMR/issues
- HaMeR项目: https://github.com/geopavlakos/hamer
- Blender Python API文档: https://docs.blender.org/api/current/

## 更新日志

- **2026-06-16**: 初始版本，基础功能实现
