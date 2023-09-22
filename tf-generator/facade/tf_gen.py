# Facade to hold all the functions to generate terraform files
_steps_registry = ["_generate_tf_header"]


def generate_tf_from_yaml(config: dict) -> str:
    """
    Main Generation Method Called from entrypoint with the configuration as a dictionary.
    :param config: Dictionary of the configuration file
    :return: String containing the output configuration data
    """
    output_buffer = ""
    for step in _steps_registry:
        output_buffer += eval(f"{step}(config)")  # Execute each step in the registry passing the dictionary to each
    return output_buffer


def _generate_tf_header(config: dict) -> str:
    # TODO: Complete Method
    return ""
