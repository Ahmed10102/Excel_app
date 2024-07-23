import streamlit as st
import pandas as pd
from PIL import Image
import pyvista as pv
import tempfile
import os
from stpyvista import stpyvista
from openpyxl import load_workbook

# Loading Image using PIL
im = Image.open('logo.png')
# Adding Image to web app
st.set_page_config(page_title="3D printing Manager", page_icon=im, layout='wide')

# Function to load STL file using PyVista
@st.cache_resource
def load_stl(file, color):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as temp_file:
        temp_file.write(file.read())
        temp_file_path = temp_file.name

    # Load and plot STL file using PyVista and Streamlit
    stl_mesh = pv.read(temp_file_path)
    
    # Check if the mesh is empty
    if stl_mesh.n_points == 0:
        return None  # Return None to indicate an error
    
    plotter = pv.Plotter(window_size=[800, 800])
    plotter.add_mesh(stl_mesh, color=color)
    plotter.view_isometric()
    plotter.background_color = 'white'
    return plotter

# Load data from local Excel file
excel_file = "3Dprinting.xlsx"
printer_sheet = "Printers"
database_sheet = "Database"

# Function to load data from Excel
@st.cache_data
def load_data(file, sheet):
    return pd.read_excel(file, sheet_name=sheet)

# Load printer data (assuming cached for efficiency)
printer_data = load_data(excel_file, printer_sheet)

# Filter printers based on status
available_printers = printer_data[printer_data['State'].isin(['Available', 'Busy'])]

# Streamlit UI
col1, col2 = st.columns([1, 2])  # Adjust column widths as needed

with col1:
    # Load Actia.png
    actia_image = Image.open("Actia.png")
    st.image(actia_image, width=100)  # Adjust width as needed

with col2:
    st.title("Liste d'attente d'impression 3D")

# Initialize session state for file, color, column visibility, and submission counter
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'color' not in st.session_state:
    st.session_state.color = "Quelconque"
if 'show_column2' not in st.session_state:
    st.session_state.show_column2 = True
if 'submission_counter' not in st.session_state:
    st.session_state.submission_counter = 1
if 'first_value' not in st.session_state:
    st.session_state.first_value = True

# Divide page into two columns
col1, col2 = st.columns(2)

# Column 1: Form inputs
with col1:
    # Create a container for the form elements
    form_container = st.container()
    with form_container:
        name = st.text_input("Name")
        requester = st.selectbox("Demandeur", ["INNOVATION", "STARTUPS"])
        uploaded_file = st.file_uploader("Importer un fichier STL", type=["stl"])
        printer_selection = st.selectbox("Imprimantes", available_printers['Printer'].tolist())

        # Display availability tag
        for printer, state in zip(available_printers['Printer'], available_printers['State']):
            if printer == printer_selection:
                if state == "Available":
                    st.success(f"{printer} is {state}")
                elif state == "Busy":
                    st.warning(f"{printer} is {state}")
                else:
                    st.error(f"{printer} is {state}")
                    
        if printer_selection=="Resine":
            material = st.selectbox("Matériaux", ["RESINE"])
        else:
            material = st.selectbox("Matériaux", ["PLA", "ABS", "PETG"])
        color = st.selectbox("Couleurs", ["Quelconque", "Noir", "Rouge", "Bleu", "Vert"])
        estimated_time = st.number_input("Temps éstimé (en minutes)", step=10)
        note = st.text_area("Note")

        # Use a container to group the buttons
        button_container = st.container()
        with button_container:
            b1, b2, b3, b4, b5, b6, b7 = st.columns([1, 2, 1, 1, 1, 1, 1])
            with b1:
                if st.button("Envoyer"):
                    if name and requester and uploaded_file and printer_selection and material and color and estimated_time:
                        # Load existing database sheet
                        database_data = load_data(excel_file, database_sheet)

                        # Check if 'SubmissionNumber' column exists
                        if 'SubmissionNumber' in database_data.columns:
                            next_submission_number = database_data['SubmissionNumber'].max() + st.session_state.submission_counter if not database_data.empty else 1
                        else:
                            next_submission_number = 1

                        # Increment the submission counter
                        st.session_state.submission_counter += 1

                        # Create a new record with submission number
                        new_record = {
                            "SubmissionNumber": next_submission_number,
                            "Name": name,
                            "Requester": requester,
                            "Printer": printer_selection,
                            "Material": material,
                            "Color": color,
                            "Note": note,
                            "FileName": uploaded_file.name if uploaded_file else None,
                            "State": "Waitlist",
                            "Estimated Time": estimated_time
                        }

                        # Save the uploaded STL file to the "files" folder with the submission number
                        os.makedirs("files", exist_ok=True)  # Create the "files" folder if it doesn't exist
                        file_path = os.path.join("files", f"submission_{next_submission_number}.stl")
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.read())

                        # Save the updated database back to the Excel file
                        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                            if 'SubmissionNumber' in database_data.columns or not(st.session_state.first_value):
                                pd.DataFrame([new_record]).to_excel(writer, sheet_name=database_sheet, index=False, header=False, startrow=(database_data['SubmissionNumber'].max() + st.session_state.submission_counter - 1))
                            else:
                                if st.session_state.first_value:
                                    st.session_state.first_value = False
                                    pd.DataFrame([new_record]).to_excel(writer, sheet_name=database_sheet, index=False, header=True)
                                    st.session_state.submission_counter += 1
                        # Display the table in the second column
                        database_data = pd.read_excel(excel_file, sheet_name=database_sheet)
                        database_data['Total Time'] = database_data[(database_data['State'] == 'Waitlist' )& (database_data['Printer'] == printer_selection) & (database_data['SubmissionNumber']<next_submission_number )].groupby('Printer')['Estimated Time'].transform('sum') + database_data['Estimated Time']

                        with col2:
                            st.table(database_data)
                    else:
                        with col2:
                            database_data = pd.read_excel(excel_file, sheet_name=database_sheet)
                            database_data['Total Time'] = database_data[(database_data['State'] == 'Waitlist' )& (database_data['Printer'] == printer_selection) & (database_data['SubmissionNumber']<database_data['SubmissionNumber'].max() )].groupby('Printer')['Estimated Time'].transform('sum')
                            st.table(database_data)
                        with col1:
                            st.error('Submission Failed! Please fill the form correctly')
            with b2:
                if st.button("Nouvelle demande"):
                    st.session_state.uploaded_file = None
                    st.session_state.color = "Quelconque"
                    st.session_state.name = ""
                    st.session_state.requester = ""
                    st.session_state.printer_selection = ""
                    st.session_state.material = ""
                    st.session_state.estimated_time = 0
                    st.session_state.note = ""
                    st.rerun()

# Column 2: STL preview (conditionally rendered)
with col2:
    color_dict = {
        "Noir": "#222222",
        "Rouge": "red",
        "Bleu": "blue",
        "Vert": "green",
        "Jaune": "yellow",
        "Orange": "orange",
        "Violet": "purple",
        "Rose": "pink",
    }

    # Update session state for file and color
    if uploaded_file is not None:
        st.session_state.uploaded_file = uploaded_file
    if color != st.session_state.color:
        st.session_state.color = color

    # Display STL preview if both file and specific color are selected
    if st.session_state.uploaded_file is not None and st.session_state.color != "Quelconque":
        stl_plotter = load_stl(st.session_state.uploaded_file, color_dict[st.session_state.color])
        if stl_plotter is not None:  # Check if stl_plotter is not None
            stpyvista(stl_plotter, key="pv_stl_preview")
