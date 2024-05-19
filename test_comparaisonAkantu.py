import numpy as np
import akantu as aka
from variationnal_operator_function import *
import matplotlib.tri as tri
import matplotlib.pyplot as plt
from plot import *

print(aka.__file__)
print(aka.__version__)

## Mesh generation
#.geo
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
Physical Line("BlockY") = {1};
Physical Line("BlockX") = {4};
Physical Line("Traction") = {3};
Physical Surface("Mesh") = {6};
"""
open("triangle.geo", 'w').write(mesh_file)

#.msh
nodes, conn = meshGeo("triangle.geo", dim =2, order=1, element_type='triangle')
# reading the mesh
spatial_dimension = 2
mesh_file = 'triangle.msh'
mesh = aka.Mesh(spatial_dimension)
mesh.read(mesh_file)

##Plot
conn = mesh.getConnectivity(aka._triangle_3)
nodes = mesh.getNodes()
triangles = tri.Triangulation(nodes[:, 0], nodes[:, 1], conn)
t=plt.triplot(triangles, '--', lw=.8)
plt.savefig('MeshElementTriangle.png')

## Material File
material_file = """
material elastic [
    name = steel
    rho = 7800     # density
    E   = 2.1e11   # young's modulus
    nu  = 0.3      # poisson's ratio
]"""
open('material.dat', 'w').write(material_file)
material_file = 'material.dat'
aka.parseInput(material_file)

## Solid MechanicsModel
model = aka.SolidMechanicsModel(mesh)
model.initFull(_analysis_method=aka._static)

##Support declaration
elem_filter = np.array([[0]])
fem = model.getFEEngine()
elem_type = aka._triangle_3
ghost_type = aka.GhostType(1)
Sup = Support(elem_filter, fem, spatial_dimension, elem_type, ghost_type)
############################################
# Calcul deplacement avec Akantu

# set the displacement/Dirichlet boundary conditions
model.applyBC(aka.FixedValue(0.0, aka._x), "BlockX")
model.applyBC(aka.FixedValue(0.0, aka._y), "BlockY")

# set the force/Neumann boundary conditions
model.getExternalForce()[:] = 0.0

trac = [1.0, 1.0] # Newtons/m^2

model.applyBC(aka.FromTraction(trac), "Traction")

# configure the linear algebra solver
solver = model.getNonLinearSolver()
solver.set("max_iterations", 2)
solver.set("threshold", 1e-8)
solver.set("convergence_type", aka.SolveConvergenceCriteria.residual)

# compute the solution
model.solveStep()

# extract the displacements
u = model.getDisplacement()
print(u)