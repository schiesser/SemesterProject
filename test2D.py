import numpy as np
import akantu as aka
from variationnal_operator_function import *
import matplotlib.tri as tri
import matplotlib.pyplot as plt

print(aka.__file__)
print(aka.__version__)

## Mesh generation

mesh_file = """
Point(1) = {0, 0, 0, 1};
Point(2) = {1, 0, 0, 1};
Point(3) = {1, 1, 0, 1};
Point(4) = {0, 1, 0, 1};
"""
mesh_file += """
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
"""
mesh_file += """
Line Loop(5) = {1, 2, 3, 4};
"""
mesh_file += """
Plane Surface(6) = {5};
"""

open("triangle.geo", 'w').write(mesh_file)

# reading the mesh
spatial_dimension = 2    
mesh_file = 'triangle.msh'
mesh = aka.Mesh(spatial_dimension)
mesh.read(mesh_file)

conn = mesh.getConnectivity(aka._triangle_3)
nodes = mesh.getNodes()
triangles = tri.Triangulation(nodes[:, 0], nodes[:, 1], conn)
t=plt.triplot(triangles, '--', lw=.8)
plt.savefig('MeshElementTriangle.png')

##Support declaration

model = aka.SolidMechanicsModel(mesh)
model.initFull(_analysis_method=aka._static)

elem_filter = np.array([[0]])
fem = model.getFEEngine()
elem_type = aka._triangle_3
ghost_type = aka.GhostType(1) #peu importe pour le moment
Sup = Support(elem_filter, fem, spatial_dimension, elem_type, ghost_type)

## Interpolation

# create a field  
nodes = mesh.getNodes()

## Cas d'un champ scalaire :
nodal_field=np.ones((nodes.shape[0],nodes.shape[1]-1))*3
nodal_field[0,0]=2 #première coordonnée : numérotation du noeud; deuxième coordonnée : selon dimensions (ici 1D)
nodal_field[2,0]=1

'''
## Cas d'un champ vectoriel :
nodal_field=np.ones(nodes.shape)*3
nodal_field[0,0]=2 #première coordonnée : numérotation du noeud; deuxième coordonnée : selon dimensions (ici champ 2D)
nodal_field[2,1]=1
'''

print("nodal_field testé :")
print(nodal_field)
print("avec les connections :")
print(conn)

# Interpolation (avec 2ème méthode de "interpolateOnIntegrationPoints")
NTF = NodalTensorField("ex_displacement", Sup, nodal_field)

nb_integration_points = fem.getNbIntegrationPoints(Sup.elem_type)
nb_element = mesh.getConnectivity(Sup.elem_type).shape[0]
value_integration_points=np.zeros((nb_integration_points*nb_element,NTF.getFieldDimension())) #dimension : nbr quad point x field dimension

'''
Si element type map array :
#value_integration_points = aka.ElementTypeMapArrayReal() 
#value_integration_points.initialize(mesh, nb_component=1)
'''

NTF.evalOnQuadraturePoints(value_integration_points)

'''
Si element type map array :
value_integration_points=value_integration_points(aka._segment_2)
'''

print("valeurs aux points de quadrature du support")
print(value_integration_points)

# Integrate

print("Integration depl : ")
#help(Sup.fem.integrate)
integration_depl=FieldIntegrator.integrate(NTF, Sup, mesh)
print(integration_depl)
