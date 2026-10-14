# Face Follower Robot

This folder contains ESP32-CAM experiments for live camera streaming and a face-following / vision-based robot concept. The codebase is experimental and includes multiple versions of attempts and revisions.

## Project purpose

The main idea is to use an ESP32-CAM module to:
- stream a live camera feed
- detect or track a face
- send movement/position decisions to a robot or motion system

The project evolved through several iterations, with different notebook-based client experiments and camera firmware approaches.

## Folder structure

- `test.cpp` — low-latency ESP32-CAM stream server example using Wi-Fi and the camera module
- `V1/` — early face follower implementation and related files
- `V2 new/` — newer client-side experiments, including MediaPipe-based work
- `V3/` — later experimental versions and refinements

## Main example

The `test.cpp` file is a useful starting point for camera initialization and streaming. It sets up:
- ESP32-CAM pin assignments
- JPEG capture configuration
- Wi-Fi connection
- a simple HTTP multipart stream so the camera can be viewed in a browser

## Important notes

- This folder is not a single final production project; it contains multiple experimental stages.
- Wi-Fi credentials in the sample code may need to be changed for your own network.
- The face-detection and robot-control logic depends on additional client-side processing and hardware integration.
- Some notebook files are intended for experimental or educational development rather than a final product build.

## Suggested workflow

1. Review the camera stream example in `test.cpp`.
2. Open the versioned folders (`V1`, `V2 new`, `V3`) to compare approaches.
3. Use the notebook files as references for client-side face tracking logic.
4. Adapt the code to your specific robot hardware and Wi-Fi setup.

## Typical use case

This project is best used as a research and prototyping workspace for:
- camera streaming from ESP32-CAM
- face tracking with computer vision libraries
- development of a follow-me robot concept

## Related project

The more polished and fully documented project in this workspace is the main [ERINX Smart Hub/README.md](../ERINX%20Smart%20Hub/README.md) project, which focuses on an ESP32-S3 smart display and media UI system.
