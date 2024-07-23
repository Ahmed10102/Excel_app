# Avencement de la simulation ROS2
## Creation du fichier URDF
Aujourd'hui on a regroupé les fichier meshes dans un fichier urdf pour defnir le modele du robot q'on va integrer dans notre simulation.
![image](https://github.com/user-attachments/assets/b5e18f4e-b776-46ba-986a-50d3cd63dd04)
> On a verifier en visualisant notre model dans RViz
## Ajout des lien entre les composant du robot
On a joint les composants en creant des __links__ convenablement pour assurer le fonctionnement correcte de notre vehicule virtuelle
```xml
  <joint name="spoiler_joint" type="fixed">
    <origin xyz="0 0.05 -0.05" rpy="1.5708 0 3.14159" />
    <parent link="chassis_link" />
    <child link="spoiler_link" />
  </joint>
```
