excluded_elements = ["delete_session_button", "theme_toggle_button"]


# Function to recursively iterate through all children of a widget
def configure_recursively(widget, config):
    bg_only_conf = {
        "bg": config["bg"]
    }

    try:
        if str(widget).split(".")[-1] in excluded_elements:
            pass
        else:
            widget.configure(config)
    except Exception as e:
        # Some items cannot have their foreground colour changed
        if "-fg" in e.__str__():
            widget.configure(bg_only_conf)
        else:
            pass
    for child in widget.winfo_children():
        try:
            if str(child.widget).split(".")[-1] in excluded_elements:
                continue
            child.configure(config)
        except Exception as e:
            # Some items cannot have their foreground colour changed
            if "-fg" in e.__str__():
                widget.configure(bg_only_conf)
            else:
                pass
        # Recursively apply the configuration to children's children
        configure_recursively(child, config)