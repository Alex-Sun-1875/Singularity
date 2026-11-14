import bpy,json
path=r'F:/workspace/Singularity/src/.tools/blender-4.5.15-windows-x64/4.5/datafiles/assets/geometry_nodes/procedural_hair_node_assets.blend'
with bpy.data.libraries.load(path,link=False)as(src,dst):
 print('GROUPS',json.dumps(src.node_groups))
 dst.node_groups=[n for n in src.node_groups if any(s in n for s in ['Curl Hair','Generate Hair','Interpolate Hair','Clump Hair','Set Hair Curve Profile','Frizz Hair'])]
for g in bpy.data.node_groups:
 if any(s in g.name for s in ['Curl Hair','Generate Hair','Interpolate Hair','Clump Hair','Set Hair Curve Profile','Frizz Hair']):
  print('INTERFACE',g.name,json.dumps([{'name':i.name,'id':getattr(i,'identifier',''),'type':getattr(i,'socket_type',''),'in_out':getattr(i,'in_out',''),'default':str(getattr(i,'default_value',''))}for i in g.interface.items_tree if i.item_type=='SOCKET']))
