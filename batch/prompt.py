"""
Submodule with main function to call to launch batch mode.
"""

import os
import PySimpleGUI as sg

from .utils import get_elmt_from_key, create_map, call_auto_map
from .update import update_detection_tab, update_map_tab, update_master_parameters, update_segmentation_tab
from .input import load, extract_files
from .integrity import sanity_check, check_channel_map_integrity, check_detection_parameters
from ..gui.layout import _segmentation_layout, _detection_layout, _input_parameters_layout, _ask_channel_map_layout


def batch_promp() :

    files_values = [[]]


    #LOAD FILES
    files_table = sg.Table(values=files_values, headings=['Filenames'], col_widths=100, max_col_width= 200, def_col_width=100, num_rows= 10, auto_size_columns=False)

    #DIMENSION SANITY
    sanity_progress = sg.ProgressBar(10, size_px=(500,10), border_width=2)
    sanity_check_button = sg.Button(
        'Check', 
        tooltip= "Will check that all files loaded have the same dimension number and that small fish is able to open them.", 
        pad=(10,0))
    sanity_header = sg.Text("Dimension sanity", font=('bold',15), pad=(0,10))
    dimension_number_text = sg.Text("Dimension number : unknown")
    

#########################################
#####   COLUMNS
#########################################

#####   Tabs

    #Input tab
    input_layout = _input_parameters_layout(
        ask_for_segmentation=True,
        is_3D_stack_preset=False,
        time_stack_preset=False,
        multichannel_preset=False,
        do_dense_regions_deconvolution_preset=False,
        do_clustering_preset=False,
        do_Napari_correction=False,
        do_segmentation_preset=False,
    )
    input_layout += [[sg.Button('Ok')]]
    input_tab = sg.Tab("Input", input_layout)

    napari_correction_elmt = get_elmt_from_key(input_tab, key='Napari correction')

    #Maptab
    map_layout = _ask_channel_map_layout(
        shape=(0,1,2,3,4),
        is_3D_stack=True,
        is_time_stack=True,
        multichannel=True,
    )
    last_shape_read = sg.Text("Last shape read : None")
    auto_map = sg.Button("auto-map", disabled=True, pad=(10,0))
    apply_map_button = sg.Button("apply", disabled=True, pad=(10,0), key='apply-map')
    map_layout += [[last_shape_read]]
    map_layout += [[auto_map, apply_map_button]]
    map_tab = sg.Tab("Map", map_layout)

    #Segmentation tab
    segmentation_layout = _segmentation_layout(multichannel=True, cytoplasm_model_preset='cyto3')
    apply_segmentation_button = sg.Button('apply', key='apply-segmentation')
    segmentation_layout += [[apply_segmentation_button]]
    segmentation_tab = sg.Tab("Segmentation", segmentation_layout, visible=False)

    #Detection tab
    detection_layout = _detection_layout(
        is_3D_stack=True,
        is_multichannel=True,
        do_clustering=True,
        do_dense_region_deconvolution=True,
        do_segmentation=True,
    )
    apply_detection_button = sg.Button('apply', key='apply-detection')
    detection_layout += [[apply_detection_button]]
    detection_tab = sg.Tab("Detection", detection_layout, visible=False)

    _tab_group = sg.TabGroup([[input_tab, map_tab, segmentation_tab, detection_tab]], enable_events=True)
    tab_col = sg.Column( #Allow the tab to be scrollable
        [[_tab_group]],
        scrollable=True,
        vertical_scroll_only=True,
        s= (390,390),
        pad=((0,0),(5,5))
        )
    
#####   Launcher

    start_button =sg.Button('Start', button_color= 'green', disabled= True, pad= ((115,5),(0,10)))
    stop_button = sg.Button('Cancel', button_color= 'red', pad= ((5,115),(0,10)))
    batch_progression_bar = sg.ProgressBar(max_value=0, size_px=(340,20), bar_color= ('blue','black'), border_width=2, pad=((15,0),(30,0)))
    mapping_ok_text = sg.Text('Uncorrect mapping', text_color='gray', font='roman 14 bold', pad=((0,0),(100,5)))
    segmentation_ok_text = sg.Text('Uncorrect segmentation settings', font='roman 14 bold', pad=(0,5), text_color='gray', visible=False)
    detection_ok_text = sg.Text('Uncorrect detection settings', text_color='gray', font='roman 14 bold', pad=(0,5))
    output_ok_text = sg.Text('Uncorrect output parameters', text_color='gray', font='roman 14 bold', pad=(0,5))
    current_acquisition_text = sg.Text('0', text_color='gray', font='roman 15 bold', pad= ((150,5),(10,10)))
    total_acquisition_text = sg.Text('/ 0', text_color='gray', font='roman 15 bold', pad= ((5,150),(10,10)))

    launcher_layout = [
        [mapping_ok_text],
        [segmentation_ok_text],
        [detection_ok_text],
        [output_ok_text],
        [batch_progression_bar],
        [current_acquisition_text,total_acquisition_text],
        [start_button, stop_button],
    ]
    launch_col = sg.Column( #Allow the tab to be scrollable
        launcher_layout,
        s= (390,390),
        pad=((3,5),(5,5))
        )

    tab_dict= {
        "Input" : input_tab,
        "Segmentation" : segmentation_tab,
        "Detection" : detection_tab,
        "Map" : map_tab,
    }

#########################################
#####   Window Creation
#########################################

    layout = [
        [sg.Text("Batch Processing", font=('bold',20), pad=((300,0),(0,2)))],
        [sg.Text("Select a folder : "), sg.FolderBrowse(initial_folder=os.getcwd(), key='Batch_folder'), sg.Button('Load')],
        [files_table],
        [sanity_header, sanity_check_button, sanity_progress],
        [dimension_number_text],
        [tab_col, launch_col],
        # [sg.Output(size=(100,10), pad=(30,10))],
    ]

    window = sg.Window("small fish", layout=layout, size= (800,800), auto_size_buttons=True, auto_size_text=True)
    
    #MASTER PARAMETERS
    Master_parameters_dict ={
        '_map' : {},
        '_is_mapping_correct' : False,
        '_is_segmentation_correct' : None, # None : segmentation disabled; Then true/false if enabled
        '_is_detection_correct' : False,
        '_is_output_correct' : False,
    }
    Master_parameters_update_dict = {
        '_is_mapping_correct' : mapping_ok_text,
        '_is_segmentation_correct' : segmentation_ok_text, # None : segmentation disabled; Then true/false if enabled
        '_is_detection_correct' : detection_ok_text,
        '_is_output_correct' : output_ok_text,

    }
    loop = 0
    timeout = 1
    last_shape = None
    

#########################################
#####   Event Loop : break to close window
#########################################

    while True :
        loop +=1
        window = window.refresh()
        event, values = window.read(timeout=timeout)
        napari_correction_elmt.update(disabled=True)
        
        #Welcome message
        if loop == 1 : 
            timeout = None
            print("Welcome to small fish batch analysis. Please start by loading some files and setting parameters.")
        
        batch_folder = values.get('Batch_folder')
        is_multichanel = values.get('multichannel')
        is_3D = values.get('3D stack')
        do_segmentation = values.get('Segmentation')
        do_dense_regions_deconvolution = values.get('Dense regions deconvolution')
        do_clustering = values.get('Cluster computation')

        if type(batch_folder) != type(None)  and event == 'Load':

            files_values, last_shape, dim_number = load(batch_folder)
            files_table.update(values=files_values)
            last_shape_read.update("Last shape read : {0}".format(last_shape))
            dimension_number_text.update("Dimension number : {0}".format(dim_number))
            Master_parameters_dict['_is_mapping_correct'] = False
            Master_parameters_dict['_is_detection_correct'] = False
            update_map_tab(
                tab_elmt=tab_dict.get("Map"),
                is_3D=is_3D,
                is_multichannel=is_multichanel,
                last_shape=last_shape
            )

        elif event == 'Check' :
            filename_list = extract_files(files_values)
            last_shape = sanity_check(
                filename_list=filename_list,
                batch_folder=batch_folder,
                window=window,
                progress_bar=sanity_progress
            )
            if isinstance(last_shape,(tuple,list)) :
                dim_number = len(last_shape)
                dimension_number_text.update("Dimension number : {0}".format(dim_number))
                auto_map.update(disabled=False)
            else :
                dim_number = None
                Master_parameters_dict['_is_mapping_correct'] = False
                Master_parameters_dict['_is_detection_correct'] = False
                dimension_number_text.update("Dimension number : unknown")
                auto_map.update(disabled=True)

            last_shape_read.update("Last shape read : {0}".format(last_shape))
           
        elif event == _tab_group.key or event == 'Ok': #Tab switch in parameters
            update_segmentation_tab(
                tab_elmt=tab_dict.get("Segmentation"),
                segmentation_correct_text= segmentation_ok_text,
                do_segmentation=do_segmentation,
                is_multichannel=is_multichanel,
            )

            update_map_tab(
                tab_elmt=tab_dict.get("Map"),
                is_3D=is_3D,
                is_multichannel=is_multichanel,
                last_shape=last_shape
            )

        elif event == 'auto-map' :
            Master_parameters_dict['_map'] = call_auto_map(
                tab_elmt=tab_dict.get("Map"),
                shape=last_shape,
                is_3D=is_3D,
                is_multichannel=is_multichanel
            )

            Master_parameters_dict['_is_mapping_correct'] = check_channel_map_integrity(
                maping=Master_parameters_dict['_map'],
                shape=last_shape,
                expected_dim=dim_number
                )
            
            if not Master_parameters_dict['_is_mapping_correct'] : Master_parameters_dict['_map'] = {}

        elif event == 'apply-map' :
            
            Master_parameters_dict['_map'] = create_map(
                values=values,
                is_3D=is_3D,
                is_multichannel=is_multichanel,
            )

            Master_parameters_dict['_is_mapping_correct'] = check_channel_map_integrity(
                maping=Master_parameters_dict['_map'],
                shape=last_shape,
                expected_dim=dim_number
                )
            
            if not Master_parameters_dict['_is_mapping_correct'] : Master_parameters_dict['_map'] = {}

        elif event == 'apply-segmentation' : #TODO
            pass
        
        elif event == 'apply-detection' :
            Master_parameters_dict['_is_detection_correct'], values = check_detection_parameters(
                values=values,
                do_dense_region_deconvolution=do_dense_regions_deconvolution,
                do_clustering=do_clustering,
                is_multichannel=is_multichanel,
                is_3D=is_3D,
                map= Master_parameters_dict.get('_map'),
                shape=last_shape
            )
        
        elif event == 'apply-output' : #TODO
            pass

        elif event == "Cancel" :
            print(values)
        
        elif event == None :
            quit()

        #End of loop
        update_master_parameters(
            Master_parameter_dict=Master_parameters_dict,
            update_dict=Master_parameters_update_dict
        )

        update_detection_tab(
                tab_elmt=tab_dict.get("Detection"),
                is_multichannel=is_multichanel,
                is_3D=is_3D,
                do_dense_region_deconvolution=do_dense_regions_deconvolution,
                do_clustering=do_clustering,
                is_mapping_ok=Master_parameters_dict['_is_mapping_correct'],
            )

    window.close()