from maya import cmds

def unlock_shelf_buttons(shelf_name):
    """
    Unlock all buttons in the specified shelf.
    
    :param str shelf_name: The name of the shelf to unlock buttons from.
    """
    shelf_buttons = cmds.shelfLayout(shelf_name, query=True, childArray=True)
    
    if shelf_buttons:
        for button in shelf_buttons:
            print(button)
            try:
                cmds.shelfButton(button, edit=True, enable=True)
            except:
                pass
# Example usage
unlock_shelf_buttons('LeviCustomBeta')  # Replace 'Shelf1' with the name of your shelf
