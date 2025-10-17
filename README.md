# tidy-eqcm
GUI to easily clean up EQCM data. Still a work-in-progress, but should be functional. With this program, you can:
- Align the CV and EQCM timestamps
- Instantly map the EQCM frequency to the CV potential
- Apply a Savitzky-Golay filter
- Remove the background drift on the EQCM with a polynomial fit

## Requirements
I tested the script on python 3.13.5; if there's any sudden errors, please try running it on that version first. There also seems to be a bug when running it via anaconda/spyder, so download python from python.org. You need to install the following packages, using e.g. pip:
- pandas
- numpy
- scipy
- matplotlib
- pyjanitor
- pyqt6

```pip install pandas numpy scipy matplotlib pyjanitor pyqt6```

Afterwards, clone this repository and run main.py. Please let me know if you had to install any other packages.

## How to use
### Loading files
The CV data file needs to be an EC-lab .mpr file exported as .txt, with at least the following columns:
- time/s **in absolute time**
- Ewe/V
- \<I\>/mA
- cycle number

For the EQCM data, you can use the EQCM-Leiden script. The .csv file needs at least the following columns:
- Timestamp
- Frequency

### Exported files
The script exports two .csv files. The CV file contains (at least)
- timestamp_s
- potential_V
- current_mA
- cycle_number

and the EQCM file contains (at least)
 - timestamp_s
 - potential_V
 - frequency_Hz
 - frequency_savgol_Hz (noise filter applied)
 - cycle_number

### Keybinds
- Click on the top-left plot to select a cycle
- 1-5: Zoom into one of the plots (1-4), or go back to the overview (5)

- H, L: Shift the EQCM timestamp

- N: Toggle the savgol filter
- A, D: Change the savgol window length
- W, S: Change the savgol order

- B: Toggle the background fit
- C, V: Change the order of the polynomial fit
- X: Apply the fit to the frequency

- U: undo all changes
- Q: quit the program

## Planned
Right now, the script only exports the cycle that you selected, making it very easy to plot the cleaned data. I am planning on changing this so the entire cleaned data gets exported, since you may want that data too.

- Export entire measurement
- Highlight which of the points are used for the polynomial fit
- Easy way to select/exclude points for the fit
- Different fits (sigmoidal curve)
- Add an indicator when the savgol filter or fit is bad (numpy/scipy warns you)
- Add tests to ensure the program functions as intended
- Show the keybindings in a separate window
- Switch between cycles on keybind

If you have other suggestions that would make the analysis easier/more user-friendly, let me know!

## Changing the code
If you're planning on changing the code, I highly recommend using a static type checker (pyright, mypy) to avoid breaking anything.
