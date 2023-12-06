excluded_elements = ["delete_session_button"]


# Function to recursively iterate through all children of a widget
def configure_recursively(widget, config):
    try:
        if str(widget).split(".")[-1] in excluded_elements:
            pass
        else:
            widget.configure(config)
    except:
        pass
    for child in widget.winfo_children():
        try:
            if str(child.widget).split(".")[-1]:
                continue
            child.configure(config)
        except:
            pass
        # Recursively apply the configuration to children's children
        configure_recursively(child, config)