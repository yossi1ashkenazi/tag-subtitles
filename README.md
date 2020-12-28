# Run Program Instructions:
## Using Executable File:
1. Clone just `build` directory from this repository to your own machine.
2. Look for `Tagging Tool.exe` file in the cloned folder and run it.
3. Now, you need to choose a video from your machine. Read the next section for more information of the media player.
4. Record and tag as much words as you want. If you regret and want to delete a record you made, just delete at least one of the relevant row's cell from the table.
5. Press on the finish button and let the program work.
6. When it will finish, you will see an alert. Once pressing 'OK' in that alert, the program will shut down.
7. Look at your cloned directory now, you should see a new folder called `tagged data`.
8. In `tagged data` you will see the labels you tagged. Each word you capture is now separated to two files with the same name (a random name) but with different filename extension:
    - A `.wav` audio file that contains the audio of the word you captured.
    - A `.avi` video file that contains speaker's lips extracted from the original video, saying the word you captured.
9. You can run this program over and over on your machine, in case of capturing a word you have captured already - the new `.wav ` and `.avi` files will be added to the relevant directory under `tagged data`, with their own generated name.
10. **HAVE A FUN DATA TAGGING!**

## Using Source Code:
1. Clone this repository to your own machine.
2. Open cmd or powershell, admin permissions are not necessary.
3. Run `python main.py`. You may need to install some packages, use `PyPI` tool for that.
    - You can find needed libraries and their versions in `requirements.txt` file.
4. Now, you need to choose a video from your machine. Read the next section for more information of the media player.
5. Record and tag as much words as you want. If you regret and want to delete a record you made, just delete at least one of the relevant row's cell from the table.
6. Press on the finish button and let the program work.
7. When it will finish, you will see an alert. Once pressing 'OK' in that alert, the program will shut down.
8. Look at your cloned directory now, you should see a new folder called `tagged data`.
9. In `tagged data` you will see the labels you tagged. Each word you capture is now separated to two files with the same name (a random name) but with different filename extension:
    - A `.wav` audio file that contains the audio of the word you captured.
    - A `.avi` video file that contains speaker's lips extracted from the original video, saying the word you captured.
10. You can run this program over and over on your machine, in case of capturing a word you have captured already - the new `.wav ` and `.avi` files will be added to the relevant directory under `tagged data`, with their own generated name.
11. **HAVE A FUN DATA TAGGING!**

# Media Player Instructions:
This player supports `AVI` format out of the box.
In order to support other formats, please run the `K-Lite_Codec_Pack_1590_Basic.exe` file from `extras` directory.
This add-on will make the media player support many other formats - `mp4, MPEG, M2TS, etc.`
For more detalis of that add-on, please visit `https://www.codecguide.com/download_kl.htm`