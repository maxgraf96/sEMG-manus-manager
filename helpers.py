import os
from threading import Timer

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


def get_total_number_of_datapoints():
    # Get the total number of datapoints
    total_datapoints = 0
    for user_folder in os.listdir('user_data'):
        user_folder_path = os.path.join('user_data', user_folder)
        for session_folder in os.listdir(user_folder_path):
            session_folder_path = os.path.join(user_folder_path, session_folder)
            if not os.path.isdir(session_folder_path):
                continue
            for gesture_folder in os.listdir(session_folder_path):
                gesture_folder_path = os.path.join(session_folder_path, gesture_folder)
                if not os.path.isdir(gesture_folder_path):
                    continue
                for file in os.listdir(gesture_folder_path):
                    if file.endswith('.csv'):
                        file_path = os.path.join(gesture_folder_path, file)
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                            total_datapoints += len(lines)
    return total_datapoints


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
