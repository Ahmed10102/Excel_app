# Liste d'attente d'impression 3D
## A propos
Cette application est crée pou gérer les demandes d'impression 3D pour l'innovation.
J'ai choisi pour créer cet application d'utiliser la bibliotèque Python Streamlit qui donne la capacité de construire une application web avec un theme moderne rien qu'avec Python.

![download](https://github.com/user-attachments/assets/1bcf0dcb-f34b-4efb-be3c-4ee2046b7cf5)

## Creation du formulaire 
On a utiliser les composent standard de Streamlit pour créer les champs du formulaire.

### Installation

pour télecharger la bibliotèque Streamlit on a simplement utiliser la comande ___pip___


``` bash
pip install streamlit
```

### Les élements standard que j'ai utiliser sont :

- text input :
```python
name=st.text_input("Name")
```` 
- drop down :
```python
requester = st.selectbox("Demandeur", ["INNOVATION", "STARTUPS"])
```` 
- file uploaer :
```python
uploaded_file = st.file_uploader("Importer un fichier STL", type=["stl"])
```` 
- number input :
 ```python
estimated_time = st.number_input("Temps éstimé (en minutes)", step=10)
```
- button :
```python
if st.button("Envoyer"):
```

## Le formulaire :

![image](https://github.com/user-attachments/assets/037b8b0f-dbb3-48bb-9914-49533ba4fdd0)



___

Pour rendre notre application plus interactive, j'ai ajouter la capacité de prévoir le modèle 3D aprés choisir le fichier et le couleur :

https://github.com/user-attachments/assets/7f47037c-4fac-4264-972e-5d4eb3473e5b

Pour réaliser cette partie on a utliser les bibliothèques __pyvista__ et __stpyvista__ . \
__Stpyvista__ utilser __pyvista__ pour géenérer des modèles 3d dans l'application __Streamlit__.

> Afficher l'aperçu STL si un fichier et une couleur spécifique sont sélectionnés
``` python
if st.session_state.uploaded_file is not None and st.session_state.color != "Quelconque":
```
> Creation d'une instance de 3D appartir du fichier uploadé
``` python
    stl_plotter = load_stl(st.session_state.uploaded_file, color_dict[st.session_state.color])
    if stl_plotter is not None:
        stpyvista(stl_plotter, key="pv_stl_preview")
```

## Gestion de données :
Pour faciliter la gestion de données et laisser l'option de gestion manuelle on a préféré de choisir un fichier Excel comme notre base de données ou ce trouve la liste des imprimantes et leur état (Disponible / Occupé / Non-Disponible).

On a utiliser __pandas__ et __openpyxl__ pour acceder les fichier excel et les modifier d'une façon fluide
``` python
import pandas as pd
import openpyxl
```
> lire à partir le pdf
``` python
pd.read_excel(file, sheet_name=sheet) 
```
> écrire dans le pdf
``` python
pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer 
