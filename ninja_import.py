import bpy
import bmesh
import mathutils
import os
import struct
import io

DEBUG = True

_ptr_offset = 0

def debug_print(msg):
    if DEBUG: print(msg)

def parse_chunk_model_vlist(mesh, buffer, base):
    chunk_cursor = base

    while True:
        chunk_head = int.from_bytes(buffer[chunk_cursor+0:chunk_cursor+4], 'little')
        chunk_type = chunk_head & 0xffff
        chunk_size = chunk_head >> 16
        
        chunk_type_identifier = chunk_type & 0xff
        chunk_type_flags = chunk_type >> 8


        if chunk_type_identifier >= 0x20 and chunk_type_identifier <= 0x32: # vertex chunk
            debug_print(f"Vertex chunk at {chunk_cursor}")

            # vertex format flags in chunk header
            fmt_sh = fmt_vn = fmt_d8 = fmt_uf = fmt_nf = fmt_s5 = fmt_s4 = fmt_in = fmt_nx = False
            # sorry this is ugly but they assigned these terribly
            match chunk_type_identifier:
                case 0x20: fmt_sh          = True
                case 0x21: fmt_vn = fmt_sh = True
                case 0x22: pass
                case 0x23: fmt_d8          = True
                case 0x24: fmt_uf          = True
                case 0x25: fmt_nf          = True
                case 0x26: fmt_s5          = True
                case 0x27: fmt_s4          = True
                case 0x28: fmt_in          = True
                case 0x29: fmt_vn          = True
                case 0x2a: fmt_vn = fmt_d8 = True
                case 0x2b: fmt_vn = fmt_uf = True
                case 0x2c: fmt_vn = fmt_nf = True
                case 0x2d: fmt_vn = fmt_s5 = True
                case 0x2e: fmt_vn = fmt_s4 = True
                case 0x2f: fmt_vn = fmt_in = True
                case 0x30: fmt_nx          = True
                case 0x31: fmt_nx = fmt_d8 = True
                case 0x32: fmt_nx = fmt_uf = True

            # vertex count, always present after chunk header
            num_vertices = int.from_bytes(buffer[chunk_cursor+4:chunk_cursor+8], 'little') >> 16
            vertex_cursor = chunk_cursor + 8
            debug_print(f"Num vertices: {num_vertices}")
            debug_print(f"Vertex format: {chunk_type_identifier:02x}")

            # get/create attribute layers
            color_layer = mesh.verts.layers.color.get("NinjaColor")
            if color_layer == None and (fmt_d8 or fmt_s4 or fmt_s5 or fmt_in): 
                color_layer = mesh.verts.layers.color.new("NinjaColor")

            # read vertex data
            for _ in range(num_vertices):
                
                vertex = mesh.verts.new()
                
                # position
                
                vertex.co = mathutils.Vector(struct.unpack('<fff', buffer[vertex_cursor+0:vertex_cursor+12]))
                vertex_cursor += 12
                if fmt_sh: 
                    vertex_cursor += 4

                # normal
                
                if fmt_vn:
                    vertex.normal = mathutils.Vector(struct.unpack('<fff', buffer[vertex_cursor+0:vertex_cursor+12]))
                    vertex_cursor += 12
                    if fmt_sh: 
                        vertex_cursor += 4
                elif fmt_nx:
                    # TODO
                    vertex_cursor += 4

                vertex.normal_update()

                # diffuse/specular color

                if fmt_d8:
                    # TODO
                    vertex_cursor += 4
                elif fmt_s4: 
                    # TODO
                    vertex_cursor += 4
                elif fmt_s5:
                    # TODO
                    vertex_cursor += 4
                elif fmt_in:
                    # TODO
                    vertex_cursor += 4

                # weights

                if fmt_nf:
                    # TODO
                    vertex_cursor += 4
                
            debug_print(f"Vertex cursor after reading data: {vertex_cursor}")


        elif chunk_type_identifier == 0xff: # end chunk
            debug_print(f"End chunk at {chunk_cursor}")
            break

        else:
            debug_print(f"Unrecognized chunk type 0x{chunk_type_identifier:02x} at {chunk_cursor} while parsing vlist")
            return
        
        chunk_cursor += 4
        chunk_cursor += chunk_size * 4
        
    mesh.verts.ensure_lookup_table()
    mesh.verts.index_update()

class ChunkStripVert:
    index = None
    uv = None
    uv2 = None

def parse_chunk_model_plist(mesh, buffer, base):
    chunk_cursor = base

    while True:
        chunk_head = int.from_bytes(buffer[chunk_cursor+0:chunk_cursor+4], 'little')
        chunk_type = chunk_head & 0xffff
        chunk_size = chunk_head >> 16
        
        chunk_type_identifier = chunk_type & 0xff
        chunk_type_flags = chunk_type >> 8

        if chunk_type_identifier >= 0x08 and chunk_type_identifier <= 0x09: # tiny chunk (texture index)
            debug_print(f"Tiny chunk at {chunk_cursor}")
            chunk_size = 0 # this chunk stores stuff in the size bytes and the actual size of the chunk is 0
            # TODO

        elif chunk_type_identifier >= 0x11 and chunk_type_identifier <= 0x1f: # material chunk
            debug_print(f"Material chunk at {chunk_cursor}")
            chunk_cursor
            # TODO

        elif chunk_type_identifier >= 0x38 and chunk_type_identifier <= 0x3a: # volume chunk (loose triangles)
            debug_print(f"Volume chunk at {chunk_cursor}")
            # TODO

        elif chunk_type_identifier >= 0x40 and chunk_type_identifier <= 0x4b: # strip chunk (triangle strips)
            debug_print(f"Strip chunk at {chunk_cursor}")
            
            uv_type = (chunk_type_identifier - 0x40) % 3 # 0=none, 1=lowres(256), 2=highres(1024)
            extra_type = (chunk_type_identifier - 0x40) // 3 # 0=none, 1=vertex normal, 2=diffuse color, 3=second uv layer

            uv_res = None
            match uv_type:
                case 1: uv_res = 255
                case 2: uv_res = 1023

            # strip count (and number of userflags per strip which is stuffed in the top two bits)
            num_strips = int.from_bytes(buffer[chunk_cursor+4:chunk_cursor+6], 'little')
            num_userflags = num_strips >> 14
            num_strips &= 0x3fff
            strip_cursor = chunk_cursor + 6
            
            debug_print(f"Num strips: {num_strips}")

            # get/create attribute layers
            uv_layer = mesh.loops.layers.uv.get("NinjaUV")
            if uv_layer == None and uv_type != 0: 
                uv_layer = mesh.loops.layers.uv.new("NinjaUV")

            color_layer = mesh.verts.layers.color.get("NinjaColor")
            if color_layer == None and extra_type == 2: 
                color_layer = mesh.verts.layers.color.new("NinjaColor")

            uv_layer_2 = mesh.loops.layers.uv.get("NinjaUV2")
            if uv_layer_2 == None and extra_type == 3: 
                uv_layer_2 = mesh.loops.layers.uv.new("NinjaUV2")

            # read strip data
            for i in range(num_strips):
                debug_print(f"Strip {i}/{num_strips}")
                num_indices = int.from_bytes(buffer[strip_cursor:strip_cursor+2], 'little', signed=True)
                strip_flip = (num_indices < 0)
                num_indices = abs(num_indices)

                strip_cursor += 2

                vertex_window = []

                for j in range(num_indices):
                    debug_print(f"Strip piece {j}/{num_indices}")
                    vert_obj = ChunkStripVert()

                    index = int.from_bytes(buffer[strip_cursor:strip_cursor+2], 'little')
                    vert_obj.index = index
                    debug_print(f"Index={index}")

                    strip_cursor += 2

                    if uv_type != 0:
                        u = int.from_bytes(buffer[strip_cursor:strip_cursor+2], 'little')
                        v = int.from_bytes(buffer[strip_cursor+2:strip_cursor+4], 'little')
                        vert_obj.uv = mathutils.Vector((u/uv_res, v/uv_res))
                        strip_cursor += 4

                    match extra_type:
                        case 1: # vertex normal
                            #TODO
                            strip_cursor += 6
                        case 2: # diffuse color
                            ar = int.from_bytes(buffer[strip_cursor:strip_cursor+2], 'little')
                            gb = int.from_bytes(buffer[strip_cursor+2:strip_cursor+4], 'little')
                            mesh.verts[index][color_layer] = mathutils.Vector((ar&0xff, gb>>8, gb&0xff, ar>>8))
                            strip_cursor += 4
                        case 3: # uv 2
                            u = int.from_bytes(buffer[strip_cursor:strip_cursor+2], 'little')
                            v = int.from_bytes(buffer[strip_cursor+2:strip_cursor+4], 'little')
                            vert_obj.uv2 = mathutils.Vector(u/uv_res, v/uv_res)
                            strip_cursor += 4


                    vertex_window.append(vert_obj)

                    if len(vertex_window) >= 3:
                        face = mesh.faces.new((
                            mesh.verts[vertex_window[0].index],
                            mesh.verts[vertex_window[1].index],
                            mesh.verts[vertex_window[2].index],
                        ))

                        if strip_flip: face.normal_flip()
                        if j % 2 == 1: face.normal_flip()

                        # match verts in the face loops we just created and assign uvs
                        for vert in vertex_window:
                            for loop in face.loops:
                                if vert.index == loop.vert.index:
                                    
                                    if vert.uv != None:
                                        loop[uv_layer].uv = vert.uv  
                                    if vert.uv2 != None:
                                        loop[uv_layer_2].uv = vert.uv2  
                                    
                                    break

                        vertex_window.pop(0)
                        strip_cursor += num_userflags * 2
            
            debug_print(f"Strip cursor after read: {strip_cursor}")

        elif chunk_type_identifier == 0x00: # null chunk
            debug_print(f"Null chunk at {chunk_cursor}")

        elif chunk_type_identifier == 0xff: # end chunk
            debug_print(f"End chunk at {chunk_cursor}")
            break

        else:
            debug_print(f"Unrecognized chunk type 0x{chunk_type_identifier:02x} at {chunk_cursor} while parsing plist")
            return
        
        chunk_cursor += 4
        chunk_cursor += chunk_size * 2


    mesh.verts.ensure_lookup_table()
    mesh.verts.index_update()


def load_chunk_model(context, buffer, base):
    vlist_ptr = int.from_bytes(buffer[base+0:base+4], 'little')
    plist_ptr = int.from_bytes(buffer[base+4:base+8], 'little')
    
    mesh = bpy.data.meshes.new("NinjaChunkModel")
    working_bmesh = bmesh.new()

    debug_print(f"Vlist pointer: {vlist_ptr}")
    parse_chunk_model_vlist(working_bmesh, buffer, vlist_ptr - _ptr_offset)
    debug_print(f"Plist pointer: {plist_ptr}")
    parse_chunk_model_plist(working_bmesh, buffer, plist_ptr - _ptr_offset)

    working_bmesh.to_mesh(mesh)
    working_bmesh.free()

    return mesh


def load_chunk_object(context, buffer, base=0, parent=None):
    eval_flags  = int.from_bytes(        buffer[base+ 0:base+ 4], 'little')
    model_ptr   = int.from_bytes(        buffer[base+ 4:base+ 8], 'little')
    o_position  = struct.unpack ('<fff', buffer[base+ 8:base+20])
    o_angle     = struct.unpack ('<fff', buffer[base+20:base+32])
    o_scale     = struct.unpack ('<fff', buffer[base+32:base+44])
    child_ptr   = int.from_bytes(        buffer[base+44:base+48], 'little')
    sibling_ptr = int.from_bytes(        buffer[base+48:base+52], 'little')
    
    mesh = None

    if (model_ptr != 0):
        debug_print(f"Model pointer: {model_ptr - _ptr_offset}")
        mesh = load_chunk_model(context, buffer, model_ptr - _ptr_offset)

    object = bpy.data.objects.new("NinjaChunkObject", mesh)

    object.parent = parent
    object.location = mathutils.Vector((o_position))
    #angle idk if euler or smth else so we will ignore for now
    object.scale    = mathutils.Vector((o_scale))
    
    context.collection.objects.link(object)
    
    object.select_set(True)

    if (child_ptr != 0): 
        debug_print(f"Model pointer: {model_ptr - _ptr_offset}")
        load_chunk_object(context, buffer, child_ptr - _ptr_offset, object)
    
    if (sibling_ptr != 0): 
        debug_print(f"Sibling pointer: {model_ptr - _ptr_offset}")
        load_chunk_object(context, buffer, sibling_ptr - _ptr_offset, parent)

    return object


def load(operator, context):
    if (not os.path.isfile(operator.filepath)):
        return {'CANCELED'}

    file_size = os.path.getsize(operator.filepath)

    match operator.format:
        case 'IFF_CONTAINER':
            _ptr_offset = 0
            with open(operator.filepath, 'rb') as file:
                while (file.tell() < file_size):
                    chunk_type = file.read(4)
                    chunk_size = int.from_bytes(file.read(4), 'little')
                    chunk_base = file.tell()

                    match chunk_type:
                        case b'NJCM': # chunk model
                            debug_print(f"NJCM chunk at {chunk_base}")
                            load_chunk_object(context, file.read(chunk_size))
                        case b'NJBM': # basic model
                            pass

                    file.seek(chunk_base + chunk_size, os.SEEK_SET)
                    
        case 'CHUNK_MODEL':
            _ptr_offset = operator.pointer_offset
            
        case 'BASIC_MODEL':
            _ptr_offset = operator.pointer_offset
            

    return {'FINISHED'}