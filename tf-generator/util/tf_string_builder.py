# Builds strings for module, resource, variable, and data blocks
from constants.configs import MAX_RECURSIONS, LINE_ENDINGS


class TFStringBuilder:
    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def generate_module(local_name: str, source: str, version: str, args: dict) -> str:
        """
        Generate the TF Config string for a module based on its type and arguments
        :param local_name: Module local name
        :param source: Source of Module
        :param version: Version of Module
        :param args: Dictionary of arguments
        :return: TF Config string representation
        """
        output = f"module \"{local_name}" + "\" {" + LINE_ENDINGS
        vars_ = {
            "source": source,
            "version": version,
            **args
        }
        output += TFStringBuilder._dict_to_string(vars_, 1)
        output += "}" + LINE_ENDINGS
        return output

    @staticmethod
    def generate_provider(local_name: str, args: dict) -> str:
        """
        Generate the TF Config string for a provider based on its arguments
        :param local_name: Module local name
        :param args: Dictionary of arguments
        :return: TF Config string representation
        """
        output = f"provider \"{local_name}" + "\" {" + LINE_ENDINGS
        vars_ = {
            **args
        }
        output += TFStringBuilder._dict_to_string(vars_, 1)
        output += "}" + LINE_ENDINGS
        return output

    @staticmethod
    def generate_resource(type_: str, local_name: str, args: dict) -> str:
        """
        Generate the TF Config string for a resource based on its type and arguments
        :param type_: Module type
        :param local_name: Resource local name
        :param args: Dictionary of arguments
        :return: TF Config string representation
        """
        output = f"resource \"{type_}\" \"{local_name}\"" + " {" + LINE_ENDINGS
        vars_ = {
            **args
        }
        output += TFStringBuilder._dict_to_string(vars_, 1)
        output += "}" + LINE_ENDINGS
        return output

    @staticmethod
    def generate_data(source: str, local_name: str, args: dict) -> str:
        """
        Generate the TF Config string for a data source based on its type and arguments
        :param source: Data Source
        :param local_name: Resource local name
        :param args: Dictionary of arguments
        :return: TF Config string representation
        """
        output = f"data \"{source}\" \"{local_name}\"" + " {" + LINE_ENDINGS
        vars_ = {
            **args
        }
        output += TFStringBuilder._dict_to_string(vars_, 1)
        output += "}" + LINE_ENDINGS
        return output

    @staticmethod
    def generate_tf_header(args: dict) -> str:
        """
        Generate the TF Config string for a Terraform header based on its arguments
        :param args: Dictionary of arguments
        :return: TF Config string representation
        """
        output = "terraform {" + LINE_ENDINGS
        vars_ = {
            **args
        }
        output += TFStringBuilder._dict_to_string(vars_, 1)
        output += "}" + LINE_ENDINGS
        return output

    @staticmethod
    def _dict_to_string(dict_: dict, tab_level=1, recursion_count=1) -> str:
        """
        ->Internal method<-
        Convert a dictionary recursively into a TF config string. (MAX RECURSIONS SET TO 5)
        :param dict_: input dictionary
        :param tab_level: number of levels deep to place the items
        :param recursion_count: counter used to prevent infinite loops
        :return: a string representation of the dictionary
        """
        if recursion_count > MAX_RECURSIONS:
            raise Exception("Recursion Count Maximum Reached!")
        max_key_len = 0
        output = ""
        for key in dict_:
            max_key_len = max(max_key_len, len(key))

        for key in dict_:
            value = dict_[key]
            output += f"{'  ' * tab_level}{key}{' ' * (max_key_len - len(key))} "
            if isinstance(value, tuple):
                if value[1] == "ref":
                    output += f"= {value[0]}{LINE_ENDINGS}"
                continue
            if isinstance(value, str):
                output += f"= \"{value}\"{LINE_ENDINGS}"
                continue
            if isinstance(value, dict):
                output += "= {" + LINE_ENDINGS
                output += TFStringBuilder._dict_to_string(value, tab_level + 1, recursion_count + 1)
                output += f"{'  ' * tab_level}" + "}" + LINE_ENDINGS
                continue
            if isinstance(value, list):
                output += "= [" + LINE_ENDINGS
                output += TFStringBuilder._list_to_string(value, tab_level + 1, recursion_count + 1)
                output += f"{'  ' * tab_level}]" + LINE_ENDINGS
                continue
            if isinstance(value, int) or isinstance(value, float) or value.isnumeric():
                output += f"= {value}{LINE_ENDINGS}"
                continue
        return output

    @staticmethod
    def _list_to_string(list_: list, tab_level=1, recursion_count=1) -> str:
        """
        ->Internal method<-
        Convert List to a TF Config String
        :param list_: input list for conversion
        :param tab_level: number of levels deep to place the items
        :param recursion_count: counter used to prevent infinite loops
        :return: a string representation of the list
        """
        if recursion_count > MAX_RECURSIONS:
            raise Exception("Recursion Count Maximum Reached!")
        output = ""
        for value in list_:
            if isinstance(value, tuple):
                if value[1] == "ref":
                    output += f"{'  ' * tab_level}{value},{LINE_ENDINGS}"
                continue
            if isinstance(value, str):
                output += f"{'  ' * tab_level}\"{value}\",{LINE_ENDINGS}"
                continue
            if isinstance(value, dict):
                output += f"{'  ' * tab_level}" + "{" + LINE_ENDINGS
                output += (TFStringBuilder._dict_to_string(value, tab_level + 1, recursion_count + 1))
                output += f"{'  ' * tab_level}" + "}," + LINE_ENDINGS
                continue
            if isinstance(value, list):
                output += f"{'  ' * tab_level}[" + LINE_ENDINGS
                output += (TFStringBuilder._list_to_string(value, tab_level + 1, recursion_count + 1))
                output += f"{'  ' * tab_level}]," + LINE_ENDINGS
                continue
            if isinstance(value, int) or isinstance(value, float) or value.isnumeric():
                output += f"{'  ' * tab_level}{value},{LINE_ENDINGS}"
                continue
        return output
