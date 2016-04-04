from ipywidgets import widgets
from IPython.core.magics.namespace import NamespaceMagics
from IPython import get_ipython
import numpy as np
from types import ModuleType, FunctionType
from IPython.display import HTML
from pandas import DataFrame
import matplotlib.pyplot as plt
import os
import pickle
from time import sleep

__all__ = ['workspace']


class workspace(object):

    """Print the workspace of an Ipython notebook.

    # Define a workspace :
    from wksp import workspace
    wk = workspace()

    # In a new cell, run the ligne above to have a detached workspace :
    wk.detached()

    # Finally, close the workspace :
    wk.close()
    """

    def __init__(self):
        ipython = get_ipython()
        ipython.user_ns_hidden['widgets'] = widgets
        ipython.user_ns_hidden['NamespaceMagics'] = NamespaceMagics
        self._closed = False
        self._namespace = NamespaceMagics()
        self._namespace.shell = ipython.kernel.shell
        self._getVarInfo()
        self._defPyVar = ['int', 'float', 'tuple', 'ndarray', 'list', 'dict', 'matrix']

        # -------------- Workspace panel --------------
        self._tab, self._tablab = self._createTab(widgets.Box(), [])

        # -------------- Setting panel --------------
        # -> Sorting :
        self._Flt_type_w = widgets.Dropdown(description='Type')
        self._Flt_sortBy_w = widgets.Dropdown(description='Sort by', options=['Name', 'Type', 'Size'], margin=5)
        self._Flt_order_w = widgets.ToggleButtons(options=['Ascending', 'Descending'], margin=5)
        self._Flt_zs_w = widgets.ToggleButtons(options=['True', 'False'], selected_label='True', description='Default system variables')
        self._Flt_apply_w = widgets.Button(description='Apply', button_style='success', margin=20)
        self._Flt_def_w = widgets.Button(description='Default', button_style='info', margin=20)
        Flt_button = widgets.HBox(children=[self._Flt_apply_w, self._Flt_def_w])
        self._Flt_apply_w.on_click(self._fill)
        self._Flt_cat_w = widgets.VBox(
            children=[self._Flt_type_w, self._Flt_sortBy_w, self._Flt_order_w, self._Flt_zs_w, Flt_button])

        # -> Load/save:
        self._LS_choice_w = widgets.ToggleButtons(options=['Save', 'Load'])
        self._LS_path_w = widgets.Text(description='Path', width=250, placeholder='Leave empty for current directory', margin=5)
        self._LS_file_w = widgets.Text(description='File', width=250, placeholder='Ex : myfile without ""', margin=5)
        self._LS_var_w = widgets.Text(description='Variables', width=250, placeholder='Ex : "x, y, z"', margin=5)
        self._LS_apply_w = widgets.Button(description='Apply', button_style='success', margin=20)
        self._LS_clear_w = widgets.Button(description='Clear', button_style='info', margin=20)
        self._LS_apply_w.on_click(self._loadsave)
        LS_button = widgets.HBox(children=[self._LS_apply_w, self._LS_clear_w])
        self._LS_txt = widgets.Latex(value='', color='#A1B56C', margin=5, font_weight='bold', visible=False)
        self._LS_cat_w = widgets.VBox(
            children=[self._LS_choice_w, self._LS_path_w, self._LS_file_w, self._LS_var_w, self._LS_txt, LS_button])

        # -> Operation :
        self._Op_ass_w = widgets.Text(description='Assign', width=300, placeholder='variable')
        self._Op_to_w = widgets.Text(description='To', width=300, placeholder='var/expression')
        self._Op_apply_w = widgets.Button(description='Apply', button_style='success', margin=20)
        self._Op_clear_w = widgets.Button(description='Clear', button_style='info', margin=20)
        Op_button = widgets.HBox(children=[self._Op_apply_w, self._Op_clear_w])
        self._Op_apply_w.on_click(self._assignVar)
        self._Op_clear_w.on_click(self._clearVar)
        self._Op_cat_w = widgets.VBox(children=[self._Op_ass_w, self._Op_to_w, Op_button])

        # ///// CAT OBJECTS \\\\\
        self._subAcc = widgets.Accordion()
        self._subAcc.children = [self._Flt_cat_w, self._LS_cat_w, self._Op_cat_w]
        [self._subAcc.set_title(k, n) for k, n in enumerate(['Sorting', 'Save/Load','Variables'])]

        # -------------- Shell --------------
        self._Sh_ass_w = widgets.Textarea(background_color='#000000', color='#ffffff', placeholder='Enter text', height=500, font_size=15)
        self._Sh_apply_w = widgets.Button(description='Apply', button_style='success', margin=20)
        self._Sh_clear_w = widgets.Button(description='Clear', button_style='info', margin=20)
        sh_button = widgets.HBox(children=[self._Sh_apply_w, self._Sh_clear_w])
        self._Sh_apply_w.on_click(self._execShell)
        self._Sh_clear_w.on_click(self._clearShell)
        self._Sh_cat_w = widgets.VBox(children=[self._Sh_ass_w, sh_button])

        # -------------- Vizu panel --------------
        # Create visualization :
        self._Vi_type_w = widgets.Dropdown(description='Type')
        self._Vi_cat_w = widgets.VBox(children=[self._Vi_type_w])

        # Create Tab :
        self._popout = widgets.Tab()
        self._popout.description = "Workspace"
        self._popout.button_text = self._popout.description
        self._popout.children = [self._tab, self._subAcc, self._Vi_cat_w, self._Sh_cat_w]
        [self._popout.set_title(k, n) for k, n in enumerate(['Workspace', 'Settings', 'Visualization', 'Shell'])]
        self._popout._dom_classes = ['inspector']

        self._ipython = ipython
        self._ipython.events.register('post_run_cell', self._fill)

    def _fill(self, *arg):
        """Fill self with variable information."""
        # Get var, name, size and type :
        self._getVarInfo()
        # Filt variables :
        vName, vType, vSize = self._FiltVar()
        # Get value :
        v = [self._namespace.shell.user_ns[name] for name in vName]
        # Set unique type to list :
        _typet = list(set(self._vartypes))
        _typet.sort()
        self._Flt_type_w.options = ['All'] + _typet

        # Fill tab :
        self._tablab.value = '<table class="table table-bordered table-striped"><tr><th>Name</th><th>Type</th><th>Value</th><th>Size</th</tr><tr><td>' + \
        '</td></tr><tr><td>'.join(['{0}</td><td>{1}</td><td>{2}<td>{3}</td>'.format(vName[k], vType[k], str(val), vSize[k]) for k, val in enumerate(v)]) + \
        '</td></tr></table>'

        st = self._popout.get_state()
        st['selected_index'] = 0
        st = self._popout.set_state(st)

    def _getVarName(self):
        """Get variables names"""
        names = self._namespace.who_ls()
        names.sort()
        return names

    def _getVarTypes(self, name):
        """Get variables names"""
        # Get name :
        var = self._namespace.shell.user_ns
        # Get types :
        return [type(var[n]).__name__.lower() for n in name]

    def _getVarSizes(self, name):
        """Get variables sizes"""
        valSize = []
        for k, vn in enumerate(name):
            v = self._namespace.shell.user_ns[vn]
            # Get shape :
            try:
                try:
                    try:
                        valSize.append(str(v.shape))
                    except:
                        valSize.append(str(np.size(v)))
                except:
                    valSize.append(str(len(v)))
            except:
                valSize.append('')
        return valSize

    def _getVarInfo(self):
        """Get ipython variables names, types and shape"""
        self._varnames = self._getVarName()                 # Get name
        self._vartypes = self._getVarTypes(self._varnames)  # Get types
        self._varsizes = self._getVarSizes(self._varnames)  # Get sizes

    def _FiltVar(self):
        """Filt, sort variables"""
        vName, vType, vSize = self._varnames, self._vartypes, self._varsizes
        # Get type :
        typ = self._Flt_type_w.get_state()['selected_label']
        if typ != 'All':
            fnames = [k for num, k in enumerate(vName) if vType[num] == typ]
        else:
            fnames = vName
        ftypes = self._getVarTypes(fnames)
        fsize = self._getVarSizes(fnames)
        # Fill a Dataframe :
        pdd = DataFrame({'Name': fnames, 'Size': fsize, 'Type': ftypes})
        # Get sort by :
        sby = self._Flt_sortBy_w.get_state()['selected_label']
        # Get ascend/descend :
        order = self._Flt_order_w.get_state()['selected_label']
        if order == 'Ascending':
            order = True
        else:
            order = False
        pdd = pdd.sort_values(sby, ascending=order)
        pdd = pdd.set_index([list(np.arange(pdd.shape[0]))])
        # Hide empty size variables :
        if eval(self._Flt_zs_w.get_state()['selected_label']):
            emptyL = []
            for num, v in enumerate(ftypes):
                emptyL.extend([num for t in self._defPyVar if v == t])
            pdd = pdd.iloc[emptyL]

        return list(pdd['Name']), list(pdd['Type']), list(pdd['Size'])

    def _assignVar(self, *arg):
        """Assign new value to variable"""
        varname = self._Op_ass_w.value
        vartp = self._Op_to_w.value
        self._namespace.shell.user_ns[varname] = eval(vartp)
        self._fill()

    def _clearVar(self, *arg):
        """Clear assign variables"""
        self._Op_ass_w.value = ''
        self._Op_to_w.value = ''

    def _execShell(self, *arg):
        """Execute a shell of commands"""
        exec(self._Sh_ass_w.value)
        self._fill()

    def _clearShell(self, *arg):
        """Clear a shell of commands"""
        self._Sh_ass_w.value = ''

    def _loadsave(self, *arg):
        """Save or load variables"""
        self._LS_txt.visible = False
        # Get path :
        path = self._LS_path_w.value
        # Get file name :
        file = self._LS_file_w.value
        savefile = os.path.join(path, file)+'.pickle'
        # Get if it's load or save :
        ldsv = self._LS_choice_w.get_state()['selected_label']
        if ldsv == 'Save':
            # Get variables :
            var = self._LS_var_w.value
            if var == '':  # Save all variables
                varname = self._getVarName()
            else:          # Save defined variables
                varname = var.replace(' ', '').split(sep=',')
            data = {name: self._namespace.shell.user_ns[name] for name in varname}
            # Save :
            with open(savefile, 'wb') as f:
                pickle.dump(data, f)
            # Confirmation text :
            self._LS_txt.value = savefile+' saved :D'
            self._LS_txt.visible = True
        elif ldsv == 'Load':
            # Load data :
            with open(savefile, "rb") as f:
                data = pickle.load(f)
            # Add variables to workspace :
            for k in data.keys():
                self._namespace.shell.user_ns[k] = data[k]
            self._fill()
            # Confirmation text :
            self._LS_txt.value = savefile+' loaded :D'
            self._LS_txt.visible = True
        sleep(3)
        self._LS_txt.visible = False

    @staticmethod
    def _createTab(var, label):
        """Create each tab of the table"""
        var = widgets.Box()
        # var._dom_classes = ['inspector']
        var.background_color = '#fff'
        var.border_color = '#ccc'
        var.border_width = 1
        var.border_radius = 5
        var.overflow_y = 'scroll'
        var.overflow_x = 'scroll'
        var.height = 700
        label = widgets.HTML(value='Not hooked')
        var.children = [label]
        return var, label

    def _ipython_display_(self):
        """Called when display() or pyout is used to display the variable
        Inspector.
        """
        self._popout._ipython_display_()

    def detached(self):
        """Put the workspace in a detached resizable window"""
        jav = """
        <script type="text/Javascript">
        $('div.inspector')
            .detach()
            .prependTo($('body'))
            .css({
                'z-index': 999,
                'left':5,
                'top':110,
                'min-width': 300,
                'width': 370,
                position: 'fixed',
                'box-shadow': '5px 5px 12px -3px black',
                opacity: 0.9
            })
            .draggable().resizable();
        </script>
        """
        return HTML(jav)

    def attached(self):
        """Put the wokspace in a notebook cell"""
        self.close()
        self.__init__()

    def close(self):
        """Close and remove hooks."""
        if not self._closed:
            self._ipython.events.unregister('post_run_cell', self._fill)
            self._popout.close()
            self._closed = True
