# -*- coding: utf-8 -*-
"""
##Define an adapter design patern using object composition. 
It make easier the implementation of linear algebra operation without concreate 
reference to specific library

resused from 
https://github.com/faif/python-patterns/blob/master/patterns/structural/adapter.py 
"""

class Adapter(object):
    """
    Adapts an object by replacing methods.
    Usage:
    dog = Dog()
    dog = Adapter(dog, make_noise=dog.bark)

    Attributes
    ----------
    obj: initial object type
        contains a link to the original object
    
    #FIXME if the obj called a copy, get back an obj instead of an Adapter
    """

    def __init__(self, obj, **adapted_methods):
        """We set the adapted methods in the object's dict"""
        self.obj = obj
        self.__dict__.update(adapted_methods)

    def __getattr__(self, attr):
        """All non-adapted calls are passed to the object"""
        return getattr(self.obj, attr)

    def original_dict(self):
        """Print original object dict"""
        return self.obj.__dict__


def adaptVec(obj, lib):
    """ Create an Vector-adapter for the different linear algera library
    
    Parameters
    -----------
    obj : objet
        the objet to adapter
    lib : string
        string that describe the library 'petsc', 'numpy', 'scipysp'
    
    Returns
    --------
    adapted : adapter
        the adapted object    
    
    remarks :
    ---------
    copy, dot, duplicate return the native object type
    set return an adatper object    
    """    
#    def try_method(obj,method):
#        """ test if the method is present in the object
#        """
#        try:                           
#            return getattr(obj,method)
#        except:             
#            return None
                 
      

    if lib=='petsc':
        ADAPTER={'duplicate':obj.duplicate, # duplicate copy patern but not the values, use before set!
                  'dot':obj.__mul__,
                  'copy':obj.copy,
                  'set':obj.set} #'set':try_method(obj,'set')} 
                  
    elif lib=='numpy':                   
        ADAPTER={'duplicate':obj.copy,
                 'dot':obj.dot,
                 'copy':obj.copy,
                 'set':obj.fill}
    
    # With scipysp the vector are full numpy vector, fill don't belong to scipy !
    elif lib=='scipysp':
        ADAPTER={'duplicate':obj.copy,
                 'dot':obj.__mul__,
                 'set':obj.fill}  # fill is not a method of scipy.sparse (try_method(obj,'fill'))
    else:
        raise NotImplementedError('The library {} is not yet implemented'.format(lib))
       
    # create the adapted objet
    return Adapter(obj,**ADAPTER)
    
def adaptMat(obj, lib):
    """ Create an Matrix-adapter for the different linear algera library
    
    Parameters
    -----------
    obj : objet
        the objet to adapter
    lib : string
        string that describe the library 'petsc', 'numpy', 'scipysp'
    
    Returns
    --------
    adapted : adapter
        the adapted object    
    
    remarks :
    ---------
    copy, dot, duplicate return the native object type
    set return an adatper object
    """    
          
          
    if lib=='petsc':
        ADAPTER={'duplicate':obj.duplicate, # duplicate copy patern but not the values, use before set !
                  'dot':obj.__mul__,
                  'copy':obj.copy,
                  } 
                  
    elif lib=='numpy':                   
        ADAPTER={'duplicate':obj.copy,
                 'dot':obj.dot,
                 'copy':obj.copy
                 }
                 
    elif lib=='scipysp':
        ADAPTER={'duplicate':obj.copy,
                 'dot':obj.__mul__,
                 'copy':obj.copy
                 } # #FIXME with scipy we use full numpy vector, fill don't belong to scipy !
    else:
        raise NotImplementedError('The library {} is not yet implemented'.format(lib))
       
    # create the adapted objet
    return Adapter(obj,**ADAPTER)    
