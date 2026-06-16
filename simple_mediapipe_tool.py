#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaPipe视频动作捕捉 - 简化版工具
完全本地运行，无需API
"""

import argparse
import json
import os
import sys
import cv2
import mediapipe as mp
import numpy as np


def extract_pose_to_json(video_path, output_json):
    print(f"[INFO] Processing: {video_path}")

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        model_complexity=2,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return None

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"[INFO] Video: {fps} FPS, {total_frames} frames")

    all_frames = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            landmarks = []
            for idx, lm in enumerate(results.pose_landmarks.landmark):
                landmarks.append({
                    'idx': idx,
                    'x': round(float(lm.x), 6),
                    'y': round(float(lm.y), 6),
                    'z': round(float(lm.z), 6),
                    'visibility': round(float(lm.visibility), 4)
                })
            all_frames.append({'frame': frame_idx, 'landmarks': landmarks})

        if frame_idx % 30 == 0:
            print(f"  ... {frame_idx}/{total_frames}")
        frame_idx += 1

    cap.release()
    pose.close()

    output_data = {
        'fps': fps,
        'total_frames': frame_idx,
        'frames': all_frames
    }

    os.makedirs(os.path.dirname(output_json) or '.', exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"[DONE] {len(all_frames)} frames saved to {output_json}")
    return output_data


def main():
    parser = argparse.ArgumentParser(description='MediaPipe Motion Capture')
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output_json', type=str, default='pose_data.json')
    args = parser.parse_args()

    extract_pose_to_json(args.input, args.output_json)


if __name__ == '__main__':
    main()
