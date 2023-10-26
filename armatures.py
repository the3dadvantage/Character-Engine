import bpy
import numpy as np
from mathutils import Matrix as MAT
import sys
import os
import importlib

psep = os.path.sep
path = '/home/rich/Desktop/cloth/character_engine'
sys.path.append(path)

try:
    U = bpy.data.texts['utils.py'].as_module()
    Q = bpy.data.texts['quaternions.py'].as_module()
    C = bpy.data.texts['coordinates.py'].as_module()
    
except:
    import utils as U
    import quaternions as Q
    import coordinates as C
    importlib.reload(U)
    importlib.reload(Q)
    importlib.reload(C)


#### quaternions ####
def get_ar_quats(ar, quats=None):
    """Returns rotation relative to edit bone.
    In other words: useless."""
    if quats is None:
        quats = np.empty((len(ar.pose.bones), 4), dtype=np.float32)
    ar.pose.bones.foreach_get('rotation_quaternion', quats.ravel())
    return quats


def get_ar_quats_world(ar, quats=None):
    if quats is None:
        world_quats = np.array([bo.matrix.to_quaternion() for bo in ar.pose.bones], dtype=np.float32)
        return world_quats
    # Or overwrite in place
    for i in range(quats.shape[0]):
        quats[i] = ar.pose.bones[i].matrix.to_quaternion()


def get_ar_matrix_world(ar, m3=False):
    """Returns whirled matrix."""
    world_matrix = np.array([bo.matrix for bo in ar.pose.bones], dtype=np.float32)
    if m3:
        return world_matrix[:, :3, :3]
    return world_matrix


#### quaternions ####
def set_ar_quats(ar, quats):
    ar.pose.bones.foreach_set('rotation_quaternion', quats.ravel())


#### quaternions ####
def set_ar_m3_world(ar, m3, locations=None, return_quats=False):
    """Sets the world rotation correctly
    in spite of parent bones. (and constraints??)"""
    if return_quats:
        quats = np.empty((m3.shape[0], 4), dtype=np.float32)
    for i in range(len(ar.pose.bones)):
        bpy.context.view_layer.update()
        arm = ar.pose.bones[i].matrix
        nparm = np.array(arm)
        nparm[:3, :3] = m3[i]
        if locations is not None:
            nparm[:3, 3] = locations[i]
        mat = MAT(nparm)
        if return_quats:
            quats[i] = mat.to_quaternion()
        ar.pose.bones[i].matrix = mat
    
    if return_quats:    
        return quats
    

#### quaternions ####
def set_ar_quats_world(ar, quats=None, locations=None):
    """Sets the world rotation correctly
    in spite of parent bones. (and constraints??)"""
    for i in range(len(ar.pose.bones)):
        bpy.context.view_layer.update()
        arm = ar.pose.bones[i].matrix
        nparm = np.array(arm)
        if quats is not None:
            qte = Q.quat_to_euler(quats[i], factor=1)        
            nparm[:3, :3] = qte
        if locations is not None:
            nparm[:3, 3] = locations[i]
        ar.pose.bones[i].matrix = MAT(nparm)


#### armature ####
def get_bone_head(ar, head=None):
    """Return Nx3 coordinates for bone head"""
    if head is None:
        head = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
    ar.pose.bones.foreach_get('head', head.ravel())
    return head


#### armature ####
def get_bone_tail(ar, tail=None):
    if tail is None:
        tail = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
    ar.pose.bones.foreach_get('tail', tail.ravel())
    return tail


def get_bone_vecs(ar):
    head = get_bone_head(ar)
    tail = get_bone_tail(ar)
    return (tail - head)


def get_bone_eco(ar, out=None):
    if out is None:
        bc = len(ar.pose.bones)
        out = np.empty((bc, 2, 3), dtype=np.float32)
    head = get_bone_head(ar)
    tail = get_bone_tail(ar)
    out[:, 0] = head
    out[:, 1] = tail
    return out
        

def get_bone_centers(ar, scale=0.5):
    """Get bone center or put scale
    in as an array calculating
    center of mass."""
    head = get_bone_head(ar)
    tail = get_bone_tail(ar)
    vec = (tail - head) * scale
    return head + vec


#### armature ####
def get_bone_locations(ar, location=None):
    """y and z are flipped on pose bones... why???"""
    
    if location is None:
        location = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
        yz = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
    
    ar.pose.bones.foreach_get('location', location.ravel())
    yz[:, 0] = location[:, 0]
    yz[:, 1] = -location[:, 2]
    yz[:, 2] = location[:, 1]
    return yz


#### armature ####
def get_bone_location_world(ar, location=None):
    """Get locs from matrix"""
    if location is None:
        location = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
    for e, bo in enumerate(ar.pose.bones):
        location[e] = np.array(bo.matrix, dtype=np.float32)[:3, 3]
    return location


def get_ar_m3(ar, m3=None):
    bc = len(ar.pose.bones)
    if m3 is None:
        m3 = np.empty((bc, 3, 3), dtype=np.float32)
    for e, bo in enumerate(ar.pose.bones):
        m3[e] = np.array(bo.matrix, dtype=np.float32)[:3, :3]
    return m3
    

#### armature ####    
def set_bone_locations(ar, location, yz=None):
    if yz is None:
        yz = np.empty((len(ar.pose.bones), 3), dtype=np.float32)
    yz=location # override!
    yz[:, 0] = location[:, 0]
    yz[:, 1] = location[:, 2]
    yz[:, 2] = -location[:, 1]    
    ar.pose.bones.foreach_set('location', yz.ravel())
    ar.pose.bones[0].location = yz[0]
    ar.pose.bones[0].location = ar.pose.bones[0].location

#### armature ####    
def update_bones(ar):
    ar.pose.bones[0].location = ar.pose.bones[0].location


#### armature ####    
def get_relative_bones(ar, flatten=True, return_repeater=True):
    """Get the index relationships of
    bones by parent and child
    relationships."""
    
    # add an index property to each bone
    flat = []
    repeater = []    
    for e, b in enumerate(ar.pose.bones):
        b['index'] = e
    
    relationships = []
    for bo in ar.pose.bones:
        rel = []
        related_count = len(b.children)
        if bo.parent is not None:
            flat += [bo.parent['index']]
            repeater += [bo['index']]
            rel += [bo.parent['index']] 
        for ch in bo.children:
            flat += [ch['index']]
            repeater += [bo['index']]
            rel += [ch['index']]
        relationships += [rel]
    
    if return_repeater:
        if flatten:    
            return flat, repeater
        return relative, repeater
    #print(flat, "this is flat")
    #print(repeater, "this is repeater")
    return relationships



def make_ar_mesh(ar):

    relative, repeater = get_relative_bones(ar)
    head = get_bone_head(ar)
    tail = get_bone_tail(ar)
        
    for bo in ar.pose.bones:
        bo['head'] = None
        bo['tail'] = None
        edges = []
    
    vert_count = 0
    co = []
    index = []
    for e, bo in enumerate(ar.pose.bones):
        edge = []
        
        if bo.parent is not None:
            if bo.parent['tail'] is not None:
                edge = bo.parent['tail']
                bo['head'] = bo.parent['tail']
            if bo.parent is None:
                bo['head'] = vert_count
                vert_count += 1
                index += [vert_count]
                co += [head[bo['index']]]
                
        if bo.parent is None:
            bo['head'] = vert_count
            vert_count += 1
            index += [vert_count]
            co += [head[bo['index']]]
            
        if len(bo.children) == 0:
            bo['tail'] = vert_count
            vert_count += 1
            index += [vert_count]
            co += [tail[bo['index']]]
        
        if len(bo.children) != 0:
            heads = np.array([ch['head'] for ch in bo.children])
            
            if np.any(heads != None):
                idx = heads[heads != None][0]
                for ch in bo.children:
                    ch['head'] = idx
                    bo['tail'] = idx
            
            if np.all(heads == None):
                bo['tail'] = vert_count
                vert_count += 1
                index += [vert_count]
                co += [tail[bo['index']]]
        
        edge = [bo['head'], bo['tail']]
        edges += [edge]
    
    ob = None
    name = ar.name + "_CE_physics_mesh"
    if name in bpy.data.objects:
        ob = bpy.data.objects[name]
        if ob.data.is_editmode:
            bpy.ops.object.mode_set()
        
    phys_mesh = U.link_mesh(co, edges, faces=[], name=name, ob=ob)
    return phys_mesh, edges, co, index, relative, repeater


if False:
    head = get_bone_head(ar)
    tail = get_bone_tail(ar)
    location = get_bone_location(ar)

if False:
    location += 0.1
    set_bone_location(ar, location)
    update_bones(ar)


class Rigs():
    def __init__(self):
        self.name = "this is doable"
        self.target_ar = bpy.data.objects['target']
        self.phys_ar = bpy.data.objects['physics']
        self.tb_count = len(self.target_ar.pose.bones)
        self.t_quats = np.empty((self.tb_count, 4), dtype=np.float32)
        get_ar_quats_world(self.target_ar, self.t_quats)        
    
    def get_target_data(self):
        get_ar_quats_world(self.target_ar, self.t_quats)
        
        print(self.t_quats[0])
        ee.rotation_quaternion = self.t_quats[0]
        

if False:
    print()
    R = Rigs()
    print(R.name)
    print("=====================")
    R.get_target_data()
