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
Physical Line("BlockX") = {1};
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
E   = 2.1e11   # young's modulus
nu  = 0.3      # poisson's ratio

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
tol =10e-10
field_dim =2
print("nodes :")
print(nodes)

# Calcul depl. avec operateur diff. :
print("Computation of displacement using differential operator :")
Ngroup = N(Sup, field_dim)
B = GradientOperator(Ngroup)

# Constitutive law
MatrixD = E/((1+nu)*(1-2*nu))*np.array([[1-nu,nu,0],[nu,1-nu,0],[0,0,(1-2*nu)/2]])
D = ConstitutiveLaw(MatrixD, Sup)

# K (without boundary conditions)
BtDB = transpose(B)@D@B
K_locales = FieldIntegrator.integrate(BtDB)
K =Assembly.assemblyK(K_locales,Sup,2)

# K (with boundary conditions) : (boundary conditions will be setting "0" displacement at some ddl)
index = np.arange(0,nodes.shape[0]*field_dim)
## nodes with boundary condition
index_nodes_boundary_condition_x = index[::field_dim][nodes[:,1]<tol] #select x coordinates of nodes at position y=0
index_nodes_boundary_condition_y = index[1::field_dim][nodes[:,1]<tol] #select y coordinates of nodes at position y=0
index_remove = np.sort(np.concatenate((index_nodes_boundary_condition_x, index_nodes_boundary_condition_y))) 
ddl = np.setdiff1d(index, index_remove) #keep ddl without condition

K_reduced = K[:,ddl]
K_reduced = K_reduced[ddl,:]

# force 
f = np.zeros((K.shape[0]))
index_f_y = index[1::field_dim][nodes[:,1]>1-tol] # select ddl of component y of the nodes at y=1
f[index_f_y]=5000 #arbitrary value (traction)
b = f[ddl] #vector force for linear system

# visualize the test
print("blocked nodess :")
print((nodes.reshape(-1,1)[index_remove,:]).reshape(-1,2))
print("external force: ")
print(f.reshape(nodes.shape))

#solve linear system
x=np.zeros(index.shape)
x[ddl] = np.linalg.solve(K_reduced, b)

print("displacement :")
u1 = x.reshape(nodes.shape)
print(u1)

############################################
# Computation of displacement using Akantu
print("Computation of displacement using Akantu :")

# set the displacement/Dirichlet boundary conditions
model.applyBC(aka.FixedValue(0.0, aka._x), "BlockX")
model.applyBC(aka.FixedValue(0.0, aka._y), "BlockY")

# set the force/Neumann boundary conditions
model.getExternalForce()[:] = 0.0

trac = [0.0, 10000] # Newtons/m^2

model.applyBC(aka.FromTraction(trac), "Traction")

blocked_dofs = model.getBlockedDOFs()
fext = model.getExternalForce()

print("blocked nodes :")
print(nodes[blocked_dofs].reshape(-1,2))
print("external force")
print(fext)

# configure the linear algebra solver
solver = model.getNonLinearSolver()
solver.set("max_iterations", 2)
solver.set("threshold", 1e-8)
solver.set("convergence_type", aka.SolveConvergenceCriteria.residual)

# compute the solution
model.solveStep()

# extract the displacements
u2 = model.getDisplacement()
print(u2)

np.testing.assert_allclose(u1, u2, atol=tol, err_msg="Problme in patch test")
