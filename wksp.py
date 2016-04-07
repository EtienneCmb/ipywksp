from ipywidgets import widgets
from IPython.core.magics.namespace import NamespaceMagics
from IPython import get_ipython
import numpy as np
from types import ModuleType, FunctionType
from IPython.display import HTML, Javascript
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
import os
import pickle
from time import sleep

__all__ = ['workspace']


class workspace(object):

    """Print the workspace of an Ipython notebook.

    # Define a workspace :
    from wksp import workspace
    wk = workspace()    # define workspace
    wk.display()        # display workspace

    # Finally, close the workspace :
    wk.close()          # close workspace
    """
    instance = None

    def __init__(self):
        """Public constructor."""
        if workspace.instance is not None:
            raise Exception("""Only one instance of the workspace can exist at a 
                time.  Call close() on the active instance before creating a new instance.
                If you have lost the handle to the active instance, you can re-obtain it
                via `workspace.instance`.""")
        # /////////////// SYSTEM VARIABLES \\\\\\\\\\\\\\\\\
        ipython = get_ipython()
        ipython.user_ns_hidden['widgets'] = widgets
        ipython.user_ns_hidden['NamespaceMagics'] = NamespaceMagics
        self._closed = False
        self._namespace = NamespaceMagics()
        self._namespace.shell = ipython.kernel.shell
        self._getVarInfo()
        self._defPyVar = ['int', 'float', 'tuple', 'ndarray', 'list', 'dict',
                          'matrix', 'set', 'dataframe', 'series']
        self._ipython = ipython
        self._ipython.events.register('post_run_cell', self._fill)

        # /////////////// WORKSPACE \\\\\\\\\\\\\\\\\
        self._tab, self._tablab = self._createTab(widgets.Box(), [])

        # /////////////// SETTINGS \\\\\\\\\\\\\\\\\
        # -> Sorting :
        self._wFlt_type = widgets.Dropdown(description='Type')
        self._wFlt_sortBy = widgets.Dropdown(description='Sort by', options=['Name', 'Type', 'Size'])
        self._wFlt_order = widgets.ToggleButtons(options=['Ascending', 'Descending'], margin=5)
        self._wFlt_defSys = widgets.ToggleButtons(options=['True', 'False'], selected_label='True', description='Default system variables')
        # Choice of columns
        self._wFlt_nameChk = widgets.Checkbox(description='Name', value=True)
        self._wFlt_typeChk = widgets.Checkbox(description='Type', value=True)
        self._wFlt_valChk = widgets.Checkbox(description='Value', value=True)
        self._wFlt_sizeChk = widgets.Checkbox(description='Size', value=True)
        Flt_columns = widgets.HBox(description='Columns', children=[self._wFlt_nameChk, self._wFlt_typeChk, self._wFlt_valChk, self._wFlt_sizeChk])
        # Apply/default button :
        _wFlt_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _wFlt_def = widgets.Button(description='Default', button_style='info', margin=20)
        Flt_button = widgets.HBox(children=[_wFlt_apply, _wFlt_def])
        _wFlt_apply.on_click(self._fill)
        _wFlt_def.on_click(self._defaultSort)
        _wFlt_cat = widgets.VBox(children=[self._wFlt_type, self._wFlt_sortBy, self._wFlt_order, self._wFlt_defSys, Flt_columns, Flt_button])

        # -> Load/save:
        self._wLS_choice = widgets.ToggleButtons(options=['Save', 'Load'])
        self._wLS_path = widgets.Text(description='Path', width=250, placeholder='Leave empty for current directory', margin=5)
        self._wLS_file = widgets.Text(description='File', width=250, placeholder='Ex : myfile', margin=5)
        self._wLS_var = widgets.Text(description='Variables', width=250, placeholder='Ex : "x, y, z"', margin=5)
        _wLS_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _wLS_clear = widgets.Button(description='Clear', button_style='info', margin=20)
        _wLS_apply.on_click(self._loadsave)
        _wLS_clear.on_click(self._clearLS)
        LS_button = widgets.HBox(children=[_wLS_apply, _wLS_clear])
        self._wLS_txt = widgets.Latex(value='', color='#A1B56C', margin=5, font_weight='bold', visible=False)
        _LS_cat = widgets.VBox(children=[self._wLS_choice, self._wLS_path, self._wLS_file, self._wLS_var, self._wLS_txt, LS_button])

        # -> Operation :
        self._wOp_ass = widgets.Text(description='Assign', width=300, placeholder='variable')
        self._wOp_to = widgets.Text(description='To', width=300, placeholder='var/expression')
        _wOp_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _wOp_clear = widgets.Button(description='Clear', button_style='info', margin=20)
        Op_button = widgets.HBox(children=[_wOp_apply, _wOp_clear])
        _wOp_apply.on_click(self._assignVar)
        _wOp_clear.on_click(self._clearVar)
        _Op_cat_w = widgets.VBox(children=[self._wOp_ass, self._wOp_to, Op_button])

        # -> CAT :
        _subAccSt = widgets.Accordion(font_weight='bold')
        _subAccSt.children = [_wFlt_cat, _LS_cat, _Op_cat_w]
        [_subAccSt.set_title(k, n) for k, n in enumerate(['Sorting', 'Save/Load','Variables'])]

        # /////////////// VISUALIZATION \\\\\\\\\\\\\\\\\
        # -> Variable and function for plotting :
        self._wVi_var = widgets.Text(description='Variables', width=250, placeholder='Ex : x')
        self._wVi_fcn = widgets.Dropdown(description='Function', options=['plot', 'imshow'])
        # -> Plot settings :
        self._wVi_tit = widgets.Text(description='Title', width=250, placeholder='Ex : My title')
        self._wVi_xlab = widgets.Text(description='X label', width=250, placeholder='Ex : time')
        self._wVi_ylab = widgets.Text(description='Y label', width=250, placeholder='Ex : Amplitude')
        self._wVi_cmap = widgets.Text(description='Colormap', width=250, placeholder='Ex : viridis')
        self._wVi_kwarg = widgets.Text(description='kwargs', width=250, placeholder='Ex : {}')
        _ViS_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _ViS_clear = widgets.Button(description='Clear', button_style='info', margin=20)
        _ViS_apply.on_click(self._plotVar)
        _ViS_clear.on_click(self._clearPlot)
        ViS_button = widgets.HBox(children=[_ViS_apply, _ViS_clear])
        ViS_box = widgets.VBox(
            children=[self._wVi_var, self._wVi_fcn, self._wVi_tit, self._wVi_xlab, self._wVi_ylab,
                      self._wVi_cmap, self._wVi_kwarg, ViS_button])

        # -> Save the figure :
        self._wVi_path = widgets.Text(description='Path', width=250, placeholder='Leave empty for current directory')
        self._wVi_file = widgets.Text(description='File', width=250, placeholder='Ex : myfile')
        self._wVi_ext = widgets.Dropdown(description='Ext', width=10, options=['.png', '.tif', '.jpg'])
        self._wVi_dpi = widgets.Text(description='dpi', width=50, placeholder='100')
        _ViQuality = widgets.HBox(children=[self._wVi_ext, self._wVi_dpi])
        _Vi_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _Vi_clear = widgets.Button(description='Clear', button_style='info', margin=20)
        _Vi_apply.on_click(self._saveFig)
        _Vi_clear.on_click(self._clearFig)
        ViApp_button = widgets.HBox(children=[_Vi_apply, _Vi_clear])
        self._wVi_txt = widgets.Latex(value='', color='#A1B56C', margin=5, font_weight='bold', visible=False)
        _Vi_cat_w = widgets.VBox(children=[self._wVi_path, self._wVi_file, _ViQuality, self._wVi_txt, ViApp_button])

        # -> CAT :
        _subAccVi = widgets.Accordion(font_weight='bold')
        _subAccVi.children = [ViS_box, _Vi_cat_w]
        [_subAccVi.set_title(k, n) for k, n in enumerate(['Settings', 'Save/Load'])]

        # /////////////// SHELL \\\\\\\\\\\\\\\\\
        self._wSh_ass = widgets.Textarea(background_color='#000000', color='#ffffff', placeholder='Enter text', height=500, font_size=15)
        _wSh_apply = widgets.Button(description='Apply', button_style='success', margin=20)
        _Sh_clear = widgets.Button(description='Clear', button_style='info', margin=20)
        sh_button = widgets.HBox(children=[_wSh_apply, _Sh_clear])
        _wSh_apply.on_click(self._execShell)
        _Sh_clear.on_click(self._clearShell)
        _Sh_cat_w = widgets.VBox(children=[self._wSh_ass, sh_button])

        # /////////////// FINAL TAB \\\\\\\\\\\\\\\\\
        self._popout = widgets.Tab(font_weight='bold')
        self._popout.description = "Workspace"
        self._popout.button_text = self._popout.description
        self._popout.children = [self._tab, _subAccSt, _subAccVi, _Sh_cat_w]
        [self._popout.set_title(k, n) for k, n in enumerate(['Workspace', 'Settings', 'Visualization', 'Shell'])]
        self._popout._dom_classes = ['inspector']
        self._closeB = widgets.HTML("""<div id="closeButton" type="button" class="close">&times</div>""")
        self._win = widgets.VBox(children=[self._closeB, self._popout])
        self._closeB._dom_classes = ['closeButton']
        self._win._dom_classes = ['mainWin']

    # /////////////// TABLE \\\\\\\\\\\\\\\\\
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
        self._wFlt_type.options = ['All'] + _typet

        # Fill tab :
        self._htmlTable(vName, vType, v, vSize)

    def _htmlTable(self, vName, vType, v, vSize):
        """"""
        self._tablab.value = """
        <table class="table table-bordered table-striped">
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Value</th>
                <th>Size</th>
            </tr>
            <tr>
                <td>""" + \
                '</td></tr><tr><td>'.join(["{0}</td><td>{1}</td><td>{2}<td>{3}</td>".format(vName[k], vType[k], str(val), vSize[k]) for k, val in enumerate(v)]) + \
                """</td>
            </tr>
        </table>"""

    # /////////////// SETTINGS \\\\\\\\\\\\\\\\\
    # -> Sorting :
    def _FiltVar(self):
        """Filt, sort variables"""
        self._popout.selected_index = 0
        vName, vType, vSize = self._varnames, self._vartypes, self._varsizes
        # Get type :
        typ = self._wFlt_type.get_state()['selected_label']
        if typ != 'All':
            fnames = [k for num, k in enumerate(vName) if vType[num] == typ]
        else:
            fnames = vName
        ftypes = self._getVarTypes(fnames)
        fsize = self._getVarSizes(fnames)
        # Fill a Dataframe :
        pdd = DataFrame({'Name': fnames, 'Size': fsize, 'Type': ftypes})
        # Get sort by :
        sby = self._wFlt_sortBy.get_state()['selected_label']
        # Get ascend/descend :
        order = self._wFlt_order.get_state()['selected_label']
        if order == 'Ascending':
            order = True
        else:
            order = False
        pdd = pdd.sort_values(sby, ascending=order)
        pdd = pdd.set_index([list(np.arange(pdd.shape[0]))])
        # Hide empty size variables :
        if eval(self._wFlt_defSys.get_state()['selected_label']):
            emptyL = []
            for num, v in enumerate(ftypes):
                emptyL.extend([num for t in self._defPyVar if v == t])
            pdd = pdd.iloc[emptyL]

        return list(pdd['Name']), list(pdd['Type']), list(pdd['Size'])

    def _defaultSort(self, *arg):
        """Reset default sorting options"""
        # Get elements states :
        self._wFlt_type.__setattr__('selected_label', 'All')
        self._wFlt_sortBy.__setattr__('selected_label', 'Name')
        self._wFlt_order.__setattr__('selected_label', 'Ascending')
        self._wFlt_defSys.__setattr__('selected_label', 'True')
        self._fill()

    # -> Load/Save variables :
    def _loadsave(self, *arg):
        """Save or load variables"""
        self._wLS_txt.visible = False
        # Get path :
        path = self._wLS_path.value
        # Get file name :
        file = self._wLS_file.value
        savefile = os.path.join(path, file)+'.pickle'
        # Get if it's load or save :
        ldsv = self._wLS_choice.get_state()['selected_label']
        if ldsv == 'Save':
            # Get variables :
            var = self._wLS_var.value
            if var == '':  # Save all variables
                varname = self._getVarName()
            else:          # Save defined variables
                varname = var.replace(' ', '').split(sep=',')
            data = {name: self._namespace.shell.user_ns[name] for name in varname}
            # Save :
            with open(savefile, 'wb') as f:
                pickle.dump(data, f)
            # Confirmation text :
            self._wLS_txt.value = savefile+' saved :D'
            self._wLS_txt.visible = True
        elif ldsv == 'Load':
            # Load data :
            with open(savefile, "rb") as f:
                data = pickle.load(f)
            # Add variables to workspace :
            for k in data.keys():
                self._namespace.shell.user_ns[k] = data[k]
            self._fill()
            # Confirmation text :
            self._wLS_txt.value = savefile+' loaded :D'
            self._wLS_txt.visible = True
        sleep(3)
        self._wLS_txt.visible = False

    def _clearLS(self, *arg):
        """Clear the save and load module"""
        self._wLS_path.value = ''
        self._wLS_file.value = ''
        self._wLS_var.value = ''

    # -> Assign a new value to a variable :
    def _assignVar(self, *arg):
        """Assign new value to variable"""
        varname = self._wOp_ass.value
        vartp = self._wOp_to.value
        self._namespace.shell.user_ns[varname] = eval(vartp)
        self._fill()

    def _clearVar(self, *arg):
        """Clear assign variables"""
        self._wOp_ass.value = ''
        self._wOp_to.value = ''

    # /////////////// VISUALIZATION \\\\\\\\\\\\\\\\\
    def _plotVar(self, *arg):
        """Plot a variable"""
        varname = self._wVi_var.value
        var = self._namespace.shell.user_ns[varname]  # Get variable
        pltfcn = self._wVi_fcn.value  # Plotting function
        tit = self._wVi_tit.value  # title
        xlab = self._wVi_xlab.value  # xlabel
        ylab = self._wVi_ylab.value  # ylabel
        cmap = self._wVi_cmap.value  # cmap
        kwargs = self._wVi_kwarg.value  # kwargs

        if cmap == '':
            cmap = 'viridis'
        if kwargs == '':
            kwargs = '{}'
        plt.set_cmap(cmap)

        pltstr = 'plt.'+pltfcn+'(var, **'+kwargs+')'
        eval(pltstr)
        plt.title(tit), plt.xlabel(xlab), plt.ylabel(ylab)
        self._fig = plt.gcf()
        plt.show()

    def _clearPlot(self, *arg):
        """Clear the save and load module"""
        self._wVi_var.value = ''
        self._wVi_tit.value = ''
        self._wVi_xlab.value = ''
        self._wVi_ylab.value = ''
        self._wVi_cmap.value = ''
        self._wVi_kwarg.value = ''
        self._wVi_fcn.selected_label = 'plot'

    def _saveFig(self, *arg):
        """Save the current figure"""
        path = self._wVi_path.value  # path
        file = self._wVi_file.value  # file
        ext = self._wVi_ext.get_state()['selected_label']  # extension
        dpi = self._wVi_dpi.value  # dpi
        # Fix dpi :
        if dpi == '':
            dpi = 100
        mpl.rc("savefig", dpi=int(dpi))
        self._fig.savefig(path+file+ext, bbox_inches='tight')

    def _clearFig(self, *arg):
        """Clear saving figure elements"""
        self._wVi_path.value = ''
        self._wVi_file.value = ''
        self._wVi_ext.selected_label = '.png'
        self._wVi_dpi.value = ''

    # /////////////// SHELL \\\\\\\\\\\\\\\\\
    def _execShell(self, *arg):
        """Execute a shell of commands"""
        exec(self._wSh_ass.value)
        self._fill()

    def _clearShell(self, *arg):
        """Clear a shell of commands"""
        self._wSh_ass.value = ''

    # /////////////// SYSTEM \\\\\\\\\\\\\\\\\
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
        self._fill()
        try:
            self._win._ipython_display_()
        except:
            workspace.instance = None
            self.__init__()
            self._win._ipython_display_()

    def display(self):
        """"""
        R = """
        $( "#closeButton" ).click(function() {
          //$(".inspector").hide('').fadeOut(1000);
          alert( "Handler for .click() called." );
        });
        """
        Javascript(R)
        if workspace.instance is None:
            workspace.instance = self
            self._ipython_display_()
            return Javascript(self._javaScripts())

    def _javaScripts(self):
        """Execute javascripts"""
        jav = """
        // Detach the main window :
        $('div.mainWin')
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
            }).draggable().resizable().fadeIn(1000);

        // Close the window :
        $( "#closeButton" ).click(function() {
          $(".inspector").hide('').fadeOut(1000);
        });

        // Reduce the window :
        """
        return jav

    def attached(self):
        """Put the wokspace in a notebook cell"""
        self.close()
        self.__init__()

    def close(self):
        """Close and remove hooks."""
        if not self._closed:
            self._ipython.events.unregister('post_run_cell', self._fill)
            self._win.close()
            self._closed = True
            workspace.instance = None
