# -*- coding: utf-8 -*-
"""
##Contains helping functions for petsc matrix and vector manipulation
"""

from petsc4py import PETSc
from slepc4py import SLEPc
Print = PETSc.Sys.Print
import numpy as np


def matrow(size,val):
    """
    Create a matrix with constant value `val` on the last raw of a matrix of size `size`.
    This function is collective
    
    Parameters
    ----------
    size : tuple 
        contains the the matrix size    
    val : complex value 
        the value to put on each component of the row matrix
    
    Returns
    -------
    M : petsc Mat
    """
    n,m = size
    #rank=MPI.COMM_WORLD.Get_rank()
    # create a sparse matrice aij
    M=PETSc.Mat()
    M.create()#PETSc.COMM_WORLD
    #M.setSizes( ((v.getLocalSize(), PETSc.DETERMINE),(PETSc.DETERMINE,1))  )
    M.setSizes( ((PETSc.DETERMINE, n),(PETSc.DETERMINE,m))  )
    M.setType('aij')
    M.setUp()
    istart,iend = M.getOwnershipRange()
    if (n-1) in (istart,iend-1):
        for j in range(0,n): # enhance using getOwnerShip range of M
            M.setValue(n-1,j,val )    # indice globaux
    
    M.assemblyBegin()    
    M.assemblyEnd()
    
    return M


def PETScVec2PETScMat(v):
    """
    Convert a petsc vector v into a 1 column aij matrix M
    Useful for nested matrix
    
    Parameters
    ----------
    v : petsc vec
        the vector to convert
    
    Returns
    -------
        M : petsc matrix
        the column matrix with the vector
    """
    # get local array (no copy)
    vloc =v.getArray()
    n = vloc.shape[0]
    #print('n=',n, 'rank',PETSc.COMM_WORLD.rank)
    # create scr index for matrix filling
    #TODO check int32
    I = np.zeros( (n,), dtype=np.int32) # size nnz
    J = np.arange( 0,n+1, dtype=np.int32) #+ rank*3
        
    # create a sparse matrice aij
    M=PETSc.Mat()
    M.create()#PETSc.COMM_WORLD
    M.setSizes( ((v.getLocalSize(), PETSc.DETERMINE),(PETSc.DETERMINE,1))  )
    M.setType('aij')
    M.setUp()    
    
    #M.createAIJWithArrays(size=(v.size, np.int32(1)) , csr= (J,I,vloc) )  #,bsize=None,comm=comm) remove because induce pb if not same parallel layout
    M.setValuesCSR(I=J,J=I,V=vloc )    
    M.assemblyBegin()    
    M.assemblyEnd()
    # return petsc matrix object    
    return M


def AvoidZerosDiagEntry(B):
    """
    Avoid Zeros entry on diagonal block error
    by adding 0 on the diagonal of the B matrix
    
    change with Matt suggestion   ((m, PETSC_DETERMINE), (n, PETSC_DETERMINE))
    as the 'size' argument.

    Parameters
    ----------
    B : petsc Mat
        the matrix to modify
    
    Returns
    -------
    B : petsc matrix
        B with explicit zeros on the diagonal
    """
    
    # construction d'un vecteur de 0
    d = B.getVecRight()
    d.set(0.)

    # construction d'une matrice diagonal avec 0
    D=PETSc.Mat()
    D.create()#PETSc.COMM_WORLD
    D.setSizes( ((B.getLocalSize()[0], PETSc.DETERMINE),(B.getLocalSize()[1],PETSc.DETERMINE))  )
    D.setType('aij')
    D.setUp()
    D.setDiagonal(d,PETSc.InsertMode.INSERT_VALUES)
    # modification de B
    B=B+D
    return B