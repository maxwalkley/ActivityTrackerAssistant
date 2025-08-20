import pandas as pd
import extractionFunctions
import streamlit as st
import re
from datetime import datetime

# === STREAMLIT INTERFACE ===

# Setup
st.set_page_config(layout="wide")

# Set screen state
if "screen" not in st.session_state:
    st.session_state.screen = "collectData"

import datetime

# Screen: Data Collection
if st.session_state.screen == "collectData":
    st.title("Rotation Information")

    # Load previous values if available
    uploadedFile = st.file_uploader("Upload Excel File", type=["xlsx"])
    
    letters = ["A", "B", "C", "D"] 
    numbers = list(range(1, 7))          

    # Try to parse existing preset like "C1"
    preset = str(st.session_state.get("rotation", ""))
    m = re.match(r"^([A-D])([1-6])$", preset)

    defaultLetter = m.group(1) if (m and m.group(1) in letters) else "C"
    defaultNumber = int(m.group(2)) if m else 1

    col1, col2 = st.columns(2)
    with col1:
        letter = st.selectbox("Block", letters, index=letters.index(defaultLetter), key="rotationLetter")
    with col2:
        number = st.selectbox("Number", numbers, index=numbers.index(defaultNumber), key="rotationNumber")

    rotation = f"{letter}{number}"
    st.session_state["rotation"] = rotation
    
    location = st.selectbox(
        "Location Name",
        options=["SMH", "VGH", "SPH"],
        index=["SMH", "VGH", "SPH"].index(st.session_state.get("location", "VGH")) 
            if st.session_state.get("location") in ["SMH", "VGH", "SPH"] else 1
    )
    startDate = st.date_input("Start Date", value=st.session_state.get("startDate", datetime.date.today()))
    endDate = st.date_input("End Date", value=st.session_state.get("endDate", datetime.date.today()))
    
    # Dynamic Academic Year Finder
    # Get current year
    currentYear = datetime.datetime.now().year

    # Get preset value or default to current year as start of academic year
    preset = st.session_state.get("academicYear", f"{currentYear}-{currentYear+1}")

    # Parse start year from preset (left side of the dash)
    try:
        presetStart = int(preset.split("-")[0])
    except:
        presetStart = currentYear

    # Build range: previous 5 years up to 1 future year
    options = [f"{y}-{y+1}" for y in range(presetStart-2, presetStart+2)]

    # Create dropdown
    academicYear = st.selectbox(
        "Academic Year",
        options=options,
        index=options.index(preset) if preset in options else len(options)-2
    )

    # Continue to Editing on button press
    if st.button("Continue", key="continue"):
        if not uploadedFile or not rotation:
            st.warning("Please fill out all required fields.")
        else:
            try:
                outputFile = extractionFunctions.fileExtractor(uploadedFile)
                st.session_state.outputFile = outputFile

                # Save form data for future reuse
                st.session_state.uploadedFile = uploadedFile
                st.session_state.rotation = rotation
                st.session_state.location = location
                st.session_state.startDate = startDate
                st.session_state.endDate = endDate
                st.session_state.academicYear = academicYear

                st.session_state.screen = "edit"
                st.rerun()

            except Exception as e:
                st.error("Could not load or process the uploaded file.")
                st.exception(e)


    

# Screen: Edit Data
if st.session_state.screen == "edit":
    st.title("Sanitized Data Editor")

    if 'outputFile' not in st.session_state:
        st.error("Output file not found. Please return to the previous screen and re-load the file.")
        st.session_state.screen = "collectData"
        st.rerun()

    outputFile = st.session_state.outputFile.copy()

    st.subheader("Insert Rows")

    insertAt = st.number_input(
        "Insert new row at index:",
        min_value=0,
        max_value=len(outputFile) + 1,
        value=0
    )
    endline = 100 
    numRowsToInsert = st.number_input(
        "Number of rows to insert:",
        min_value=1,
        max_value=endline,
        value=1
    )

    # Insert empty rows on button press for ease of editing
    if st.button("Insert Empty Rows"):
        newRows = pd.DataFrame(
            [[""] * len(outputFile.columns)] * numRowsToInsert,
            columns=outputFile.columns
        )
        outputFile = pd.concat([
            outputFile.iloc[:insertAt],
            newRows,
            outputFile.iloc[insertAt:]
        ], ignore_index=True)

        st.session_state.outputFile = outputFile.copy()
        st.success(f"Inserted {numRowsToInsert} row(s) at index {insertAt}.")

    # Display with clean rown numbers using index
    outputFile_display = outputFile.reset_index(drop=True)

    if "# Students" in outputFile_display.columns:
        outputFile_display["# Students"] = outputFile_display["# Students"].astype(str)

    windowHeight = 800
    editedDataFile = extractionFunctions.renderFullHeightDataframe(outputFile_display)

    colSpacers = [0.13, 0.18, 0.15, 0.15, 1.75]
    
    col1, col2, col3, col4, _ = st.columns(colSpacers)

    with col1:
        # Move to TTPS screen on button press
        if st.button("TTPS", key="editTTP"):
            
            # Save latest edits to session state
            st.session_state.outputFile = editedDataFile.copy()
    
            editedDataFile = extractionFunctions.cleanEditedData(editedDataFile)
            processedData = extractionFunctions.dataTTPS(editedDataFile, 
                                                         st.session_state.get("startDate", ""), 
                                                         st.session_state.get("endDate", ""), 
                                                         st.session_state.get("location", ""), 
                                                         st.session_state.get("rotation", ""))
            st.session_state.ttpsData = processedData.copy()
            st.session_state.screen = "ttps"
            st.rerun()

    with col2:
        # Move to Tracker screen on button press
        if st.button("TRACKER", key="editTracker"):
            
            # Save latest edits to session state
            st.session_state.outputFile = editedDataFile.copy()
            
            editedDataFile = extractionFunctions.cleanEditedData(editedDataFile)
            processedData = extractionFunctions.dataTracker(editedDataFile, 
                                                            st.session_state.get("academicYear", ""), 
                                                            st.session_state.get("rotation", ""), 
                                                            st.session_state.get("location", ""))
            st.session_state.trackerData = processedData.copy()
            st.session_state.screen = "tracker"
            st.rerun()

    with col3:
        # Move to One45 screen on button press
        if st.button("ONE45", key="editOne45"):
            
            # Save latest edits to session state
            st.session_state.outputFile = editedDataFile.copy()
            
            editedDataFile = extractionFunctions.cleanEditedData(editedDataFile)
            processedData = extractionFunctions.dataOne45(editedDataFile)
            st.session_state.one45Data = processedData.copy()
            st.session_state.screen = "one45"
            st.rerun()

    with col4:
        # Return to Data Collection screen on button press
        if st.button("Return", key="editReturn"):
            editedDataFile = extractionFunctions.cleanEditedData(editedDataFile)
            st.session_state.cleanedData = editedDataFile.copy()
            st.session_state.screen = "collectData"
            st.rerun()

        
# Screen: TTPS output
if st.session_state.screen == "ttps":
    st.title("TTPS Data")
    st.text("All entries marked as \"* Cannot Input into TTP *\" are not shown, all other entries are shown")
    
    # Cast problematic column to string before display
    ttpsDisplay = st.session_state.ttpsData.copy()
    if "# Students" in ttpsDisplay.columns:
        ttpsDisplay["# Students"] = ttpsDisplay["# Students"].astype(str)
        
    extractionFunctions.renderFullHeightDataframeNonEditable(ttpsDisplay)
        
    # Return to Editing on button press
    if st.button("Return", key="editReturnTTPS"):
        st.session_state.screen = "edit"
        st.rerun()
        
# Screen: Internal Tracker output
if st.session_state.screen == "tracker":
    st.title("Internal Tracker Data")
    
    # Cast problematic column to string before display
    trackerDisplay = st.session_state.trackerData.copy()
    if "# Students" in trackerDisplay.columns:
        trackerDisplay["# Students"] = trackerDisplay["# Students"].astype(str)
        
    extractionFunctions.renderFullHeightDataframeNonEditable(trackerDisplay)
    
    # Return to Editing on button press
    if st.button("Return", key="editReturnTracker"):
        st.session_state.screen = "edit"
        st.rerun()


# Screen: One45 output
if st.session_state.screen == "one45":
    st.title("One45 Data")
    
    # Cast problematic column to string before display
    one45Display = st.session_state.one45Data.copy()
    if "# Students" in one45Display.columns:
        one45Display["# Students"] = one45Display["# Students"].astype(str)
        
    extractionFunctions.renderFullHeightDataframeNonEditable(one45Display)
        
    # Return to Editing on button press
    if st.button("Return", key="editReturnOne45"):
        st.session_state.screen = "edit"
        st.rerun()




