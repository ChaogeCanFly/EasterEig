# -*- coding: utf-8 -*-
""" ##Definiftion of the eigenvalue solver class for numpy, scipy.sparse and petsc/slepc solvers

This module implement standard, generalized and quadratic eigenvalue problems.

Examples
--------
The basic use of this class is

1. Create the solver object :
 `myOP.createSolver(lib='numpy',pb_type='gen')`
2. Solve :
 `myOP.solver.solve(nev=6,target=0+0j,skipsym=False)`
3. Get back the eigenvalue and eigenvector in a list of Eig object :
 `extracted = myOP.solver.extract( [0,1] )`
4. Destroy solver (usefull for petsc/slepc) :
 `myOP.solver.destroy()`

Remarks
-------
The petsc version is configured to use shift and invert with mumps...
"""

from abc import ABC, abstractmethod
import scipy as sp
from scipy.sparse.linalg import eigs
import numpy as np

from eastereig import _petscHere, Eig, gopts

if _petscHere:
    from slepc4py import SLEPc
    from petsc4py import PETSc
    Print = PETSc.Sys.Print


# compatible with Python 2 *and* 3:
#ABC = ABCMeta('ABC', (object,), {'__slots__': ()})

class EigSolver(ABC):
    """ Define the abstract interface common to all Eigenvalue solver
    
    
    Attributes
    ----------
    K : matrix or matrix list
        contains the eigenvalue problem matrices
    pb_type: string {'std','gen','PEP''}
        the type of eigenvalue problem to solve
    Lda : list
        List of the sorted eigenvalues    
    """
    
    def __init__(self, K, pb_type):
        """ Init the solver with pb_type and the list of matrix K
        """
        # store pb_type
        self.pb_type=pb_type
        # create a link to the eigenvalue problem matrices (from parent object)
        self.K=K
    
    
    def extract(self, eig_list):
        """ Extract the eig_list eigenvectors and return a type of Eig object ?
    
        Parameters
        ----------
        eig_list : iterable
            index list (related to the sort criteria) of the wanted eigenvalue
            
        Returns
        -------
        extrated : list 
            list of Eig objects associated to eig_list
        """
        extracted = []
        # loop over the modes
        for i in eig_list:
            extracted.append( Eig(self._lib,self.Lda[i], self.Vec[:,i]) )
                    
        return extracted 

    def destroy(self):
        """ Destroy the solver"""
        pass
            
    def sort(self,key='abs',skipsym=False):	
        """ Sort the eigenvalue problem by order of magnitude
        
        Important to be sure that all solver use the same criteria
        
        Parameters
        ----------
        key : 'abs' (default), 'real', 'imag'
            the key used to sort the eigenavlues
        skipsym : bool
            remove eigenvalue with imag lda< 0
            
        Remarks
        ------
        collective
        """ 
        key_func_dict={'abs':np.abs,'imag':np.imag,'real':np.real}        
        if key in key_func_dict.keys():
            key_func = key_func_dict[key]
        else:
            raise AttributeError('This type of key is not defined')
            
        
        if skipsym==True:
            # Filter left going waveguide modes
            skip_idx = np.where(self.Lda.imag>0)[0] # unpack tuple
            self.Lda = self.Lda[skip_idx]
        
        # sort by assending order of key
        self.idx = np.argsort(key_func(self.Lda)) # like in matlab
        self.Lda = self.Lda[self.idx]
        # if symmetric filtering is active need global index for eigenvector
        if skipsym==True:
            self.idx = skip_idx[self.idx]
        
        self.nconv = len(self.Lda)
        
    @abstractmethod
    def solve(self, nev=6,target=0+0j,key='abs',skipsym=False):	
        """ Solve the eigenvalue problem"""    
        pass

	



      
        
class NumpyEigSolver(EigSolver):
    """ Define the concrete interface common to all numpy Eigenvalue solver
    
    The eigenvalue problem is solved with numpy for full matrix
    
    #TODO add PEP by linearization
    """
    # keep trace of the lib
    _lib='numpy'              
    def solve(self,nev=6,target=0+0j,skipsym=False):
        """ Solve the eigenvalue problem and get back the results as (Lda, X)

        Parameters
        ----------
        nev : int
            number of requested eigenpairs
        target : complex, optional
            target used for the shift and invert transform
        skipsym : bool
            remove eigenvalue with imag lda< 0

        Remarks
        --------
        For full matrix, all eigenvalues are obtained. Neither 'nev' nor 'target' are used. These parameters
        are used to ensure a common interface between solvers.
        """   
        print('> Solve {} eigenvalue problem with {} class...\n'.format(self.pb_type,self.__class__.__name__))
        if self.pb_type=='std':            
            self.Lda,Vec = sp.linalg.eig(self.K[0],b=None) 
        elif self.pb_type=='gen':            
            self.Lda,Vec = sp.linalg.eig(self.K[0],b=-self.K[1]) 
        else:
            raise NotImplementedError('The pb_type {} is not yet implemented'.format(self.pb_type))
        
        # sort eigenvectors and create idx index
        self.sort(skipsym=skipsym)    
        self.Vec=Vec[:,self.idx]

        return self.Lda
            


class ScipySpEigSolver(EigSolver):
    """ Define the concrete interface common to all numpy Eigenvalue solver
    
    The eigenvalue problem is solved with numpy for full matrix
    
    #TODO add PEP by linearization
    
    """
    # keep trace of the lib
    _lib='scipysp'      
    
    def solve(self,nev=6,target=0+0j,skipsym=False):
        """ Solve the eigenvalue problem and get back the results as (Lda, X)
        
        Parameters
        ----------
        nev : int
            number of requested eigenpairs
        target : complex, optional
            target used for the shift and invert transform
        skipsym : bool
            remove eigenvalue with imag lda< 0

        Remarks
        --------
        For full matrix all eigenvalues are obtained. nev is not used.
        """   
        print('> Solve eigenvalue {} problem with {} class...\n'.format(self.pb_type,self.__class__.__name__))
        if self.pb_type=='std':            
            self.Lda,Vec = eigs(self.K[0], k=nev, M=None, sigma=target, return_eigenvectors=True) 
        elif self.pb_type=='gen':            
            self.Lda,Vec = eigs(self.K[0], k=nev, M=-self.K[1], sigma=target, return_eigenvectors=True) 
        else:
            raise NotImplementedError('The pb_type {} is not yet implemented'.format(self.pb_type))
        
        # sort eigenvectors and create idx index
        self.sort(skipsym=skipsym)    
        self.Vec=Vec[:,self.idx]

        return self.Lda


# define only if petsc and slepc are present
if _petscHere:
     class PetscEigSolver(EigSolver):
        """ Define the concrete interface common to all PETSc/SLEPc Eigenvalue solver
        
        Configured to use shift and invert transform with mumps
        """
        #todo if move into fonction, no need to add a test if poetscHere ?
        PB_TYPE_FACTORY = {
            'std':SLEPc.EPS,
            'gen':SLEPc.EPS,
            'PEP':SLEPc.PEP
              }
        """ list of petsc factory depending on the kind of eigenvalue problem
        """
    
        PB_TYPE = {
            'std': SLEPc.EPS.ProblemType.NHEP,
            'gen': SLEPc.EPS.ProblemType.GNHEP,
            'PEP': SLEPc.PEP.ProblemType.GENERAL
            }
        """
        SLEPc problem type dictionnary, by defaut use only *non-hermitian*   
        """
    
        # keep trace of the lib
        _lib='petsc'         
        
        def __init__(self, K, pb_type):
            """ init slepc with the good pb_type"""
            # check input
            if pb_type not in self.PB_TYPE_FACTORY.keys():
                raise NotImplementedError('The pb_type {} is not yet implemented...'.format(self.pb_type))
            # store pb type
            self.pb_type=pb_type
            self._SLEPc_PB = PetscEigSolver.PB_TYPE_FACTORY[pb_type]
            # create a link to the eigenvalue problem matrices (from parent object)
            self.K=K
            
        def _create(self,nev,target):
            """ Create and setup the SLEPC solver"""
            
            # mpi stuff    
            comm=PETSc.COMM_WORLD.tompi4py()
            rank = comm.Get_rank()
            # create the solver with the selected factory
            E = self._SLEPc_PB()
            E.create()
            
            # Setup the spectral transformation
            SHIFT = SLEPc.ST().create()
            SHIFT.setType(SHIFT.Type.SINVERT)
            E.setST(SHIFT)  
            E.setTarget(target)
            # operator setup
            K = self.K
            if self.pb_type == 'std':
                # unpack the operator matrix        
                E.setOperators(*K)
            if self.pb_type == 'gen':
                # M=-K1      
                E.setOperators(K[0],-K[1])            
            else:
                E.setOperators(K)
                
            # number of eigenvlue we are looking for   
            E.setDimensions(nev=nev)
            # By defaut use non hermitian solver
            E.setProblemType(self.PB_TYPE[self.pb_type])
       
            # Direct solver seting (for shift and invert)      
            ksp=SHIFT.getKSP()    
            ksp.setType('preonly')  # direct solver in petsc= preconditioner        
            pc=ksp.getPC()
            pc.setType('lu')
            #pc.setFactorSolverType('superlu_dist')
    
            # set solver options
            pc.setFactorSolverType(gopts['direct_solver_name'])
            opts = PETSc.Options(gopts['direct_solver_petsc_options_name'])
            for op_name,op_value in gopts['direct_solver_petsc_options_dict'].items():
                opts[op_name]=op_value
            # Mumps options to avoid mumps crash with high fill in
            # The problem arise if the prediction/mem allocation is too different (default 20%)
            #opts["icntl_14"] = 50 # ICNTL(14) controls the percentage increase in the estimated working space
            #opts["icntl_6"] = 5  # Use ICNTL(6)= 5 for augmented system (which is asystem with a large zero diagonal block).     
      
            #  After all options have been set, the user should call the setFromOptions() 
            E.setFromOptions()
            
            # store the solver
            self.E=E
            
        def destroy(self):
            """ Destroy the petsc/slecp solver"""
            self.E.destroy()
    
        def extract(self, eig_list):
            """ Extract the eig_list eigenvectors
        
            Parameters
            ----------
            eig_list : iterable
                index list (related to the sort criteria) of the wanted eigenvalue
                
            Returns
            -------
            extrated : list 
                list of Eig objects associated to eig_list
            """               
            # init output
            extracted = []
            # create petsc vector
            vr = self.K[0].createVecRight() 
            # loop over the modes
            for i in eig_list:            
                lda =self.E.getEigenpair(self.idx[i],vr) 
                extracted.append( Eig(self._lib,lda, vr.copy()) )
                        
            return extracted
            
        def solve(self,nev=6,target=0+0j,key='abs',skipsym=False):
            """ Solve the eigenvalue problem and get back the results as (Lda, X)
            
            Parameters
            ----------
            nev : int
                number of requested eigenpairs
            target : complex, optional
                target used for the shift and invert transform
            skipsym : bool
                remove eigenvalue with imag lda< 0
            
            Remarks
            --------
            It is still possible to interact with the SLEPc solver until the destroy method call 
            """   
            
            self._create(nev,target)
            Print('> Solve eigenvalue {} problem with {} class ...\n'.format(self.pb_type,self.__class__.__name__))
            self.E.solve() 
            
            nconv = self.E.getConverged()
            self.Lda = np.zeros((nconv,),dtype=np.complex128)
              
            # extract *unsorted* eigenvalue
            for i in range(0,nconv):    
                self.Lda[i] = self.E.getEigenpair(i) # collective
            # sort
            self.sort(key=key,skipsym=skipsym)
            
            return self.Lda
