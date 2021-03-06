import ufl
import dolfinx
import numpy
from mpi4py import MPI
from dolfinx.io import XDMFFile
from fem import assemble_matrix, assemble_vector
import odd
from petsc4py import PETSc
from scipy.sparse.linalg import spsolve

comm = MPI.COMM_WORLD
mesh = dolfinx.UnitIntervalMesh(comm, 10)

mesh = dolfinx.UnitSquareMesh(comm, 2000, 2000, ghost_mode=dolfinx.cpp.mesh.GhostMode.shared_facet)
n = ufl.FacetNormal(mesh)
k0 = 10

# Definition of test and trial function spaces
deg = 1  # polynomial degree
V = dolfinx.FunctionSpace(mesh, ("Lagrange", deg))

u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)

def plane_wave(x):
    '''Plane Wave Expression'''
    theta = numpy.pi/4
    return numpy.exp(1.0j * k0 * (numpy.cos(theta) * x[0] + numpy.sin(theta) * x[1]))

# Prepare Expression as FE function
ui = dolfinx.Function(V)
ui.interpolate(plane_wave)
g = ufl.dot(ufl.grad(ui), n) + 1j * k0 * ui


a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx - k0**2 * ufl.inner(u, v) * ufl.dx  \
    + 1j * k0 * ufl.inner(u, v) * ufl.ds
L = ufl.inner(g, v) * ufl.ds

# Assemble distribute Matrix (odd format)
# A = assemble_matrix(a)
# Assemble distribute vector
b = assemble_vector(L)
bp = dolfinx.fem.assemble_vector(L)


t = MPI.Wtime()
for i in range(100):
    v_odd = numpy.vdot(b, b)
t = MPI.Wtime() - t

tpetsc = MPI.Wtime()
for i in range(100):
    v_petsc = bp.dot(bp)
tpetsc = MPI.Wtime() - tpetsc

if comm.rank == 0:
    print(t/ tpetsc)