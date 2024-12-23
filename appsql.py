import streamlit as st
import pandas as pd
from PIL import Image
import pyvista as pv
import tempfile
import os
from stpyvista import stpyvista
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import json


# Load the secret key from the JSON file
with open("secrets.json", "r") as file:
    secret = json.load(file)

# Access the secret key
PASSWORD= secret["secret_key"]
# Database connection setup
DATABASE_URL = "mysql+pymysql://root:"+PASSWORD+"@localhost:3306/3dprintingmanager"

# Set up SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

# Define the database models
class Printer(Base):
    __tablename__ = 'printers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    printer = Column(String(50), nullable=False)
    state = Column(String(50), nullable=False)

class Submission(Base):
    __tablename__ = 'submissions'
    submissionnumber = Column(Integer, primary_key=True, autoincrement=True)  # Primary key
    name = Column(String(100), nullable=False)
    requester = Column(String(50), nullable=False)
    printer = Column(String(50), nullable=False)
    material = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    note = Column(String(200))
    filename = Column(String(200))
    state = Column(String(50), nullable=False)
    estimated_time = Column(Float, nullable=False)
    total_wait_time = Column(Float, nullable=True)
    
# Create tables if they don't exist
Base.metadata.create_all(engine)

# Function to load STL file using PyVista
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

# Function to load printer data from the database
def load_printer_data():
    # Query the database and convert to a list of dictionaries
    printers = session.query(Printer).filter(Printer.state.in_(['Available', 'Busy'])).all()
    return [{'Printer': p.printer, 'State': p.state} for p in printers]

# Load printer data (not cached)
printer_data = load_printer_data()

# Convert the list of dictionaries to a DataFrame
printer_df = pd.DataFrame(printer_data)

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
        printer_selection = st.selectbox("Imprimantes", printer_df['Printer'].tolist())

        # Display availability tag
        for printer, state in zip(printer_df['Printer'], printer_df['State']):
            if printer == printer_selection:
                if state == "Available":
                    st.success(f"{printer} is {state}")
                elif state == "Busy":
                    st.warning(f"{printer} is {state}")
                else:
                    st.error(f"{printer} is {state}")
                    
        if printer_selection == "Resine":
            material = st.selectbox("Matériaux", ["RESINE"])
        else:
            material = st.selectbox("Matériaux", ["PLA", "ABS", "PETG"])
        color = st.selectbox("Couleurs", ["Quelconque", "Noir", "Rouge", "Bleu", "Vert"])
        estimated_time = st.number_input("Temps éstimé (en minutes)", step=10)
        note = st.text_area("Note")

        # Use a container to group the buttons
        button_container = st.container()
        with button_container:
            b1, b2, b3, b4, b5= st.columns([3, 3, 1, 1, 1])
            with b1:
                if st.button("Envoyer"):
                    if name and requester and uploaded_file and printer_selection and material and color and estimated_time:
                        # Save the uploaded STL file to the "files" folder with a temporary name (without submission number)
                        os.makedirs("files", exist_ok=True)  # Create the "files" folder if it doesn't exist
                        temp_file_path = os.path.join("files", f"temp_submission.stl")
                        with open(temp_file_path, "wb") as f:
                            f.write(uploaded_file.read())

                        # Create a new submission record
                        new_submission = Submission(
                            name=name,
                            requester=requester,
                            printer=printer_selection,
                            material=material,
                            color=color,
                            note=note,
                            filename=uploaded_file.name if uploaded_file else None,
                            state="Waitlist",
                            estimated_time=estimated_time
                        )

                        # Calculate total wait time
                        waitlist = session.query(Submission).filter_by(state='Waitlist', printer=printer_selection).all()
                        total_wait_time = sum(sub.estimated_time for sub in waitlist) + estimated_time
                        new_submission.total_wait_time = total_wait_time

                        # Add new submission to the session and commit
                        session.add(new_submission)
                        session.commit()

                        # Move the file to the final location with the correct submission number after commit
                        file_path = os.path.join("files", f"submission_{new_submission.submissionnumber}.stl")
                        os.rename(temp_file_path, file_path)
                        with col1:
                            st.success('Submission succeeded!')  
                        # Display the table in the second column
                        with col2:
                            
                            filtered_data = session.query(Submission).filter(
                                Submission.state == 'Waitlist',
                                Submission.printer == printer_selection,
                                Submission.submissionnumber <= new_submission.submissionnumber
                            ).all()
                            st.table(pd.DataFrame([{
                                'SubmissionNumber': sub.submissionnumber,
                                'Material': sub.material,
                                'Color': sub.color,
                                'Estimated Time': sub.estimated_time,
                                'Total Wait Time': sub.total_wait_time
                            } for sub in filtered_data]))
                                       
                    else:
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
