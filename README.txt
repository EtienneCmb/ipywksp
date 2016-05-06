# ipywksp

Version : v0.0.3

## Description
Add a workspace to the IPython notebook. Implemented features :
- See all the defined variables
- Sort by types/size/name
- Display variables according to their types 
- Save/load in a pickle file
- Change values of variables
- Javascript integration to have a detached workspace
- Plot variables and save the figure

## Example of use:
>>> from ipywksp import workspace
>>> workspace(theme="dark", autoHide=True)

## Screenshots
Default theme :
![alt tag](https://github.com/EtienneCmb/ipywksp/blob/develop/screenshots/theme_light.png)

For those who have a dark theme :
![alt tag](https://github.com/EtienneCmb/ipywksp/blob/develop/screenshots/theme_dark.png)

## Future
- Save only visible variables in the workspace (avoid saving modules)
- Choose colums to display
- Enlarge variables (everything in a pandas dataframe?)
- Better integration of html/javascript (sort interactiv table)
- Check python 2.x/3.x compatibility

## Ideas
- Monitor system (slide for cpu and ram)
- Folder Tree for file organization + drag'd drop
- Pimp workspace : define themes, transparency... save and load preferences

## Contributors
Etienne Combrisson, Annalisa Pascarella, Philippe Castonguay, Thomas Thiery

This project is based on a ipython widgets exmple :
https://github.com/ipython/ipywidgets/blob/02e999adbc50f67cd05537bc19650d3b249684a6/examples/Variable%20Inspector.ipynb
