import ipywidgets.widgets as wdg
from IPython.core.magics.namespace import NamespaceMagics
from IPython.display import HTML, display, Javascript
from IPython import get_ipython

import numpy as np
from pandas import DataFrame
from types import ModuleType, FunctionType
import os
import pickle
from time import sleep

import matplotlib.pyplot as plt
from matplotlib.pylab import mpl

__all__ = ['workspace']


class _createWindow(object):

    """Class to create a window.

    Parameters
    ----------
    children : list, [def : []]
        List of HTML widgets

    title : list, [def : []]
        List of strings for the title of each tab

    kind : string, [def : 'tab]
        Display window as tab (kind='tab) or accordion (kind='acc)

    resizale : bool, [def : True]
        Boolean value to set if the window should be resizable or not

    xscroll : bool, [def : False]
        Boolean value to set if the window should be x-scrollable

    yscroll : bool, [def : False]
        Boolean value to set if the window should be y-scrollable

    win, clo, red, enl, tab, fit : string
        Name to call it in the javascript (jv). Those parameters can be usefull
        if there is multiple windows.
            - win : jv name of the window [def : 't']
            - tab : jv name of the table [def : 'a']
            - fit : jv name of the fitting button [def : 'f']
            - red : jv name of the reduce button [def : 'r']
            - enl : jv name of the enlarge button [def : 'e']
            - clo : jv name of the close button [def : 'c']

    tab_kwargs : dict, [def : {}]
        Any supplementar arguments to pass to the tab is created

    win_kwargs : dict, [def : {}]
        Any supplementar arguments to pass to the window is created
    """

    def __init__(self, children=[], title=[''], kind='tab', resizable=True,
                 xscroll=False, yscroll=False, win='t', clo='c', red='r',
                 enl='e', tab='a', fit='f', tab_kwargs={}, win_kwargs={}):
        # Get variables :
        m = 5
        defStr = '<div id="{0}" type="button" class="close">{1}</div>'
        self._winN = win
        self._tabN = tab
        self._cloN = clo
        self._redN = red
        self._enlN = enl
        self._fitN = fit

        # Define scrolling :
        if xscroll:
            x_scroll = "'scroll'"
        else:
            x_scroll = "'hidden'"
        if yscroll:
            y_scroll = "'scroll'"
        else:
            y_scroll = "'hidden'"
        if xscroll or yscroll:
            self._scrollStr = """
            'overflow': 'auto',
            'overflow-x': """ + x_scroll + """,
            'overflow-y': """ + y_scroll + ", "
        else:
            self._scrollStr = ''

        # Resizable :
        if resizable:
            self._resizable = '.resizable()'
        else:
            self._resizable = ''

        # Create the window :
        if kind.lower() == 'tab':
            self._tab = wdg.Tab(font_weight='bold', children=children,
                                _dom_classes=[tab], **tab_kwargs)
        elif kind.lower() == 'acc':
            self._tab = wdg.Accordion(font_weight='bold', children=children,
                                      _dom_classes=[tab], **tab_kwargs)
        for k in range(len(children)):
            self._tab.set_title(k, title[k])

        # Create toolbar :
        cloW = wdg.HTML(defStr.format(clo, '&times'), margin=m, _dom_classes=[clo])
        redW = wdg.HTML(defStr.format(red, '&#8722'), margin=m, _dom_classes=[red])
        enlW = wdg.HTML(defStr.format(enl, '&#8734'), margin=m, _dom_classes=[enl])
        resW = wdg.HTML(defStr.format(fit, '&#8596'), margin=m, _dom_classes=[fit])
        self._toolbar = wdg.HBox(children=[resW, redW, enlW, cloW], pack='end', align='end', width='100%')

        # Pack toolbar and window
        self._win = wdg.VBox(children=[self._toolbar, self._tab], _dom_classes=[win],
                             visible=False, **win_kwargs, border_radius=5)
        self._display()

    def _ipython_display_(self):
        """Display the ipython widgets"""
        self._win._ipython_display_()

    def _javascript(self):
        """Java scripts for detaching the window and for each button in the toolbar
        """
        jav = """
        // Detach the main window :
        $('div."""+self._winN+"""')
            .detach()
            .prependTo($('body'))
            .css({
                'z-index': 999,
                'left':"0.2%",
                'top':"11%",
                'height': "87%",
                'width': "19.3%",
                'min-width': "19.3%",
                'max-width': "99%",
                'max-height': "87%",
                'min-height':'3%',""" + self._scrollStr + """
                position: 'fixed',
                'box-shadow': '5px 5px 12px -3px black',
                opacity: 1
            })
            .draggable()""" + self._resizable + """
            .fadeIn(700)
            ;
        $('div."""+self._tabN+"""')
            .css({'min-width': "100%"})

        // Get browser and window size :
        var wWin = $(window).width();
        var hWin = $(window).height();
        var wBef = $("."""+self._winN+"""").width();
        var hBef = $("."""+self._winN+"""").height();

        // Close the window :
        $( "#"""+self._cloN+"""" ).attr('title', 'Close')
        $( "#"""+self._cloN+"""" ).click(function() {
          $("."""+self._winN+"""").hide('').fadeOut(1000);
        });

        // Reduce window :
        $( "#"""+self._redN+"""" ).attr('title', 'Reduce')
        var leftWin = "0.2%"
        var tr = 0; // Toggler
        $( "#"""+self._redN+"""" ).click(function() {
            tr = ++tr % 2;
            if (tr == 1) {
                var leftPos = $("."""+self._winN+"""").position().left;
                if (leftPos < wWin/2) {
                    leftWin = "0.2%"
                } else {
                    leftWin = "95%"
                }
                wBef = $("."""+self._winN+"""").width();
                hBef = $("."""+self._winN+"""").height();
                $( "#"""+self._redN+"""" ).attr('title', 'Restore')
                $("."""+self._tabN+"""").hide('').fadeOut(200);
                $('div."""+self._winN+"""')
                    .delay(400)
                    .css({'overflow-y':'', 'overflow-x':''})
                    .animate({
                    'z-index': 999,
                    'left':leftWin,
                    'top':"11%",
                    'min-width': "1%",
                    'width': "5%",
                    'height': "1%",
                    }, 500, function() {
                    // Animation complete.
                    }).resizable("destroy");
            } else if (tr == 0) {
                $( "#"""+self._redN+"""" ).attr('title', 'Reduce')
                $('div."""+self._winN+"""')
                    .css({""" + self._scrollStr + """
                    'z-index': 999,
                    'left':"0.2%",
                    'top':"11%",
                    "height":hBef,
                    "width":wBef,
                    'min-width': "19.3%"})"""+self._resizable+""";
                $("."""+self._tabN+"""").delay(200).show('').fadeIn(1000);
            }
        });

        // Enlarge window :
        $( "#"""+self._enlN+"""" ).attr('title', 'Enlarge')
        var tw = 0; // Toggler
        $( "#"""+self._enlN+"""" ).click(function(e) {
            tw = ++tw % 3;
            if (tw == 2) {
                $( "#"""+self._enlN+"""" ).attr('title', 'Restore')
                $("."""+self._tabN+"""").show('').fadeIn(1000);
                $('div."""+self._winN+"""')
                    .animate({
                    'width': "99%",
                    'height': "87%",
                    }, 500, "linear", function() {
                    // Animation complete.
                    });
            } else if (tw == 1) {
                $( "#"""+self._enlN+"""" ).attr('title', 'Full screen')
                $("."""+self._tabN+"""").show('').fadeIn(1000);
                $('div."""+self._winN+"""')
                    .animate({
                    'width': "50%",
                    'height': "60%",
                    }, 500, function() {
                    // Animation complete.
                    });
            } else if (tw == 0) {
                $( "#"""+self._enlN+"""" ).attr('title', 'Enlarge')
                $("."""+self._tabN+"""").show('').fadeIn(1000);
                $('div."""+self._winN+"""').css({"width":"", "height":""});
            }
        });

        // Force to fit to the notebook :
        $( "#"""+self._fitN+"""" ).attr('title', 'Fit to the notebook')
        var tf = 0; // Toggler
        $( "#"""+self._fitN+"""" ).click(function() {
            tf = ++tf % 2;
            if (tf == 1) {
                $( "#"""+self._fitN+"""" ).attr('title', 'Auto ajust')
                $("."""+self._tabN+"""").show('').fadeIn(1000);
                $('div."""+self._winN+"""')
                    .animate({
                    'z-index': 999,
                    'left':"0.2%",
                    'top':"11%",
                    'height': "87%",
                    'width': "19.3%",
                    }, 500, function() {
                    // Animation complete.
                    });
            } else if (tf == 0) {
                $("."""+self._tabN+"""").show('').fadeIn(1000);
                $('div."""+self._winN+"""')
                    .css({"width":"",""" + \
                            self._scrollStr+""""height":"", "width":"", 'min-width': "19.3%"});
            }
        });
        """
        return jav

    def _display(self):
        """Subfunction to display the window and detach it"""
        self._ipython_display_()
        sleep(0.5)
        display(Javascript(self._javascript()))

    def display(self):
        """Display the already created window"""
        display(Javascript("""$('div."""+self._winN+"""').show('').fadeIn(1000)"""))


class workspace(_createWindow):

    """Print the workspace of an Ipython notebook.

    # Define a workspace :
    from wksp import workspace
    wk = workspace()    # define workspace
    wk.display()        # display workspace

    # Finally, close the workspace :
    wk.close()          # close workspace
    """

    def __init__(self):
        """Public constructor."""

        # /////////////// SYSTEM VARIABLES \\\\\\\\\\\\\\\\\
        ipython = get_ipython()
        ipython.user_ns_hidden['widgets'] = wdg
        ipython.user_ns_hidden['NamespaceMagics'] = NamespaceMagics
        self._namespace = NamespaceMagics()
        self._namespace.shell = ipython.kernel.shell
        self._getVarInfo()
        self._defPyVar = ['int', 'float', 'tuple', 'ndarray', 'list', 'dict',
                          'matrix', 'set', 'dataframe', 'series', 'str']
        self._ipython = ipython
        self._ipython.events.register('post_run_cell', self._fill)

        # /////////////// WORKSPACE \\\\\\\\\\\\\\\\\
        _tab = wdg.Box()
        _tab.background_color = '#fff'
        _tab.border_color = '#ccc'
        _tab.border_width = 1
        _tab.border_radius = 5
        self._tablab = wdg.HTML(value='Not hooked')
        _tab.children = [self._tablab]

        # /////////////// SETTINGS \\\\\\\\\\\\\\\\\
        # -> Sorting :
        self._wFlt_type = wdg.Dropdown(description='Type')
        self._wFlt_sortBy = wdg.Dropdown(description='Sort by', options=['Name', 'Type', 'Size'])
        self._wFlt_order = wdg.ToggleButtons(options=['Ascending', 'Descending'], margin=5)
        self._wFlt_defSys = wdg.ToggleButtons(options=['True', 'False'], selected_label='True', description='Default system variables')
        # Choice of columns
        self._wFlt_nameChk = wdg.Checkbox(description='Name', value=True)
        self._wFlt_typeChk = wdg.Checkbox(description='Type', value=True)
        self._wFlt_valChk = wdg.Checkbox(description='Value', value=True)
        self._wFlt_sizeChk = wdg.Checkbox(description='Size', value=True)
        Flt_columns = wdg.HBox(description='Columns', children=[self._wFlt_nameChk, self._wFlt_typeChk, self._wFlt_valChk, self._wFlt_sizeChk])
        # Apply/default button :
        _wFlt_apply = wdg.Button(description='Apply', button_style='success', margin=20)
        _wFlt_def = wdg.Button(description='Default', button_style='info', margin=20)
        Flt_button = wdg.HBox(children=[_wFlt_apply, _wFlt_def])
        _wFlt_apply.on_click(self._fill)
        _wFlt_def.on_click(self._defaultSort)
        _wFlt_cat = wdg.VBox(children=[self._wFlt_type, self._wFlt_sortBy, self._wFlt_order, self._wFlt_defSys, Flt_columns, Flt_button])

        # -> Load/save:
        self._wLS_choice = wdg.ToggleButtons(options=['Save', 'Load'])
        self._wLS_path = wdg.Text(description='Path', width=250, placeholder='Leave empty for current directory', margin=5)
        self._wLS_file = wdg.Text(description='File', width=250, placeholder='Ex : myfile', margin=5)
        self._wLS_var = wdg.Text(description='Variables', width=250, placeholder='Ex : "x, y, z". Empty save all visible variables', margin=5)
        _wLS_apply = wdg.Button(description='Apply', button_style='success', margin=20)
        _wLS_clear = wdg.Button(description='Clear', button_style='info', margin=20)
        _wLS_apply.on_click(self._loadsave)
        _wLS_clear.on_click(self._clearLS)
        LS_button = wdg.HBox(children=[_wLS_apply, _wLS_clear])
        self._wLS_txt = wdg.Latex(value='', color='#A1B56C', margin=5, font_weight='bold', visible=False)
        _LS_cat = wdg.VBox(children=[self._wLS_choice, self._wLS_path, self._wLS_file, self._wLS_var, self._wLS_txt, LS_button])

        # -> Operation :
        self._wOp_ass = wdg.Text(description='Assign', width=300, placeholder='variable')
        self._wOp_to = wdg.Text(description='To', width=300, placeholder='var/expression')
        _wOp_apply = wdg.Button(description='Apply', button_style='success', margin=20)
        _wOp_clear = wdg.Button(description='Clear', button_style='info', margin=20)
        Op_button = wdg.HBox(children=[_wOp_apply, _wOp_clear])
        _wOp_apply.on_click(self._assignVar)
        _wOp_clear.on_click(self._clearVar)
        _Op_cat_w = wdg.VBox(children=[self._wOp_ass, self._wOp_to, Op_button])

        # -> CAT :
        _subAccSt = wdg.Accordion(font_weight='bold')
        _subAccSt.children = [_wFlt_cat, _LS_cat, _Op_cat_w]
        [_subAccSt.set_title(k, n) for k, n in enumerate(['Sorting', 'Save/Load','Variables'])]

        # /////////////// VISUALIZATION \\\\\\\\\\\\\\\\\
        # -> Variable and function for plotting :
        self._wVi_var = wdg.Text(description='Variables', width=250, placeholder='Ex : x')
        self._wVi_fcn = wdg.Dropdown(description='Function', options=['plot', 'imshow'])
        # -> Plot settings :
        self._wVi_tit = wdg.Text(description='Title', width=250, placeholder='Ex : My title')
        self._wVi_xlab = wdg.Text(description='X label', width=250, placeholder='Ex : time')
        self._wVi_ylab = wdg.Text(description='Y label', width=250, placeholder='Ex : Amplitude')
        self._wVi_cmap = wdg.Text(description='Colormap', width=250, placeholder='Ex : viridis')
        self._wVi_kwarg = wdg.Text(description='kwargs', width=250, placeholder='Ex : {}')
        _ViS_apply = wdg.Button(description='Apply', button_style='success', margin=20)
        _ViS_clear = wdg.Button(description='Clear', button_style='info', margin=20)
        _ViS_apply.on_click(self._plotVar)
        _ViS_clear.on_click(self._clearPlot)
        ViS_button = wdg.HBox(children=[_ViS_apply, _ViS_clear])
        ViS_box = wdg.VBox(
            children=[self._wVi_var, self._wVi_fcn, self._wVi_tit, self._wVi_xlab, self._wVi_ylab,
                      self._wVi_cmap, self._wVi_kwarg, ViS_button])

        # -> Save the figure :
        self._wVi_path = wdg.Text(description='Path', width=250, placeholder='Leave empty for current directory')
        self._wVi_file = wdg.Text(description='File', width=250, placeholder='Ex : myfile')
        self._wVi_ext = wdg.Dropdown(description='Ext', width=10, options=['.png', '.tif', '.jpg'])
        self._wVi_dpi = wdg.Text(description='dpi', width=50, placeholder='100')
        _ViQuality = wdg.HBox(children=[self._wVi_ext, self._wVi_dpi])
        _Vi_apply = wdg.Button(description='Apply', button_style='success', margin=20)
        _Vi_clear = wdg.Button(description='Clear', button_style='info', margin=20)
        _Vi_apply.on_click(self._saveFig)
        _Vi_clear.on_click(self._clearFig)
        ViApp_button = wdg.HBox(children=[_Vi_apply, _Vi_clear])
        self._wVi_txt = wdg.Latex(value='', color='#A1B56C', margin=5, font_weight='bold', visible=False)
        _Vi_cat_w = wdg.VBox(children=[self._wVi_path, self._wVi_file, _ViQuality, self._wVi_txt, ViApp_button])

        # -> CAT :
        _subAccVi = wdg.Accordion(font_weight='bold')
        _subAccVi.children = [ViS_box, _Vi_cat_w]
        [_subAccVi.set_title(k, n) for k, n in enumerate(['Settings', 'Save/Load'])]

        # /////////////// FINAL TAB \\\\\\\\\\\\\\\\\
        javaWin = {'win': 't', 'clo': 'c', 'red': 'r', 'enl': 'e', 'tab': 'a', 'fit': 'f'}
        _createWindow.__init__(
            self, children=[_tab, _subAccSt, _subAccVi], **javaWin,
            title=['Workspace', 'Settings', 'Visualization'], xscroll=True,
            yscroll=True, win_kwargs={'background_color': '#FFF'})
        self._popout = self._tab
        self._fill()

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
        self._popout.selected_index = 0

    def _htmlTable(self, vName, vType, v, vSize):
        """Creation of the html table for the workspace"""
        cellLayout = """
        <div style='font-weight:bold; text-align:center'>{0}</div></td>""" + \
            """<td><div style='text-align:center'>{1}</div></td>""" + \
            """<td><div style='text-align:center'>{2}</div></td><td>""" + \
            """<div style='max-height:80px; text-overflow:ellipsis; table-layout:fixed; overflow:auto'>{3}</div>""" + \
            """</td>
        """

        self._tablab.value = """
        <table class="table table-bordered table-striped'">
            <tr>
                <th><div style='text-align:center'>Name</div></th>
                <th><div style='text-align:center'>Type</div></th>
                <th><div style='min-width:40px; text-align:center'>Size</div></th>
                <th>Value</th>
            </tr>
            <tr>
                <td>""" + \
                '</td></tr><tr><td>'.join([cellLayout.format(vName[k], vType[k], vSize[k], str(val)) for k, val in enumerate(v)]) + \
                """</td>
            </tr>
        </table>"""

    # /////////////// SETTINGS \\\\\\\\\\\\\\\\\
    # -> Sorting :
    def _FiltVar(self):
        """Filt, sort variables"""
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
                vName, _, _ = self._FiltVar()
            else:          # Save defined variables
                vName = var.replace(' ', '').split(sep=',')
            data = {name: self._namespace.shell.user_ns[name] for name in vName}
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
            # Confirmation text :
            self._wLS_txt.value = savefile+' loaded :D'
            self._wLS_txt.visible = True
            sleep(2)
            self._fill()
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
        var = wdg.Box()
        var.background_color = '#fff'
        var.border_color = '#ccc'
        var.border_width = 1
        var.border_radius = 5
        # var.overflow = 'hidden'
        # var.height = 700
        label = wdg.HTML(value='Not hooked')
        var.children = [label]
        return var, label
