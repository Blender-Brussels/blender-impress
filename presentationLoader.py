#   _    _             _             _                          
#  | |__| |___ _ _  __| |___ _ _ ___(_)_ __  _ __ _ _ ___ ______
#  | '_ \ / -_) ' \/ _` / -_) '_|___| | '  \| '_ \ '_/ -_|_-<_-<
#  |_.__/_\___|_||_\__,_\___|_|     |_|_|_|_| .__/_| \___/__/__/
#                                         |_|                 
#
#  File:		presentationLoader.py 
#
#  Description: This file is part of Blender-Impress,
#				a slide show presentation tool using the Blender Game Engine.
#
#  Source: 		https://github.com/Blender-Brussels/blender-impress
#
#  License:
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#


# The location of the xml file describing your slides
XML_PRESENTATION_FILE = 'presentation.xml'


import bpy
from mathutils import Vector
import os
import xml.etree.ElementTree as ET

from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty,
                       CollectionProperty,
                       )

from bpy_extras.image_utils import load_image


# copy/paste and dirty hack of blender-2.70-linux-glibc211-x86_64/2.70/scripts/addons/io_import_images_as_planes.py 

def set_texture_options( context, texture ):
    #texture.image.use_alpha = BoolProperty(name="Use Alpha", default=False, description="Use alphachannel for transparency")
    texture.image.use_alpha = False
    #texture.image_user.use_auto_refresh = bpy.types.ImageUser.bl_rna.properties["use_auto_refresh"]
    texture.image_user.use_auto_refresh = True
    ctx = context.copy()
    ctx["edit_image"] = texture.image
    ctx["edit_image_user"] = texture.image_user
    bpy.ops.image.match_movie_length(ctx)

def set_material_options( material, slot):
    material.alpha = 1.0
    material.specular_alpha = 1.0
    # slot.use_map_alpha = False
    #material.use_transparency = BoolProperty(name="Use Alpha", default=False, description="Use alphachannel for transparency")
    material.use_transparency = False
    material.use_shadeless = True
    #t = bpy.types.Material.bl_rna.properties["transparency_method"]
    #items = tuple((it.identifier, it.name, it.description) for it in t.enum_items)
    #material.transparency_method = EnumProperty(name="Transp. Method", description=t.description, items=items)
    #t = bpy.types.Material.bl_rna.properties["use_shadeless"]
    #material.use_shadeless = BoolProperty(name=t.name, default=False, description=t.description)
    #t = bpy.types.Material.bl_rna.properties["use_transparent_shadows"]
    #material.use_transparent_shadows = BoolProperty(name=t.name, default=False, description=t.description)

def create_image_textures( context, image):
    fn_full = os.path.normpath(bpy.path.abspath(image.filepath))
    # look for texture with importsettings
    for texture in bpy.data.textures:
        if texture.type == 'IMAGE':
            tex_img = texture.image
            if (tex_img is not None) and (tex_img.library is None):
                fn_tex_full = os.path.normpath(bpy.path.abspath(tex_img.filepath))
                if fn_full == fn_tex_full:
                    set_texture_options(context, texture)
                    return texture

    # if no texture is found: create one
    name_compat = bpy.path.display_name_from_filepath(image.filepath)
    texture = bpy.data.textures.new(name=name_compat, type='IMAGE')
    texture.image = image
    set_texture_options(context, texture)
    return texture

def create_material_for_texture( texture ):
    # look for material with the needed texture
    for material in bpy.data.materials:
        slot = material.texture_slots[0]
        if slot and slot.texture == texture:
            set_material_options(material, slot)
            return material

    # if no material found: create one
    name_compat = bpy.path.display_name_from_filepath(texture.image.filepath)
    material = bpy.data.materials.new( name=name_compat )
    slot = material.texture_slots.add()
    slot.texture = texture
    slot.texture_coords = 'UV'
    set_material_options(material, slot)
    return material

def img2plane( folder, filename ):
    
    if filename not in bpy.data.images:
        # no need to reload the image, it is already in the memory!
        f = load_image( bpy.path.abspath( folder + filename ) )
    
    if filename not in bpy.data.images:
        print( "filename:", folder + filename, "NOT FOUND!" )
        return
    
    img = bpy.data.images[ filename ]
    #print( img, img.generated_width, img.generated_height, img.size )
    
    ratio = img.size[ 0 ] / img.size[ 1 ]
    #print( ratio )
    
    scalew = ratio
    scaleh = 1
    '''
    if ratio > 1:
        scaleh = 1 / ratio
    else:
        scalew = 1 / ratio
    '''
    
    texture = create_image_textures( bpy.context, img )
    material = create_material_for_texture( texture )
    
    bpy.ops.mesh.primitive_plane_add('INVOKE_REGION_WIN')
    plane = bpy.context.scene.objects.active
    if plane.mode is not 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    plane.location = (0,0,0)
    plane.dimensions = scalew, scaleh, 0.0
    plane.name = material.name
    bpy.ops.object.transform_apply(scale=True)
    plane.data.uv_textures.new()
    plane.data.materials.append(material)
    plane.data.uv_textures[0].data[0].image = img
    
    material.game_settings.use_backface_culling = False
    material.game_settings.alpha_blend = 'ALPHA'
    
    return plane

def video2plane( folder, filename ):
    
    if "video_init" not in bpy.data.texts:
        print( "creation of a 'video_init' text block" )
    
    if "video_update" not in bpy.data.texts:
        print( "creation of a 'video_init' text block" )
    
    p = img2plane( folder, filename )
    
    bpy.context.scene.objects.active = p
    bpy.ops.object.game_property_new(type='STRING', name="video_path")
    prop = p.game.properties['video_path']
    prop.value = bpy.path.abspath( folder + filename )
    
    bpy.ops.object.game_property_new( type='BOOL', name="play" )
    prop = p.game.properties['play']
    prop.value = False
    
    bpy.ops.logic.controller_add( type='PYTHON', name='py_init')
    p.game.controllers['py_init'].text = bpy.data.texts["loadVideo.py"]

    bpy.ops.logic.controller_add( type='PYTHON', name='py_update')
    p.game.controllers['py_update'].text = bpy.data.texts["updateVideo.py"]

    bpy.ops.logic.sensor_add( type='ALWAYS', name='init' )
    p.game.sensors[ 'init' ].link( p.game.controllers['py_init'] )
    
    bpy.ops.logic.sensor_add( type='ALWAYS', name='update' )
    p.game.sensors[ 'update' ].link( p.game.controllers['py_update'] )
    p.game.sensors[ 'update' ].use_pulse_true_level = True
    
    return p

def create_text( node, bevel_depth = 0.1, bevel_resolution = 1, extrude = 0.1 ):
    
    global font
    
    if 'mat_text' not in bpy.data.materials: 
        material = bpy.data.materials.new( name="mat_text" )
        for m in bpy.data.materials:
            slot = m.texture_slots[0]
        set_material_options( material, slot )
    mat_text = bpy.data.materials[ 'mat_text' ]
    
    
    # Create TextCurve object
    bpy.ops.object.text_add(
        location=(0, 0.5, 0),
        rotation=(0, 0, 0))
    
    ob = bpy.context.object
    #ob.name = 'Text1'
    # TextCurve attributes
    ob.data.name = 'TextData'
    ob.data.body = node.text
    #fnt = bpy.data.fonts.load('bpy.path.abspath( '//'+'')
    if font != 0:
        ob.data.font = font
        
    ob.data.align = 'CENTER'
    # Inherited Curve attributes
    #ob.data.bevel_depth = bevel_depth
    #ob.data.bevel_resolution = bevel_resolution
    #ob.data.extrude = extrude
    #setMaterial(ob, red)
    bpy.ops.object.convert( target='MESH', keep_original=False )
    
    size = 0.2
    if 'size' in node.attrib:
        size = float( node.attrib['size'] )
    ob.scale = ( size, size, size )
        
    if 'x' in node.attrib:
        ob.location.x = float( node.attrib['x'] )
    if 'y' in node.attrib:
        ob.location.y = float( node.attrib['y'] )
    
    ob.data.materials.append( mat_text )
    
    return ob
    
def preparePath( src ):
    lastslash = src.rfind("/")
    folder = "//"
    filename = p.attrib["src"]
    if lastslash > -1:
        folder = "//" + src[ 0:lastslash+1 ]
        filename = filename[ lastslash+1: ]
    return folder, filename

def appendSlide():
    
    global slides
    global slideIndex
    global currentimg
    global currentvid
    global currenttxt

    global general_timer
    global currenttimer
    
    newslide = 0
    
    if currentimg != 0 or currentvid != 0 or currenttxt != 0:
        
        if currentimg != 0:
            currentimg.name = "slide_%04d" % slideIndex
            for t in currenttxt:
                t.select = False
                t.parent = currentimg
                t.location.z = 0.01
            newslide = currentimg
            slides.append( currentimg )
            slideIndex += 1
            
        elif currentvid != 0:
            currentvid.name = "slide_%04d" % slideIndex
            for t in currenttxt:
                t.select = False
                t.parent = currentimg
                t.location.z = 0.01
            newslide = currentvid
            slides.append( currentvid )
            slideIndex += 1
            
        elif len( currenttxt ) > 0:
            ct = currenttxt[ 0 ]
            ct.name = "slide_%04d" % slideIndex
            currenttxt.remove( ct )
            for t in currenttxt:
                t.select = False
                t.parent = ct
            newslide = ct
            slides.append( ct )
            slideIndex += 1
    
    if newslide != 0:
        bpy.context.scene.objects.active = newslide
        bpy.ops.object.game_property_new(type='FLOAT', name="duration")
        prop = newslide.game.properties['duration']
        if currenttimer != 0:
            prop.value = currenttimer
        else:
            prop.value = general_timer
        
    currenttimer = 0
    currentimg = 0
    currentvid = 0
    currenttxt = []
    
    
    
# ### MAIN ###

# Cleaning the blend file from orphan images, movies, etc...
for f in range( 0, len( bpy.data.fonts ) ):
   if f != 0:
       bpy.data.fonts[ f ].user_clear()

for mat in bpy.data.materials:
    if mat.name[0:5] != 'keep-':
        mat.user_clear()
        print ('Removed unused material: ', mat.name)

for texture in bpy.data.textures:
    if texture.name[0:5] != 'keep-':
        texture.user_clear()
        print ('Removed unused texture: ', texture.name)
        
for image in bpy.data.images:
    if image.name[0:5] != 'keep-':
        image.user_clear()
        print ('Removed unused image: ', image.name)
        
for movieclip in bpy.data.movieclips:
    if movieclip.name[0:5] != 'keep-':
        movieclip.user_clear()
        print ('Removed unused movie: ', movieclip.name)
    
slides = []
page = ET.parse( bpy.path.abspath( '//' + XML_PRESENTATION_FILE ) )

general_timer = 2
font = 0
slideIndex = 0
# better xml parsing
currenttimer = 0
currentslide = 0
currentimg = 0
currentvid = 0
currenttxt = []


for p in page.getiterator():
    
    if p.tag == "presentation":
        if 'timer' in p.attrib:
            general_timer = float( p.attrib[ 'timer' ] )
    
    if p.tag == "slide":
        print( "start new slide" )
        appendSlide()
        if 'timer' in p.attrib:
            currenttimer = float( p.attrib[ 'timer' ] )
         
    if p.tag == "img":
        print( "loading image: ", p.attrib["src"] )
        d, f = preparePath( p.attrib["src"] )
        currentimg = img2plane( d, f )
        if 'timer' in p.attrib:
            currenttimer = float( p.attrib[ 'timer' ] )

    if p.tag == "text":
        print( "loading text: ", p )
        currenttxt.append( create_text( p ) )
        if 'timer' in p.attrib:
            currenttimer = float( p.attrib[ 'timer' ] )
 
    if p.tag == "video":
        print( "loading video: ", p.attrib["src"] )
        d, f = preparePath( p.attrib["src"] )
        currentvid = video2plane( d, f )
        if 'timer' in p.attrib:
            currenttimer = float( p.attrib[ 'timer' ] )

appendSlide()


'''
for p in page.getiterator():
    
    if p.tag == "img":
        print( "loading image: ", p.attrib["src"] )
        d, f = preparePath( p.attrib["src"] )
        s = img2plane( d, f )
        s.name = "slide_" + str( slideIndex )
        slides.append( s )
        slideIndex += 1
        
    if p.tag == "text":
        print( "loading text: ", p )
        s = create_text( p.text )
        s.name = "slide_" + str( slideIndex )
        slides.append( s )
        slideIndex += 1
 
    if p.tag == "video":
        print( "loading video: ", p.attrib["src"] )
        s = video2plane( "//", p.attrib["src"] )
        s.name = "slide_" + str( slideIndex )
        slides.append( s )
        slideIndex += 1
'''
# rearrange sildes
offsetx = 0
for s in slides:
    # print( "moving", s.name )
    s.location.x = offsetx * 2
    offsetx += 1

'''
for i in bpy.data.images:
    print( i )
for i in bpy.data.movieclips:
    print( i )
'''
