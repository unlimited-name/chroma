import xml.etree.ElementTree as et
import numpy as np
from collections import deque

from chroma.detector import Detector
from chroma.transform import make_rotation_matrix
from chroma.geometry import Mesh, Solid

#Using the PyMesh library instead of Chroma's internal meshes to support boolean
#operations like subtractions or unions. Perhaps Chroma's meshes should be
#replaced _entirely_ by PyMesh...
import pymesh

def box(x,y,z):
    '''Generate a mesh for a GDML box primitive'''
    return pymesh.generate_box_mesh([-x/2,-y/2,-z/2],[x/2,y/2,z/2])

def tube(z,r,segs=None):
    '''Generate a mesh for a GDML tube primitive. Note: does not support all parameters.'''
    if segs is None:
        segs = max(9,int(r*16))
    return pymesh.generate_cylinder([0,0,-z/2],[0,0,+z/2],r,r,num_segments=segs)
    
#To convert length and angle units to cm and radians
units = { 'cm':1, 'mm':0.1, 'm':100, 'deg':np.pi/180, 'rad':1 }

class Volume:
    '''
    Represents a GDML volume and the volumes placed inside it (physvol) as 
    childeren. Keeps track of position and rotation of the GDML solid.
    '''
    def __init__(self,name,gdml):
        self.name = name
        elem = gdml.vol_map[name]
        self.material_ref = elem.find('materialref').get('ref')
        self.solid_ref = elem.find('solidref').get('ref')
        placements = elem.findall('physvol')
        self.children = []
        self.child_pos = []
        self.child_rot = []
        for placement in placements:
            vol = Volume(placement.find('volumeref').get('ref'), gdml)
            pos, rot = gdml.get_pos_rot(placement)
            self.children.append(vol)
            self.child_pos.append(pos)
            self.child_rot.append(rot)

    def show_hierarchy(self,filename,indent='-'):
        flag = False
        if (filename == 0):
            filename = open('hierachy.txt','w+')
            flag = True
        
        filename.write(indent+str(self)+str(self.solid_ref)+str(self.material_ref))
        for child in self.children:
            child.show_hierarchy(indent=indent+' ')
        
        if flag:
            filename.close()

    def __str__(self):
        return self.name
    def __repr__(self):
        return str(self)

from chroma.demo.optics import vacuum
def _default_volume_classifier(volume_ref, material_ref, parent_material_ref):
    '''This is an example volume classifier, primarily for visualization'''
    if 'OpDetSensitive' in volume_ref:
        return 'pmt',dict(material1=vacuum, material2=vacuum, color=0xA0A05000, surface=None, channel_type=0)
    elif material_ref == parent_material_ref:
        return 'omit',dict()
    else:
        return 'solid',dict(material1=vacuum, material2=vacuum, color=0xEEA0A0A0, surface=None)
        

class GDMLLoader:
    '''
    This class supports loading a geometry from a GDML file by directly parsing 
    the XML. A subset of GDML is supported here, and exceptions will be raised
    if the GDML uses unsupported features.
    '''
    
    def __init__(self, gdml_file):
        ''' 
        Read a geometry from the specified GDML file.
        '''
        self.gdml_file = gdml_file
        xml = et.parse(gdml_file)
        gdml = xml.getroot()
        
        define = gdml.find('define')
        self.pos_map = { pos.get('name'):pos for pos in define.findall('position') }
        self.rot_map = { rot.get('name'):rot for rot in define.findall('rotation') }
        
        solids = gdml.find('solids')
        self.solid_map = { solid.get('name'):solid for solid in solids }
        
        structure = gdml.find('structure')
        volumes = structure.findall('volume')
        self.vol_map = { v.get('name'):v for v in volumes }
        
        world_ref = gdml.find('setup').find('world').get('ref')
        self.world = Volume(world_ref, self)
        self.mesh_cache = {}
        
    def get_pos_rot(self, elem):
        ''' 
        Searches for position and rotation children of an Element. The found
        Elements are returned as a tuple as a tuple. Checks for elements
        defined inline as position, rotation tags, and dereferences 
        positionref, rotationref using defined values. Returns None if 
        neither inline nor ref is specified.
        '''           
        pos = elem.find('position')
        if pos is None:
            pos = elem.find('positionref')
            if pos is not None:
                pos = self.pos_map[pos.get('ref')]
        rot = elem.find('rotation')
        if rot is None:
            rot = elem.find('rotationref')
            if rot is not None:
                rot = self.rot_map[rot.get('ref')]
        return pos,rot
        
    def get_vals(self, elem, value_attr=['x', 'y', 'z'], unit_attr='unit'):
        '''
        Calls get_val for a list of attributes (value_attr). The result 
        values are scaled from the unit specified in the unit_attrib attribute.
        '''
        scale = units[elem.get(unit_attr)] if unit_attr is not None else 1.0
        return [self.get_val(elem, attr) * scale for attr in value_attr]
        
    def get_val(self, elem, attr, default=None):
        '''
        Calls eval on the value of the attribute attr if it exists and return 
        it. Otherwise return the default specified. If there is no default 
        specifed, raise an exception.
        '''
        txt = elem.get(attr, default=None)
        assert txt is not None or default is not None, 'Missing attribute: '+attr
        return eval(txt, {}, {}) if txt is not None else default
        
    def get_mesh(self,solid_ref):
        '''
        Build a PyMesh mesh for the solid identified by solid_ref if the named
        solid has not been built. If it has been built, a cached mesh is returned.
        If the tag of the solid is not yet implemented, or it uses features not
        yet implemented, this will raise an exception.
        '''
        if solid_ref in self.mesh_cache:
            return self.mesh_cache[solid_ref]
        elem = self.solid_map[solid_ref]
        mesh_type = elem.tag
        if mesh_type == 'box':
            x, y, z = self.get_vals(elem,unit_attr='lunit')
            mesh = box(x, y, z)
        elif mesh_type == 'tube':
            ascale = units[elem.get('aunit', default='deg')]
            deltaphi = ascale*self.get_val(elem, 'deltaphi', default=360)
            #assert deltaphi == np.pi*2, 'partial tubes not implemented'
            if(deltaphi != np.pi*2):
                print("=========warning=========")
                print("Partial tubes not implemented")
                print("The angle is ",deltaphi)
            scale = units[elem.get('lunit', default='cm')]
            rmin = scale*self.get_val(elem,'rmin',default=0)
            #assert rmin == 0, 'hollow tubes not implemented'
            if(rmin != 0):
                print("=========warning=========")
                print("Hollow tubes not implemented")
                print("Rmin is ",rmin)
            rmax = scale*self.get_val(elem, 'rmax')
            z = scale*self.get_val(elem, 'z')
            mesh = tube(z,rmax)
        elif mesh_type == 'subtraction':
            a = self.get_mesh(elem.find('first').get('ref'))
            b = self.get_mesh(elem.find('second').get('ref'))
            pos, rot = self.get_pos_rot(elem)
            if pos is not None:
                x, y, z = self.get_vals(pos)
                b = pymesh.form_mesh(b.vertices + np.asarray([x, y, z]), b.faces)
            if rot is not None:
                rx, ry, rz = self.get_vals(rot)
                #FIXME use rotation to modify b
                assert rx==0 and ry==0 and rz==0, 'rotation not implemented'
            mesh = pymesh.boolean(a, b, operation='difference')
        else:
            raise Exception('Solid not implemented: '+self.tag)
        self.mesh_cache[solid_ref] = mesh
        return mesh
        
    def build_detector(self, detector=None, volume_classifier=_default_volume_classifier):
        '''
        Add the meshes defined by this GDML to the detector. If detector is not
        specified, a new detector will be created.
        
        The volume_classifier should be a function that returns a classification
        of the volume ('pmt','solid','omit') and kwargs passed to the Solid
        constructor for that volume: material1, material2, color, surface
        
        The different classifications have different behaviors:
        'pmt' should specify channel_type in the kwargs to identify the channel, calls add_pmt
        'solid' will add a normal solid to the Chroma geometry, calls add_solid
        'omit' will not add the Solid to the Chroma geometry
        '''
        if detector is None:
            detector = Detector(vacuum)
        q = deque()
        q.append([self.world, np.zeros(3), np.identity(3), None])
        while len(q):
            v, pos, rot, parent_material_ref = q.pop()
            for child, c_pos, c_rot in zip(v.children, v.child_pos, v.child_rot):
                c_pos = self.get_vals(c_pos) if c_pos is not None else np.zeros(3)
                c_rot = self.get_vals(c_rot) if c_rot is not None else np.identity(3)
                c_pos = np.matmul(c_pos,rot)+pos
                x_rot = make_rotation_matrix(c_rot[0], [1, 0, 0])
                y_rot = make_rotation_matrix(c_rot[1], [0, 1, 0])
                z_rot = make_rotation_matrix(c_rot[2], [0, 0, 1])
                c_rot = np.matmul(rot, np.matmul(x_rot, np.matmul(y_rot, z_rot))) #FIXME verify this order
                q.append([child, c_pos, c_rot, v.material_ref])
            m = self.get_mesh(v.solid_ref)
            mesh = Mesh(m.vertices, m.faces) # convert PyMesh mesh to Chroma mesh
            classification, kwargs = volume_classifier(v.name, v.material_ref, parent_material_ref)
            if classification == 'pmt':
                channel_type = kwargs.pop('channel_type',None)
                solid = Solid(mesh, **kwargs)
                detector.add_pmt(solid, displacement=pos, rotation=rot, channel_type=channel_type)   
            elif classification == 'solid':
                solid = Solid(mesh, **kwargs)
                detector.add_solid(solid, displacement=pos, rotation=rot)   
            elif classification == 'omit':
                pass
            else:
                raise Exception('Unknown volume classification: '+classification)
        return detector
