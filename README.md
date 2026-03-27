# sEMG Manus Manager

sEMG Manus Manager is a graphical application made to record, manage and analyse data from the Manus gloves and Thalmic Labs Myo sEMG devices.

This application is also the recording/inspection companion for the published sEMG-MANUS dataset: synchronised Myo sEMG and MANUS finger-joint recordings for hand pose estimation and XR musical interaction.

## Related Dataset

- Zenodo dataset DOI: [`10.5281/zenodo.19261324`](https://doi.org/10.5281/zenodo.19261324)
- Zenodo record: [`zenodo.org/records/19261324`](https://zenodo.org/records/19261324)
- Dataset companion repository: [`maxgraf96/sEMG-manus-dataset`](https://github.com/maxgraf96/sEMG-manus-dataset)
- Published release scope: 18 participant folders, 22 gestures, 3108 CSV recordings after cleanup
- Recommended benchmark cohort: 15 participants (`u_3` to `u_16` and `u_18`)
- Incomplete participants to exclude from balanced between-user analyses unless partial-data handling is intentional: `u_1`, `u_2`, `u_17`
- Per-recording CSV schema: 42 columns comprising 8 Myo sEMG channels, 10 Myo IMU channels, 20 MANUS finger-joint channels, and 4 wrist quaternion channels

## Features

- User & Session Management: Create and manage users, view and manage their recording sessions.
- Recordings List: View a list of recordings for a selected session.
- Open Recordings: Open individual recordings for analysis using external tools.
- Start New Recordings: Start new recordings and save them to user's session folder.

## Screenshot

![screen.png](resources%2Fscreen.png)

## Requirements

- Python 3.11
- Windows for the full desktop workflow
- Node.js only if you want to run the hand visualiser

## Dependency Notes

- `requirements.txt` now lists the direct runtime dependencies instead of a fully pinned transitive export.
- `cefpython3` is not included for Python 3.11. The latest PyPI release is too old for a Python 3.11 install, so the embedded browser-based visualiser is disabled gracefully in that environment.
- The codebase is still Windows-first. It contains Windows-specific process launching and file-opening paths.
- User/session data no longer has to live inside this repository. The app reads `USER_DATA_DIR` from a local `.env` file.

## Platform Support

- Windows is required for the full experience, including data collection with the MANUS dataglove stack. The MANUS software workflow is optimized for Windows, and this app also contains Windows-specific integrations around recording and external process management.
- macOS is useful as an inspection environment. You can use this app there to browse sessions, inspect recordings, and run analysis-oriented parts of the tool, but not the full hardware-driven workflow.

## Installation

1. Clone this repository to your local machine.
2. Open a terminal and navigate to the cloned directory.
3. Copy `.env.example` to `.env`.
4. Set `USER_DATA_DIR` in `.env` to the folder where you want user/session data to live. This can be outside the repository.
5. Create and activate a Python 3.11 virtual environment.
6. Run `pip install -r requirements.txt` to install the required dependencies.
7. Run `python main.py` to start the application.

## Usage

- Create a new user: Click the "Add New User" button in the sidebar and enter the user's name.
- Select a user: Click on the user's name in the sidebar to see their sessions.
- View session details: Each session will display a list of recorded data files.
- Open a recording: Double-click on a recording file to open it with an external program.
- Start a new recording: Click the "Start New Recording" button for the selected session.
- Switch themes: Click the "Light/Dark" button in the status bar to change the theme.

## Contributing

This project is open-source and welcomes contributions. Feel free to fork the repository and submit pull requests with your improvements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Disclaimer

This application is provided as-is with no warranty or support. Use it at your own risk.

## Contact

Feel free to open issues or contact me directly for any questions or feedback.
